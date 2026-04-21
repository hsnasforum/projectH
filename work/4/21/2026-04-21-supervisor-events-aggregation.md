# 2026-04-21 supervisor events aggregation

## 변경 파일
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/21/2026-04-21-supervisor-events-aggregation.md` (새 파일)

## 사용 skill
- `security-gate`: supervisor `events.jsonl` 집계 회귀 테스트가 로그/감사 경계에 영향을 주는지 확인했습니다. 새 승인, 삭제, 덮어쓰기, 외부 네트워크, commit/push/PR 동작은 추가하지 않았습니다.
- `finalize-lite`: 구현 라운드 종료 전에 실행한 검증, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 실측 결과, 남은 리스크를 표준 `/work` 형식으로 정리했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` CONTROL_SEQ 632 지시에 따라 supervisor가 wrapper lane task event를 `events.jsonl`에 `source="wrapper"`로 실제 기록하는지 고정하는 회귀 테스트를 추가했습니다.
- handoff의 Step 2 확인 결과, 현재 aggregation 호출 경로는 정상 동작했습니다. 따라서 `pipeline_runtime/supervisor.py`의 `_mirror_wrapper_task_events` 구현은 수정하지 않았습니다.

## 핵심 변경
- `RuntimeSupervisorTest.test_mirror_wrapper_task_events_appends_to_events_jsonl`를 추가했습니다.
- 테스트는 임시 run directory의 `wrapper-events/codex.jsonl`에 `DISPATCH_SEEN` 이벤트를 쓰고, `RuntimeSupervisor.__new__`로 최소 필드만 구성한 뒤 `_mirror_wrapper_task_events()`를 직접 호출합니다.
- `events.jsonl` 생성 여부, `source == "wrapper"` 항목 1건, `event_type == "DISPATCH_SEEN"`, `payload.job_id == "ctrl-1"`를 확인합니다.
- handoff 예시 fixture에는 `append_wrapper_event(..., source=...)`가 없었지만 현재 함수 시그니처가 `source` 키워드를 필수로 요구하므로 `source="wrapper"`를 추가했습니다.
- 첫 Step 2 실행은 fixture 시그니처 오류로 `TypeError: append_wrapper_event() missing 1 required keyword-only argument: 'source'`가 발생했습니다. 테스트 fixture 보정 후 재실행은 PASS였습니다.

## 검증
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_mirror_wrapper_task_events_appends_to_events_jsonl`
  - 첫 실행: `FAILED (errors=1)` / `TypeError: append_wrapper_event() missing 1 required keyword-only argument: 'source'`
  - `source="wrapper"` fixture 보정 후 재실행: `Ran 1 test in 0.004s`, `OK`
- `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_mirror_wrapper_task_events_appends_to_events_jsonl`
  - `Ran 1 test in 0.005s`
  - `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 117 tests in 0.898s`
  - `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - `Ran 8 tests in 0.002s`
  - `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 출력 없음, `rc=0`

## 남은 리스크
- 이번 라운드는 aggregation 회귀 테스트 추가에 한정했고 production supervisor 프로세스 재시작이나 live run 재검증은 수행하지 않았습니다.
- `pipeline_runtime/supervisor.py`의 현재 코드 경로는 신규 회귀 테스트에서 정상으로 확인됐으므로 live gap은 handoff 가설대로 구버전 프로세스 또는 기존 run 상태 영향일 수 있습니다.
- branch commit/push/PR은 진행하지 않았습니다. handoff 기준 operator 결정 C는 여전히 대기입니다.
