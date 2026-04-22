# 2026-04-23 Milestone 11 Axis 2 path restriction

## 변경 파일
- `core/operator_executor.py`
- `tests/test_operator_executor.py`
- `tests/test_operator_audit.py`
- `work/4/23/2026-04-23-milestone11-axis2-path-restriction.md`

## 사용 skill
- `approval-flow-audit`: approval 이후 실행되는 로컬 파일 쓰기 경계가 명시적 승인 흐름을 우회하지 않는지 확인했습니다.
- `security-gate`: `target_id` 쓰기/rollback 대상이 프로젝트 루트 밖으로 벗어나지 않도록 경로 제한과 테스트 범위를 점검했습니다.
- `finalize-lite`: 지정 검증 결과와 문서 동기화 필요 여부를 구현 범위 안에서 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 명령, 남은 리스크를 `/work` 기록으로 남겼습니다.

## 변경 이유
- Milestone 11 Axis 2 handoff(`CONTROL_SEQ: 911`)에 따라 operator action의 `target_id`가 `Path.cwd().resolve()` 밖으로 해석되는 경우 실행과 rollback을 차단해야 했습니다.
- 기존 테스트 임시 파일은 기본적으로 `/tmp`에 생성되어 새 sandbox 정책과 충돌하므로 CWD 내부에서 생성되도록 보정해야 했습니다.

## 핵심 변경
- `core/operator_executor.py`에 `_validate_operator_action_target(target_id)`를 추가해 resolved target path가 현재 프로젝트 루트 밖이면 `ValueError`를 발생시키도록 했습니다.
- `execute_operator_action`과 `rollback_operator_action` 모두에서 `target_id` 비어 있음 검증 직후 sandbox 검증을 호출하도록 연결했습니다.
- `tests/test_operator_executor.py`의 `NamedTemporaryFile` 사용 5곳을 `dir="."`로 바꾸고, missing-file 및 missing-backup 테스트의 절대 외부 경로를 CWD 내부 nonexistent path로 바꿨습니다.
- `/etc/passwd` 대상 실행과 rollback이 각각 거부되는 path restriction 테스트 2건을 추가했습니다.
- `tests/test_operator_audit.py`의 audit trail 임시 파일도 CWD 내부에서 생성되도록 바꿨습니다.

## 검증
- `python3 -m py_compile core/operator_executor.py tests/test_operator_executor.py tests/test_operator_audit.py`
  - 통과
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit -v 2>&1 | tail -14`
  - `Ran 35 tests in 0.031s`
  - `OK`

## 남은 리스크
- 이번 slice는 executor helper와 단위 테스트 범위만 변경했습니다. approval route, session history, UI rollback trigger는 아직 새 sandbox 정책을 사용자 흐름으로 노출하거나 감사 기록으로 확장하지 않았습니다.
- rollback backup path 자체의 sandbox/retention 정책은 별도 축으로 남아 있습니다.
- 문서 파일은 handoff의 편집 대상이 아니어서 수정하지 않았습니다. 현재 closeout에 구현 truth만 기록했습니다.
