## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/21/2026-04-21-g4-task-hint-corroboration-fields.md`

## 사용 skill
- `onboard-lite`: handoff, 관련 코드 경로, 기존 `/work`·`/verify`를 최소 범위로 확인했습니다.
- `finalize-lite`: handoff가 요구한 검증 3개만 다시 실행하고 closeout 사실관계를 정리했습니다.

## 변경 이유
- implement-owner lane이 active control seq를 갖고 있어도 `active_round.job_id`와 `dispatch_id`가 비어 있으면 task hint에 corroboration 필드가 비어 남았습니다.
- 이 상태에서는 wrapper emitter가 implement lane `DISPATCH_SEEN`을 만들지 못해, supervisor의 `signal_mismatch` 가드가 계속 발동할 수 있어 handoff가 지시한 emitter-side follow-on 보강이 필요했습니다.

## 핵심 변경
- `pipeline_runtime/supervisor.py`의 `_write_task_hints`에서 implement owner가 active이고 `active_control_seq >= 0`인 경우, `active_round`에 값이 없더라도 `job_id`를 `ctrl-<seq>`, `dispatch_id`를 `seq-<seq>`로 채우도록 추가했습니다.
- verify lane의 `use_verify_round_hint` 경로와 다른 lane의 빈 payload 동작은 그대로 유지했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 `test_write_task_hints_implement_lane_has_dispatch_fields_when_active`를 추가해, implement owner `Codex` active hint에는 synthetic field가 채워지고 `Claude`/`Gemini`는 inactive + 빈 field를 유지하는지 고정했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 103 tests in 0.663s`
  - `OK`
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 출력 없음, `rc=0`

## 남은 리스크
- 이번 변경은 implement lane task hint에 synthetic corroboration 필드를 채우는 범위만 다룹니다. `pipeline_runtime/cli.py`의 실제 `DISPATCH_SEEN` emit 경로 자체는 이번 라운드에서 바꾸지 않았습니다.
- handoff가 지정한 `tests.test_pipeline_runtime_supervisor`만 재실행했습니다. 다른 runtime/browser suite는 이번 slice 범위 밖입니다.
