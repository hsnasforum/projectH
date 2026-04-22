# 2026-04-23 Milestone 13 Axis 3 effectiveness metric

## 변경 파일
- `storage/session_store.py`
- `scripts/audit_traces.py`
- `tests/test_session_store.py`
- `work/4/23/2026-04-23-milestone13-axis3-effectiveness-metric.md` (이 파일)

## 사용 skill
- `security-gate`: session summary와 audit 출력이 로컬 session 기록 기반 읽기/집계 범위에 머무르는지 확인했다.
- `finalize-lite`: 지정 검증 결과와 implement-lane 금지사항 준수 여부를 점검했다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 Korean closeout으로 남겼다.

## 변경 이유
- M13 Axes 1-2에서 `applied_preference_ids`가 session message와 correction record에 연결됐다.
- CONTROL_SEQ 965 handoff에 따라 personalized response가 correction을 얼마나 유발하는지 추적할 baseline counter를 `get_global_audit_summary()`와 `audit_traces.py`에 추가했다.

## 핵심 변경
- `SessionStore.get_global_audit_summary()` summary dict에 `personalized_response_count`, `personalized_correction_count`를 추가했다.
- session message에 truthy `applied_preference_ids`가 있으면 personalized response로 집계하고, grounded brief + `corrected_text`가 함께 있으면 personalized correction으로 집계한다.
- `scripts/audit_traces.py`가 personalized response/correction count와 correction rate를 출력한다.
- `tests/test_session_store.py`에 personalized response 2건, personalized correction 1건을 확인하는 focused test를 추가했다.
- `preference_store.py`, `agent_loop.py`, `correction_store.py`, 계약 파일, `.pipeline` control slot은 수정하지 않았다.

## 검증
- `python3 -m py_compile storage/session_store.py scripts/audit_traces.py`
  - 통과, 출력 없음
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets tests.test_evaluate_traces -v 2>&1 | tail -5`
  - 최초 실행: `Ran 59 tests ... FAILED (failures=1)`
  - 원인: 새 테스트 fixture의 `original_response_snapshot`에 `artifact_id`/`artifact_kind`가 없어 session normalization 후 `corrected_text`가 보존되지 않았다.
  - fixture를 실제 grounded-brief message 형태에 맞춰 보정한 뒤 재실행: `Ran 59 tests in 0.063s`, `OK`
- `python3 scripts/audit_traces.py`
  - `personalized_response_count`: `0`
  - `personalized_correction_count`: `0`
  - `Personalized responses:   0`
  - `Personalization correction rate: N/A (no personalized responses yet)`
- `git diff --check -- storage/session_store.py scripts/audit_traces.py`
  - 통과, 출력 없음
- `git diff --check -- storage/session_store.py scripts/audit_traces.py tests/test_session_store.py`
  - 통과, 출력 없음

## 남은 리스크
- 현재 로컬 데이터 기준 personalized response/correction은 0건이다. 실제 효과율은 active preference가 적용된 이후 데이터가 쌓여야 의미가 생긴다.
- 이번 slice는 metric baseline만 추가했다. preference 활성화, 효과 판정 로직, UI 표시, 자동화 정책 변경은 포함하지 않았다.
- 기존 untracked `report/gemini/2026-04-23-m13-effectiveness-metric-scoping.md`와 `work/4/23/2026-04-23-milestone13-axis2-commit-push.md`는 선행 작업물로 남아 있으며 이번 round에서 수정하지 않았다.
- 커밋, 푸시, PR 생성, next-slice 선택, `.pipeline` control slot 작성은 수행하지 않았다.
