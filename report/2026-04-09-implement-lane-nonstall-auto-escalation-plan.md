# projectH implement lane non-stall auto-escalation 계획서

**작성일**: 2026-04-09<br>
**성격**: 구현 직전 운영 재설계 계획서<br>
**목적**: Claude가 `STATUS: implement` 상태에서 operator 선택 질문으로 멈추지 않고, Codex/Gemini/operator 순서로 자동 에스컬레이션되도록 single-Codex tmux 흐름을 재설계

---

## 1. 문제 정의

현재 규칙 문서와 watcher prompt는 아래 방향을 이미 말하고 있습니다.

- `Claude = implement`
- `Codex = verify + next slice narrowing`
- `Gemini = Codex가 못 좁힐 때만 arbitration`
- `operator = 마지막 stop`

하지만 실제 동작에서는 아래 실패 모드가 남아 있습니다.

1. Claude가 `implement` 중 handoff 실행 대신 operator에게 선택지를 직접 물을 수 있음
2. watcher가 그 멈춤을 Codex/Gemini arbitration으로 강제 전환하지 않음
3. 오래된 `.pipeline/operator_request.md` 같은 stale control file이 살아 있으면 사람과 lane이 같이 헷갈릴 수 있음

즉 현재 문제는 문구 부족이 아니라, **행동 제약이 기계적으로 강제되지 않는 것**입니다.

---

## 2. 목표

이번 재설계의 목표는 아래 한 줄입니다.

**Claude implement lane은 더 이상 operator 선택 UI를 직접 열지 않고, 막히면 watcher가 Codex/Gemini/operator 순서로 자동 전이시킨다.**

---

## 3. 이번 계획이 닫는 범위

### 포함

- Claude implement-state hard guard
- Claude blocked sentinel contract
- watcher의 자동 Codex triage 전이
- Codex -> Gemini -> operator escalation state machine
- stale control suppression
- launcher/UI에서 stale stop 신호를 active control처럼 보이지 않게 하는 기준

### 제외

- setup/agent profile/runtime profile 설계
- setup executor/launcher setup mode
- whole-project control slot 대개편
- 새로운 다중 operator UI

즉 이번 계획은 `.pipeline` / watcher / prompt contract의 **멈춤 방지 전이 설계**에만 집중합니다.

---

## 4. 하드 규칙

### 4.1 Claude implement lane의 허용 행동

`STATUS: implement`를 받은 Claude는 아래 둘 중 하나만 할 수 있습니다.

1. handoff에 적힌 bounded slice를 구현한다
2. machine-readable blocked sentinel을 남기고 중단한다

아래 행동은 금지합니다.

- operator에게 “다음 중 하나를 선택해 주세요”라고 직접 묻기
- 다음 slice를 스스로 다시 선정하기
- `operator_request.md`를 직접 쓰거나 갱신하기
- `gemini_request.md`를 직접 쓰거나 갱신하기

### 4.2 operator 호출 권한

operator stop는 Codex만 최종적으로 열 수 있습니다.

즉:

- Claude는 operator stop를 열 수 없음
- Gemini는 advisory만 가능
- Codex만 `.pipeline/operator_request.md`를 최신 stop control로 승격 가능

### 4.3 stale control 가시성

최신 valid control이 아니면 launcher/UI/watcher는 그것을 active stop/go 신호처럼 취급하면 안 됩니다.

최소 원칙:

- 최신 `STATUS: implement` handoff가 있으면 오래된 `operator_request.md`는 stop 근거가 아님
- 오래된 `operator_request.md`, `gemini_request.md`, `gemini_advice.md`는 archive 또는 inactive 표시 대상
- watcher dispatch 판단은 “존재”가 아니라 “최신 valid control” 기준으로만 수행

---

## 5. 제안 상태기계

### 5.1 핵심 상태

- `IMPLEMENT_READY`
  최신 `.pipeline/claude_handoff.md`가 `STATUS: implement`
- `IMPLEMENT_BLOCKED`
  Claude가 machine-readable blocked sentinel을 남김
- `CODEX_TRIAGE_PENDING`
  watcher가 Codex에 triage를 보낼 차례
- `GEMINI_ARBITRATION_PENDING`
  Codex가 exact slice를 못 좁혀 Gemini를 요청함
- `OPERATOR_STOP`
  Codex가 최종적으로 `needs_operator`를 최신 control로 엶

### 5.2 전이 규칙

1. `IMPLEMENT_READY -> IMPLEMENT_BLOCKED`
   Claude가 handoff 실행 불가 사유를 sentinel로 남길 때
2. `IMPLEMENT_BLOCKED -> CODEX_TRIAGE_PENDING`
   watcher가 sentinel을 감지하고 Codex triage prompt를 dispatch
3. `CODEX_TRIAGE_PENDING -> IMPLEMENT_READY`
   Codex가 새 `STATUS: implement` handoff를 쓰면 Claude 재개
4. `CODEX_TRIAGE_PENDING -> GEMINI_ARBITRATION_PENDING`
   Codex가 `.pipeline/gemini_request.md`를 최신 valid control로 열면 Gemini로 전이
5. `GEMINI_ARBITRATION_PENDING -> CODEX_TRIAGE_PENDING`
   Gemini가 advice를 남기면 Codex follow-up
6. `CODEX_TRIAGE_PENDING -> OPERATOR_STOP`
   Gemini까지 봐도 못 좁혔을 때만 Codex가 `.pipeline/operator_request.md`를 최신 stop control로 씀

핵심은:

**Claude blocked -> Codex**가 자동으로 이어져야 하며,
Claude blocked -> operator 선택 대기
로 가면 실패입니다.

---

## 6. 새 계약

### 6.1 Claude blocked sentinel

Claude가 막혔을 때는 자연어 장문 질문 대신, watcher가 잡을 수 있는 좁은 신호를 남겨야 합니다.

권장 최소 형식:

```text
STATUS: implement_blocked
BLOCK_REASON: handoff_not_actionable
REQUEST: codex_triage
HANDOFF: .pipeline/claude_handoff.md
```

권장 성질:

- 짧고 반복 가능한 고정 형식
- watcher regex로 안정적으로 감지 가능
- operator에게 직접 선택을 요구하는 문구를 포함하지 않음

### 6.2 Codex triage prompt

Codex triage prompt는 아래를 강제해야 합니다.

- latest `.pipeline/claude_handoff.md` 확인
- Claude blocked reason 확인
- latest `/work` / same-day latest `/verify` 확인
- 결과를 아래 셋 중 하나로만 닫기
  - 새 `STATUS: implement`
  - `STATUS: request_open`
  - `STATUS: needs_operator`

즉 Codex는 blocked 상황에서 “무엇이든 설명”이 아니라 **다음 control file**을 반드시 남겨야 합니다.

### 6.3 Gemini advice contract

Gemini는 blocked 상황에서도 아래만 수행합니다.

- advisory log 작성
- `.pipeline/gemini_advice.md` 작성

Gemini는:

- handoff 확정 금지
- operator stop 확정 금지

---

## 7. watcher 재설계

### 7.1 Claude blocked 감지

watcher는 Claude pane 최근 출력에서 blocked sentinel을 감지해야 합니다.

최소 조건:

- 최신 dispatch가 Claude implement lane이었음
- pane 최근 출력에 `STATUS: implement_blocked`가 안정적으로 보임
- 이미 같은 fingerprint로 triage를 보낸 적이 없음을 dedupe로 확인

### 7.2 자동 Codex triage

blocked sentinel이 감지되면 watcher는 operator 대기를 열지 않고 바로 Codex triage를 dispatch합니다.

dispatch 입력:

- latest `.pipeline/claude_handoff.md`
- Claude blocked snippet
- latest `/work`
- same-day latest `/verify`
- active control signatures

### 7.3 stale control suppression

watcher는 매 loop에서 control file을 읽기 전에 active control set을 계산해야 합니다.

최소 규칙:

- 가장 최신 valid `STATUS` control만 canonical
- 더 오래된 stop/go/advice/request 파일은 dispatch 판단에서 제외
- 제외된 파일은 inactive로만 보이거나 archive 대상이 됨

### 7.4 operator stop 조건

watcher는 operator를 직접 열지 않습니다.

operator stop는 오직:

- Codex가 최신 `.pipeline/operator_request.md`에 `STATUS: needs_operator`
  를 썼을 때만 active stop가 됩니다.

---

## 8. launcher / UI 재설계

launcher나 GUI는 stale stop를 active warning처럼 보이면 안 됩니다.

최소 표시 규칙:

- `Active control`
  최신 valid control 1개만 강조
- `Inactive stale controls`
  별도 collapse 영역 또는 작은 badge로만 표시

즉 사용자가 오래된 `operator_request.md`를 보고 “지금도 stop인가?”를 헷갈리지 않게 해야 합니다.

---

## 9. 구현 순서

권장 순서는 아래입니다.

1. Claude prompt에 implement hard guard 추가
2. Claude blocked sentinel 형식 고정
3. watcher에 blocked detection 추가
4. watcher에 Codex triage dispatch 추가
5. control file active/stale 판정 로직 추가
6. launcher/UI에 active control vs stale control 표시 분리
7. archive helper 또는 auto-suppress 정리 규칙 연결

이 순서를 권장하는 이유:

- prompt guard만 바꾸면 여전히 멈출 수 있음
- watcher 자동 전이만 넣으면 stale control 때문에 다시 stop처럼 보일 수 있음
- 따라서 prompt, watcher, control visibility를 한 묶음으로 닫아야 함

---

## 10. 테스트 계획

### 10.1 Claude blocked 시나리오

- Claude가 `implement_blocked` sentinel을 남김
- watcher가 Codex triage를 dispatch
- operator 선택 대기 없이 다음 lane으로 넘어감

### 10.2 Codex triage 성공 시나리오

- Codex가 새 `STATUS: implement` handoff 작성
- watcher가 Claude를 다시 호출

### 10.3 Gemini arbitration 시나리오

- Codex가 `request_open`
- Gemini가 `advice_ready`
- Codex가 최종 handoff 또는 operator stop 작성

### 10.4 stale operator suppression 시나리오

- 오래된 `operator_request.md`가 남아 있음
- 더 최신 `claude_handoff.md`가 있음
- watcher/launcher가 operator stop로 오인하지 않음

### 10.5 forbidden behavior 시나리오

- Claude pane 출력에 “다음 중 하나를 선택” 같은 operator menu text가 생겨도
- watcher가 그것을 valid stop/go control로 취급하지 않음
- 가능한 경우 blocked sentinel 유도 prompt로 복구

---

## 11. 비목표

이번 재설계는 아래를 하지 않습니다.

- setup system 개편
- role binding runtime 적용
- generic multi-agent orchestration platform화
- operator UI 확장
- whole-project audit loop 재설계

즉 목표는 좁습니다.

**Claude implement lane이 멈추지 않게 만들고, 막히면 Codex/Gemini/operator 순서로만 흐르도록 강제하는 것**입니다.

---

## 12. 추천 다음 슬라이스

가장 먼저 구현할 한 슬라이스는 아래가 적절합니다.

**Claude implement hard guard + blocked sentinel + watcher auto-route to Codex triage**

이 슬라이스가 먼저 필요한 이유:

- 현재 실제 사용자 불편은 “멈춤” 자체
- stale control suppression은 그 다음에 붙여도 되지만, auto-route가 없으면 같은 문제가 반복됨
- operator menu 질문을 행동 차원에서 막으려면 prompt와 watcher 전이가 먼저 붙어야 함

그 다음 슬라이스는 아래가 자연스럽습니다.

**active control vs stale control suppression in watcher and launcher**
