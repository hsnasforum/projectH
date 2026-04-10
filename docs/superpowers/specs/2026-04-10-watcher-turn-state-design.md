# Watcher Turn State 단일 상태 축 설계

**날짜**: 2026-04-10
**범위**: watcher_core.py dispatch 상태 일원화, 턴 순서 버그 수정, stale control 혼선 해결, Claude idle 대응
**구현 대상**: 섹션 1~4. 섹션 5(양방향 ack)는 미구현 확장 스케치.

---

## 배경

### 최근 실사고

1. **턴 순서 버그**: work closeout이 이미 커밋된 상태에서 watcher가 Codex 대신 Claude를 먼저 디스패치
2. **stale control 혼선**: 오래된 control slot이 active로 해석되어 잘못된 에이전트가 실행됨
3. **CONTROL_SEQ ↔ UI 불일치**: backend.py가 control slot을 독자적으로 재해석해 watcher와 다른 결론
4. **VERIFY_RUNNING ↔ handoff 혼선**: Codex verify 중인데 UI에서는 Claude handoff가 활성으로 표시
5. **Claude idle 고착**: `_waiting_for_claude = True`인 상태에서 Claude가 작업을 안 하면 watcher 무한 대기

### 근본 원인

watcher_core.py 내부에서 턴 정보가 분산:
- `_waiting_for_claude` (bool)
- `_pending_claude_handoff_sig` (str)
- `lease.is_active("slot_verify")` (PaneLease)
- `_get_active_control_signal()` (ControlSignal)
- `JobState.status` (JobStatus enum)

backend.py는 이것들을 모르고 control slot + job state JSON을 따로 재해석 → 불일치 발생.

---

## 섹션 1: WatcherTurnState — 단일 상태 축

### 설계

```python
class WatcherTurnState(str, Enum):
    IDLE             = "IDLE"
    CLAUDE_ACTIVE    = "CLAUDE_ACTIVE"
    CODEX_VERIFY     = "CODEX_VERIFY"
    CODEX_FOLLOWUP   = "CODEX_FOLLOWUP"
    GEMINI_ADVISORY  = "GEMINI_ADVISORY"
    OPERATOR_WAIT    = "OPERATOR_WAIT"
```

CLAUDE_STALLED는 첫 버전에서 넣지 않음. pane fingerprint / progress marker 규칙이 안정화된 뒤 2차로 도입.

### turn_state.json

watcher가 `.pipeline/state/turn_state.json`에 매 전이마다 기록:

```json
{
  "state": "CODEX_VERIFY",
  "entered_at": 1744300000.0,
  "reason": "work_needs_verify",
  "active_control_file": "claude_handoff.md",
  "active_control_seq": 17,
  "verify_job_id": "work-4-10-..."
}
```

### 핵심 규칙

- **turn_state.json은 watcher 내부 canonical의 UI 투영이다.** job state를 대체하지 않는다.
- job state(`.pipeline/state/*.json`의 VERIFY_PENDING / VERIFY_RUNNING / ...)는 그대로 canonical.
- turn_state.json은 현재 active turn의 요약 projection.
- **모든 턴 전환은 `_transition_turn(new_state, reason)` 한 메서드를 통해서만 일어난다.**
- `_waiting_for_claude`, `_pending_claude_handoff_sig` 같은 분산 플래그는 제거되고 이 상태로 통합.
- `stall_timeout_sec`는 watcher config 내부 값. turn_state.json에는 넣지 않음.

### `_transition_turn()` 역할

- 독자적으로 승자를 정하지 않는다.
- 이미 resolve된 active control과 verify state를 받아 기록만 한다.
- atomic write (temp file + rename)로 turn_state.json을 갱신.

### backend.py 변경

- turn_state.json이 있으면 **그것만** 사용해서 UI 표시.
- turn_state.json이 없으면 기존 control slot + job state 해석으로 fallback (마이그레이션 호환).
- turn_state.json과 기존 slot 해석을 **혼합하지 않는다** — split-brain 방지.

---

## 섹션 2: 턴 순서 버그 수정

### 현재 문제

`_determine_initial_turn()` (라인 2168)에서 `_latest_work_needs_verify()`가 `False`를 반환하면 Claude로 빠짐. work closeout이 metadata-only로 판정되면 "verify할 work가 없다" → Claude 차례로 오판.

### 설계

**`_determine_initial_turn()`을 `_transition_turn()`으로 흡수.** initial turn도 같은 전이 경로를 탐.

판정 로직:

```
1. operator_request가 active control
   → OPERATOR_WAIT

2. gemini_request가 active control
   → GEMINI_ADVISORY

3. gemini_advice가 active control
   → CODEX_FOLLOWUP

4. claude_handoff가 active control이고 STATUS=implement이지만
   verify_pending 또는 verify_active가 있으면
   → CODEX_VERIFY
   (Codex가 먼저 따라붙어야 함)

5. _latest_work_needs_verify()
   → CODEX_VERIFY

6. claude_handoff가 active control이고 dispatchable
   → CLAUDE_ACTIVE

7. 그 외
   → IDLE
```

4번 규칙이 핵심 추가: handoff가 active라도 **verify_pending이나 verify_active이면 Claude보다 Codex 우선**. `dispatchable == False` 같은 간접 조건이 아니라 `verify_pending` / `verify_active`를 명시적 입력으로 사용.

마지막 fallback은 `IDLE`. `CODEX_VERIFY` fallback은 과검증 루프 위험.

### verify 필요 판정 완화

- **현재**: `_latest_work_needs_verify()` → `_get_latest_work_path()` → `_find_latest_md()` → `_is_dispatchable_work_note()` → `_is_metadata_only_work_note()` = True이면 dispatchable에서 제외 → verify 대상에서도 빠짐.
- **변경**: `_latest_work_needs_verify()`가 호출하는 경로에서 verify 필요 여부를 판정할 때는 `_is_canonical_round_note()` 기준으로 모든 canonical round note를 대상으로 함. `_is_metadata_only_work_note()` 필터는 Codex verify 디스패치 프롬프트 내용 구성에만 영향.
- **구체적으로**: `_get_latest_work_path()`에 `for_verify_check=True` 파라미터를 추가하거나, `_latest_work_needs_verify()` 전용 경로를 분리하여 metadata-only 필터를 우회.

---

## 섹션 3: Stale Control 혼선 및 상태 불일치 해결

### 현재 문제들

1. **stale control 혼선**: sig 변경 감지 → active control 체크하는 경로와 안 하는 경로가 혼재
2. **CONTROL_SEQ ↔ UI 불일치**: backend.py가 watcher와 동일한 정렬 로직을 독자적으로 구현
3. **VERIFY_RUNNING ↔ handoff 혼선**: backend.py가 verify activity와 control slot을 따로 읽어 합침

### 설계

**turn_state.json이 세 문제를 한꺼번에 해결.**

watcher_core.py:
- `_check_pipeline_signal_updates()`에서 sig 변경 감지 → active control 체크 → `_transition_turn()` 호출.
- stale sig는 로그만 남기고 전이를 일으키지 않음.
- `_transition_turn()`에서 전이 시 이전 `active_control_seq`보다 낮은 seq의 signal은 무시.
- 같은 seq는 무조건 허용이 아님 — **같은 file + 새 sig이거나, canonical resolver가 winner로 판단한 경우만 허용**.

backend.py:
- `read_turn_state(project)` 함수 추가: `.pipeline/state/turn_state.json` 읽기.
- `format_control_summary()`가 turn_state.json이 있으면 그것만으로 표시.
- 없으면 기존 control slot + verify activity 해석 fallback.
- **turn_state.json과 기존 해석을 혼합하지 않음.**

---

## 섹션 4: Claude Idle 고착 대응 (Liveness)

### 현재 문제

`CLAUDE_ACTIVE` 상태에서 Claude가 실제로 작업을 안 하면 watcher가 무한 대기. work/ 스냅샷 diff로만 판단하므로 pane이 죽으면 영원히 대기.

### 설계

첫 버전: CLAUDE_STALLED enum 없이 **CLAUDE_ACTIVE → IDLE 복구 경로만**.

#### watcher 내부 필드 (turn_state.json에 안 들어감)

```python
claude_active_idle_timeout_sec: float = 300  # config 값

# 런타임 추적
_last_progress_at: float = 0.0
_last_active_pane_fingerprint: str = ""
_last_idle_release_handoff_sig: str = ""
_last_idle_release_at: float = 0.0
```

#### timeout 기준: last_progress_at

`entered_at`이 아니라 `last_progress_at` 기준. 다음 중 하나라도 있으면 갱신:
- pane fingerprint가 바뀜
- /work 또는 tree snapshot 변화
- 새 실행 출력 감지

#### idle timeout 판정 조건 (조합)

`pane_text_is_idle()` 단독이 아니라:
- pane fingerprint가 오래 안 바뀜 **AND**
- /work 미변경 **AND**
- tree snapshot 미변경 **AND**
- idle 패턴이 안정적으로 유지

이 조합일 때만 `claude_idle_timeout`으로 IDLE 전이.

#### IDLE 전이 후 재디스패치 루프 방지

같은 handoff sig는 cooldown 동안 Claude에 재디스패치하지 않음:
- `_last_idle_release_handoff_sig`: IDLE 전이 시 당시 handoff sig 기록
- `_last_idle_release_at`: IDLE 전이 시각 기록
- 다음 poll에서 같은 handoff sig면 cooldown(예: 300초) 동안 Claude로 보내지 않음
- cooldown 동안 Codex verify가 필요하면 Codex가 대신 갈 수 있음

#### IDLE 전이 후 동작

- 다음 poll에서 일반 턴 판정 로직을 다시 탐.
- Claude에 프롬프트를 재전송하지 않음.
- 로그에만 `claude_idle_timeout` 이벤트 기록.

#### 2차 확장

pane fingerprint / progress marker 규칙이 안정화되면:
- `CLAUDE_STALLED` enum 추가
- UI에 "Claude 응답 없음" 표시
- 재전송 또는 Codex triage 경로 연결

---

## 섹션 5: 양방향 Ack — 미구현 확장 스케치

> **주의**: 이 섹션은 현재 구현 대상이 아니다. 향후 확장 아이디어로만 기록한다.
> agent가 반드시 ack 파일을 쓴다는 강한 계약이 아니며, canonical truth나 dispatch correctness의 근거로 사용되지 않는다.

### 기본 아이디어

watcher가 프롬프트를 전달한 뒤, 에이전트가 **선택적으로** `.pipeline/state/ack-<role>.json`을 써서 dispatch가 관찰되었음을 알릴 수 있다.

**v1 대상 role**: `implement`만. 이유:
- `verify` role은 기존 job state 갱신(VERIFY_PENDING → VERIFY_RUNNING)이 사실상 receipt 역할을 하므로 별도 ack 불필요.
- `advisory`, `followup` 등 다른 role은 future extension.

```json
{
  "role": "implement",
  "signal_type": "dispatch_observed",
  "handoff_sig": "abc123...",
  "control_seq": 17,
  "observed_at": 1744300005.0
}
```

### 성격

- **advisory signal이다.** canonical truth가 아니다.
- ack 있음 = 받았을 가능성 높음. ack 없음 = 실패 확정 아님.
- dispatch correctness와 active turn 판정은 watcher 내부 canonical state가 맡는다.
- 에이전트가 쓸 수 있다. 없어도 기존 liveness/fallback으로 동작한다.
- "모델이 프롬프트를 보고 파일을 꼭 쓴다"는 계약은 현실적으로 약하므로, 필수 계약으로 설계하지 않는다.

### 섹션 1~4와의 호환

- `_transition_turn()`은 ack와 무관하게 동작.
- ack는 `last_progress_at` 갱신의 추가 입력원이 될 수 있으나, 다음 조건을 모두 만족할 때만 갱신:
  - `ack.handoff_sig == current handoff sig`
  - `ack.control_seq == current active_control_seq`
  - 현재 turn state와 ack의 role이 일치
  - 이 3개를 만족하지 않는 stale ack나 이전 라운드 ack는 `last_progress_at`를 갱신하지 않는다.
- turn_state.json 구조에 ack 관련 필드를 넣지 않음.
- ack가 없어도 기존 pane fingerprint + work snapshot 경로가 fallback.

### 미결정 사항

- ack 파일의 구체적인 write 주체와 시점은 구현 시 결정.
- `prompt_received`보다 `dispatch_observed` 또는 `round_started`가 더 현실적인 의미.
- verify role은 job state가 receipt 역할을 하므로 별도 ack 불필요 (확정).
- advisory/followup role의 ack 필요성은 future extension에서 판단.

---

## 영향 받는 파일

| 파일 | 변경 유형 |
|------|----------|
| `watcher_core.py` | WatcherTurnState enum, `_transition_turn()`, 분산 플래그 제거, idle timeout, 턴 판정 로직 변경 |
| `pipeline_gui/backend.py` | `read_turn_state()` 추가, `format_control_summary()` turn_state.json 우선 경로, fallback 유지 |
| `pipeline_gui/app.py` | backend에서 받은 turn state 표시 (backend 변경에 따른 최소 수정) |
| `tests/test_watcher_core.py` | 새 enum/전이 로직 테스트, idle timeout 테스트, 재디스패치 루프 방지 테스트 |
| `tests/test_pipeline_gui_backend.py` | turn_state.json 읽기/fallback 테스트 |
| `.pipeline/README.md` | turn_state.json 규약 및 상태 전이 정책 문서화 |

## 구현하지 않는 것

- CLAUDE_STALLED enum (2차)
- 양방향 ack 구현 (향후 확장)
- partial write settle window for control slots (현재 실사고 아님)
- 이벤트 기반 아키텍처 전환 (시기상조)
- pane crash 자동 복구 (별도 과제)
