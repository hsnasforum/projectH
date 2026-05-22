# 2026-05-21 schema write logging role harness none

## 변경 파일
- `pipeline_runtime/schema.py`
- `pipeline_runtime/role_harness.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_pipeline_runtime_role_harness.py`
- `work/5/21/2026-05-21-schema-write-logging-role-harness-none.md`

## 사용 skill
- `security-gate`: local runtime 파일 쓰기 실패 로깅이 쓰기 승인/전파 경계를 바꾸지 않고 관측 가능성만 높이는지 확인하기 위해 사용했습니다.
- `finalize-lite`: 실행한 검증과 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `atomic_write_json()`과 `atomic_write_text()`는 tmp 파일 쓰기 또는 replace 실패 시 `OSError`를 전파하지만, 호출 측에서 예외를 삼키면 실패 경로 추적이 어려웠습니다.
- `role_harness_path()`는 미등록 역할에 대해 빈 문자열을 반환해, 호출 측이 유효한 문자열 경로로 오인할 여지를 남겼습니다.
- 기존 falsy check와 호환되는 `None` 반환으로 미등록 역할을 더 명확히 표현하는 것이 목적이었습니다.

## 핵심 변경
- `pipeline_runtime/schema.py`에 module logger를 추가했습니다.
- `atomic_write_json()` 실패 시 `logging.exception("atomic_write_json failed: %s", path)`를 남기고 기존처럼 `OSError`를 재전파합니다.
- `atomic_write_text()`도 동일하게 실패 경로를 logging으로 남기고 예외 재전파를 유지합니다.
- `role_harness_path()` 반환 타입을 `str | None`으로 바꾸고, 미등록 역할에는 `None`을 반환하도록 변경했습니다.
- schema 테스트에 atomic write 실패 로그와 재전파 회귀 테스트를 추가했고, role harness 테스트에 등록/미등록 역할 반환값을 갱신했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/role_harness.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_pipeline_runtime_role_harness -v`
  - 결과: `Ran 58 tests in 0.122s`, `OK`.
- 통과: `python3 -c "... role_harness_path('implement') ... role_harness_path('unknown_xyz') ..."`
  - 결과: `role_harness OK`.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5`
  - 결과: `Ran 277 tests in 1.977s`, `OK`.
- 통과: `git diff --check -- pipeline_runtime/schema.py pipeline_runtime/role_harness.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- logging 설정 자체는 이번 slice의 OUT_OF_SCOPE라 변경하지 않았습니다.
- 호출 측 코드는 변경하지 않았습니다. 기존 `if not path:`류 falsy check와 `None` 반환은 호환된다는 전제입니다.
- 전체 repo unittest discover, browser/E2E, live runtime/tmux 검증은 실행하지 않았습니다.
- 현재 worktree에는 이전 Claude print JSONL lane integration 및 turn arbitration constant dedup 관련 수정/기록 파일이 남아 있습니다. 이번 slice에서는 관련 없는 기존 변경을 되돌리거나 포함하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
