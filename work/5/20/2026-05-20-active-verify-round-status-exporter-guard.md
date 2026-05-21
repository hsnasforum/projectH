# 2026-05-20 active verify round status exporter guard

## 변경 파일

- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-active-verify-round-status-exporter-guard.md`

## 사용 skill

- `finalize-lite`: 구현 범위가 focused supervisor regression guard에 머물렀는지, 문서 동기화나 넓은 smoke가 필요한지 점검하기 위해 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1998`가 `turn_state=IDLE`인 exported status에 active verify round가 남아 있을 때 launcher-facing health가 `ok/continue`로 숨겨지지 않는 supervisor/exported-status guard를 요구했습니다.
- 직전 helper-level 검증은 `pipeline_runtime/automation_health.py`가 `IDLE + VERIFY_PENDING|VERIFYING`을 `recovering/dispatch_stall/retrying`으로 계산함을 확인했지만, supervisor가 쓰는 exported `status.json` 경로의 focused regression은 아직 별도로 고정되지 않았습니다.

## 핵심 변경

- `tests/test_pipeline_runtime_supervisor.py`에 `test_write_status_surfaces_idle_active_verify_round_as_recovering`을 추가했습니다.
- 새 테스트는 `turn_state=IDLE`, active `implement_handoff`, active verify job 조합에서 `VERIFY_PENDING`과 `VERIFY_RUNNING` 두 job status를 모두 확인합니다.
- 기대값은 exported status 기준 `automation_health=recovering`, `automation_reason_code=dispatch_stall`, `automation_next_action=retrying`입니다.
- active round `dispatch_stage`가 비어 있어도 active verify round 자체가 `ok/continue`로 숨겨지지 않는다는 점을 고정했습니다.
- 새 regression은 현재 source 수정 없이 통과했습니다. 이번 라운드에서 `pipeline_runtime/supervisor.py`와 `pipeline_runtime/automation_health.py`는 수정하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `cb03bd5816b743ebb76962f6b4c8fbfc953ba4ea08648a7581d98096db7354e2`와 일치했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_idle_active_verify_round_as_recovering`
  - 결과: PASS. `Ran 1 test in 0.014s`, `OK`.
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS, 출력 없음.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS, 출력 없음.
- `rg -n "test_write_status_surfaces_idle_active_verify_round_as_recovering|automation_health.*recovering|automation_next_action.*retrying|active_round.*expected_round_state" tests/test_pipeline_runtime_supervisor.py`
  - 결과: CHECK. 새 테스트와 핵심 assertion 위치를 확인했습니다.

## 남은 리스크

- 이번 라운드는 supervisor/exported-status focused regression만 추가했습니다. full `tests.test_pipeline_runtime_supervisor`, full runtime/watcher suite, controller startup, Playwright/e2e, long soak는 실행하지 않았습니다.
- `tests/test_pipeline_runtime_supervisor.py`, `pipeline_runtime/supervisor.py`, `pipeline_runtime/automation_health.py`에는 이번 라운드 이전부터 존재하던 미커밋 변경이 섞여 있습니다. 이번 라운드에서는 새 exported-status regression만 추가했고 기존 변경은 되돌리지 않았습니다.
- source 수정 없이 테스트가 통과했으므로 문서 추가 동기화는 수행하지 않았습니다.
