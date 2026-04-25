STATUS: verified
CONTROL_SEQ: manual-hibernate-stale-working
BASED_ON_WORK: work/4/24/2026-04-24-hibernate-stale-working-surface.md
VERIFIED_BY: Codex
NEXT_CONTROL: unchanged

---

## Hibernate Stale Working Surface

### Verdict

PASS. Claude pane이 idle인데 controller/status가 working처럼 보이던 stale progress 표면을 제거했습니다.

### Checks Run

- `python3 -m py_compile pipeline_runtime/turn_arbitration.py pipeline_runtime/supervisor.py tests/test_turn_arbitration.py tests/test_pipeline_runtime_supervisor.py` -> OK
- `python3 -m unittest tests.test_turn_arbitration.WatcherTurnArbitrationTest.test_operator_gate_hibernate_suppresses_stale_verify_need tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_stale_verify_progress_during_operator_hibernate` -> `Ran 2 tests`, OK
- `python3 -m unittest tests.test_turn_arbitration tests.test_pipeline_runtime_supervisor` -> `Ran 156 tests in 1.187s`, OK
- `bash stop-pipeline.sh` -> OK
- `bash start-pipeline.sh` -> OK
- `python3 -m pipeline_runtime.cli status . --json` -> final status `RUNNING`, `turn_state=IDLE`, `progress={}`, no lane `progress_phase`
- `cat .pipeline/runs/20260424T052542Z-p434030/task-hints/claude.json` -> `active=false`
- `tmux capture-pane -t aip-projectH:0.0 -p -S -40` -> Claude idle prompt visible
- `git diff --check` -> OK

### Residual Risk

- Runtime is healthy and idle, but `.pipeline/operator_request.md` still hibernates on `m28_direction + pr_merge_gate`; that is now displayed truthfully instead of as active Claude work.
- This note does not resolve the separate automation policy issue that safe local implementation should continue while PR merge approval remains pending.
