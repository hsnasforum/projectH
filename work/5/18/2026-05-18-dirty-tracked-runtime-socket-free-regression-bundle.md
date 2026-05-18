# 2026-05-18 dirty tracked runtime socket free regression bundle

## 변경 파일
- `work/5/18/2026-05-18-dirty-tracked-runtime-socket-free-regression-bundle.md`

## 사용 skill
- `work-log-closeout`: handoff가 요구한 socket-free runtime unit 회귀 묶음의 실제 통과/실패 결과와 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- `CONTROL_SEQ: 1906` handoff는 현재 tracked watcher/verify dirty set에 대해 socket/server를 열지 않는 broader runtime unit regression bundle을 실행하고 결과만 기록하라고 지시했습니다.
- `CONTROL_SEQ: 1905`에서 targeted `py_compile`과 3개 unittest 모듈은 통과했으므로, 이번 라운드는 더 넓은 runtime unit 묶음의 현재 상태를 확인하는 증거 수집 guard입니다.
- 이번 라운드는 source/test 수정, stash 적용/삭제, publication 판단이 아니라 검증 결과 기록만 수행하는 범위입니다.

## 핵심 변경
- production code, tests, docs, prompts, runtime behavior, pipeline control은 수정하지 않았습니다.
- `git status --short -- ...` 기준 tracked modified 파일은 `tests/test_pipeline_runtime_supervisor.py`, `tests/test_verify_fsm.py`, `tests/test_watcher_core.py`, `verify_fsm.py`, `watcher_core.py`, `watcher_dispatch.py`, `watcher_prompt_assembly.py` 7개입니다.
- `git diff --stat -- ...` 기준 위 7개 파일은 `7 files changed, 529 insertions(+), 15 deletions(-)`입니다.
- `python3 -m py_compile verify_fsm.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py`는 출력 없이 통과했습니다.
- broader unittest 명령은 525개 테스트를 실행했지만 `tests.test_pipeline_runtime_receipts`와 `tests.test_pipeline_runtime_wrapper_events` import 실패 2건으로 실패했습니다.
- `stash@{0}`는 `codex-clean-worktree-2026-05-18` 메시지로 계속 보존되어 있으며 apply/pop/drop/clear/branch/store/rewrite/discard하지 않았습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md`: PASS, `4b737814d95f818d223ae0da9ae025a2b9c669ad45e144933704cadd66a6aa78`로 handoff 입력 SHA와 일치했습니다.
- `git status --short -- tests/test_pipeline_runtime_supervisor.py tests/test_verify_fsm.py tests/test_watcher_core.py verify_fsm.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py`: PASS/INFO, 위 7개 파일이 `M` 상태임을 확인했습니다.
- `git diff --stat -- tests/test_pipeline_runtime_supervisor.py tests/test_verify_fsm.py tests/test_watcher_core.py verify_fsm.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py`: PASS/INFO, `7 files changed, 529 insertions(+), 15 deletions(-)` 확인.
- `python3 -m py_compile verify_fsm.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py`: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_control_writers tests.test_pipeline_runtime_receipts tests.test_pipeline_runtime_schema tests.test_pipeline_runtime_wrapper_events tests.test_pipeline_runtime_supervisor tests.test_verify_fsm tests.test_watcher_core`: FAIL, `Ran 525 tests in 9.186s`, `FAILED (errors=2)`.
- unittest 실패 원인: `ModuleNotFoundError: No module named 'tests.test_pipeline_runtime_receipts'`, `ModuleNotFoundError: No module named 'tests.test_pipeline_runtime_wrapper_events'`.
- `rg --files tests | rg 'test_pipeline_runtime_(receipts|wrapper_events)\.py$'`: FAIL/INFO, 출력 없음. 두 테스트 모듈 파일이 현재 워크트리에 없음을 확인했습니다.
- `git status --short -- tests/test_pipeline_runtime_receipts.py tests/test_pipeline_runtime_wrapper_events.py`: PASS/INFO, 출력 없음.
- `git stash list --max-count=1`: PASS, `stash@{0}: On feat/m124-axis2-investigation-quality-summary: codex-clean-worktree-2026-05-18` 확인.
- `git diff --check -- work/5/18/2026-05-18-dirty-tracked-runtime-socket-free-regression-bundle.md`: PASS, 출력 없음.
- `git status --short -- work/5/18/2026-05-18-dirty-tracked-runtime-socket-free-regression-bundle.md .pipeline/advisory_request.md .pipeline/operator_request.md`: PASS/INFO, 새 `/work` 파일만 `??`로 표시되고 advisory/operator control 변경은 없었습니다.

## 남은 리스크
- broader unittest 묶음은 지정된 두 테스트 모듈이 현재 워크트리에 없어 실패했습니다. 이번 implement handoff는 source/test 수정을 금지하므로 파일명 보정이나 테스트 목록 수정은 하지 않았습니다.
- 전체 unittest, Playwright, `make e2e-test`, live tmux E2E, local socket/server startup, runtime start/stop, long soak는 실행하지 않았습니다.
- 현재 tracked source/test 변경의 채택, 분리, 수정, 되돌림, publish 여부는 판단하지 않았습니다.
- `stash@{0}`는 여전히 대형 보존물이며 이번 라운드에서 적용하거나 폐기하지 않았습니다.
- publication은 계속 held 상태입니다. commit, push, branch/PR publication, PR creation/reuse, merge, release, external publication, readiness claim은 수행하지 않았습니다.
