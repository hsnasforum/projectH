# 2026-04-23 Milestone 12 Axis 1 trace audit baseline

## 변경 파일
- `storage/session_store.py`
- `scripts/audit_traces.py`
- `tests/test_session_store.py`
- `work/4/23/2026-04-23-milestone12-axis1-trace-audit-baseline.md`

## 사용 skill
- `security-gate`: 로컬 session trace를 읽어 집계하는 변경이므로 읽기 전용 경계, 저장 위치, audit 출력 범위를 확인했습니다.
- `finalize-lite`: handoff가 요구한 세 검증 명령과 변경 파일 범위만 기준으로 완료 여부를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 명령, 남은 리스크를 한국어 closeout으로 남겼습니다.

## 변경 이유
- Milestone 12 Axis 1 handoff(`CONTROL_SEQ: 920`)에 따라 personalization 전제 조건 평가용 trace baseline 집계가 필요했습니다.
- session별 correction pair, feedback signal, operator action outcome 수를 로컬에서 읽기 전용으로 확인할 수 있어야 했습니다.

## 핵심 변경
- `SessionStore.get_global_audit_summary()`를 추가해 `data/sessions/*.json` 전체의 session 수, grounded-brief correction pair 수, feedback-like/dislike 수, operator executed/rolled_back/failed 수를 집계하도록 했습니다.
- 실제 저장 계약에 맞춰 message-level feedback도 집계하고, 현재 label인 `helpful`은 like, `unclear`/`incorrect`는 dislike로 매핑했습니다. legacy `like`/`dislike` label도 함께 허용했습니다.
- `scripts/audit_traces.py`를 추가해 JSON summary와 사람이 읽는 요약을 출력하도록 했고, `python3 scripts/audit_traces.py` 실행 시 repo root import가 되도록 경로를 보정했습니다.
- `tests/test_session_store.py`에 유효한 grounded-brief source message fixture를 사용한 `test_get_global_audit_summary`를 추가했습니다.

## 검증
- `python3 -m py_compile storage/session_store.py scripts/audit_traces.py tests/test_session_store.py`
  - 통과
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit -v 2>&1 | tail -14`
  - `Ran 37 tests in 0.034s`
  - `OK`
- `python3 scripts/audit_traces.py`
  - 통과
  - 출력 요약: `Sessions: 267`, `Correction pairs: 137`, `Feedback signals: 0`, `Operator actions: executed=0, rolled_back=0, failed=0`

## 남은 리스크
- 이번 slice는 trace baseline 집계와 CLI만 추가했습니다. personalization 판단, threshold, model layer 설계, 문서 업데이트는 handoff 범위가 아니어서 진행하지 않았습니다.
- CLI는 로컬 `data/sessions/`를 읽기만 하며, 손상된 session 파일은 기존 `get_session()` 복구/격리 동작을 따릅니다.
- feedback count는 현재 message-level feedback 저장 계약을 반영하지만, 기존 세션에 feedback이 거의 없으면 0으로 나올 수 있습니다.
