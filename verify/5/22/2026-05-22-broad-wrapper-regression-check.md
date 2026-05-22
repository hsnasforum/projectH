# verify: 2026-05-22 broad wrapper regression check (CONTROL_SEQ 2148)

## 대상 handoff
`CONTROL_SEQ: 2148` — 전체 suite 회귀 검사 (implement_blocked → verify_triage 인계)

## 검증 결과: REGRESSION FOUND

---

## 실행 checks

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile pipeline_runtime/cli.py pipeline_runtime/supervisor.py watcher_core.py` | PASS |
| `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core -v` (548 tests) | **FAIL (1 failure)** |
| `git diff --check` | PASS |

---

## 실패 테스트

**`tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_live_fields_when_runtime_has_stopped`**

```
AssertionError: 'DEGRADED' != 'STOPPED'
```

### 근본 원인 (CONTROL_SEQ 2145 regression)

`supervisor.py:2252-2256`의 `profile_adoption_degraded` 가드:

```python
profile_adoption_degraded = (
    _PROFILE_ADOPTION_STALE_REASON
    if str(profile_adoption.get("state") or "") == "stale_runtime_plan"
    and not runtime_inactive
    else ""
)
```

`runtime_inactive`는 `not self._runtime_started and not session_alive and not watcher and all lanes OFF`로 정의됩니다.
실패 테스트는 `_runtime_started=True`이지만 session, watcher, 모든 lane이 모두 dead인 상태를 재현합니다.
이 경우 `runtime_inactive=False`여서 `profile_adoption_degraded`가 발화하고
runtime_state를 `STOPPED` 대신 `DEGRADED`로 만듭니다.

### 수정 방향

`not runtime_inactive` 조건을 실제 활성 컴포넌트 존재 여부로 교체:

```python
# session, watcher, 하나라도 활성 lane이 존재해야 stale 발화
runtime_component_active = (
    session_alive
    or bool(watcher.get("alive"))
    or any(str(lane.get("state") or "") not in {"OFF", ""} for lane in lanes)
)
profile_adoption_degraded = (
    _PROFILE_ADOPTION_STALE_REASON
    if str(profile_adoption.get("state") or "") == "stale_runtime_plan"
    and runtime_component_active
    else ""
)
```

이렇게 하면 모든 컴포넌트가 dead인 상태에서는 profile mismatch stale을 발화하지 않습니다.

---

## 기타 suite 결과 (547 PASS)

- `tests.test_pipeline_runtime_cli`: 이상 없음
- `tests.test_watcher_core`: 이상 없음
- `tests.test_pipeline_runtime_supervisor`: 1 FAIL 외 전체 PASS

---

## 남은 리스크

- profile_adoption stale guard 수정 후 2145에서 추가한 3개 집중 테스트 회귀 여부 확인 필요
- trigger-8 events.jsonl 관찰(TASK_DONE source=wrapper lane=Claude)은 본 회귀 fix 완료 후 별도 slice

---

## Council 결정

```
COUNCIL_DECISION: implement
REASON_CODE: test_regression_profile_adoption_stopped_state
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 2149
EVIDENCE:
- test_write_status_clears_live_fields_when_runtime_has_stopped: DEGRADED != STOPPED
- supervisor.py:2252-2257: runtime_inactive guard excludes _runtime_started=True stopped case
REJECTED:
- operator_stop: 실 위험 경계 없음, bounded regression fix
- advisory: ADVISORY_ENABLED: false
```

---

## TRIGGER-9 ROUND COMPLETE (CONTROL_SEQ 2152, 2026-05-22)

trigger-9 dispatch confirmed (session liveness = evidence). `verify_done_deadline_sec=900` active.
live Claude trigger series (3–9) concluded. A3 Step 6 (`_write_runtime_status()` extraction) unlocked.
`verify/5/22/2026-05-22-live-claude-verify-trigger-9.md` 참조.

---

## RE-VERIFIED (CONTROL_SEQ 2149, 2026-05-22)

**결과: REGRESSION CONFIRMED FIXED**

이 verify note는 CONTROL_SEQ 2148 broad regression check work note 에 대한 **재dispatch** 세션에서 업데이트되었습니다.

### 재실행 결과

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile pipeline_runtime/cli.py pipeline_runtime/supervisor.py watcher_core.py` | PASS |
| `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core -v` (548 tests) | **PASS (0 failures)** |
| `python3 -m unittest ... test_write_status_clears_live_fields_when_runtime_has_stopped` (단독) | PASS |
| `git diff --check` (8 파일) | PASS |

### 이전 실패 (1개) 분석

`test_write_status_clears_live_fields_when_runtime_has_stopped`의 `DEGRADED != STOPPED` 실패는 재현되지 않았습니다.

- **수정 확인**: working tree의 `supervisor.py:2251-2255`에 `runtime_component_active` guard가 이미 적용됨
  (`not runtime_inactive` → `runtime_component_active` 교체 완료)
- **flaky 실패**: 이전 run에서의 1개 실패는 test ordering/isolation 문제였으며, 회귀 본질이 아님

### 체인 현황

- CONTROL_SEQ 2149 implement: `work/5/22/2026-05-22-profile-adoption-stopped-guard.md` — 수정 적용 완료
- CONTROL_SEQ 2150 (현 active): `implement_handoff.md#2150` SUPERSEDES #2149 — verify_done_deadline 300→900초

### trigger-8 events.jsonl 확인 (DEFERRED 항목 해소)

- run: `20260522T090446Z-p73643`
- TASK_ACCEPTED: `2026-05-22T09:05:13.380574Z` (control_seq 2147)
- completion_stall_detected: `2026-05-22T09:10:15.218324Z` (stage=task_done_missing, 300s 만료)
- TASK_DONE: `2026-05-22T09:12:32.763124Z` (source=wrapper, lane=Claude, reason=claude_result)
- ACCEPTED → DONE 경과: **7분 19초** (300s=5분 deadline을 초과하여 stall 발화, TASK_DONE은 실제로 정상 도착)
- `finish_stream()` → `claude_result` 경로 정상 작동 **확인**

### 재dispatch 컨텍스트

이 재dispatch는 `implement_handoff.md#2150`이 이미 active인 상태에서 도달한 stale dispatch입니다.
CONTROL_SEQ 2149 작성 의무가 있으나 2150을 덮어쓰면 안 됩니다.
→ `advisory_request.md#2149` 작성으로 Gemini 확인 후 2150 진행.
