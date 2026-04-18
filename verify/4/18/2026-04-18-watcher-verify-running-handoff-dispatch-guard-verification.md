# 2026-04-18 watcher verify-running handoff dispatch guard verification

## 변경 파일
- `verify/4/18/2026-04-18-watcher-verify-running-handoff-dispatch-guard-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-watcher-verify-running-handoff-dispatch-guard.md`에 아직 matching `/verify`가 없어서, 그대로 새 control slot만 열면 canonical truth-sync를 건너뛰게 됩니다.
- 동시에 blocked `CONTROL_SEQ: 293` handoff는 controller scenario 10 tighten을 요구했지만, 현재 작업 트리에는 그 테스트/문서 계약이 이미 들어와 있으므로 stale handoff를 그대로 유지할 수 없었습니다.

## 핵심 변경
- latest watcher `/work`의 주장부터 다시 검증했습니다. `watcher_core.py`는 `_get_current_run_jobs(...)`로 current run의 `VERIFY_RUNNING` job을 먼저 집어 계속 step하고, verify close 직후 `_flush_pending_claude_handoff()`를 다시 태워 pending Claude handoff release를 같은 polling cycle 안에서 이어가도록 되어 있습니다. 관련 focused 검증은 모두 다시 통과했습니다.
- blocked seq 293의 전제는 더 이상 current truth가 아닙니다. `e2e/tests/controller-smoke.spec.mjs`의 scenario 10은 지금 `claude_desk` zone 안에서 `x`와 `y`를 모두 assert하고 있고, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`도 그 동일한 zone-bounded contract를 이미 적고 있습니다. 따라서 controller scenario 10을 다시 구현시키는 handoff는 stale입니다.
- latest watcher round를 truthfully 닫은 뒤의 다음 same-family current-risk reduction은 `pipeline_runtime/supervisor.py::_build_active_round()` 보정입니다. 현재 구현은 visible round를 사실상 최신 `updated_at` 중심으로 고르므로, stale `VERIFY_PENDING` 또는 older verify job이 thin-client `active_round` surface를 다시 current truth처럼 보이게 만들 수 있습니다. `.pipeline/claude_handoff.md`는 이 exact slice로 `CONTROL_SEQ: 294`를 열도록 갱신했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.ClaudeHandoffDispatchTest tests.test_watcher_core.VerifyCompletionContractTest`
  - 결과: `Ran 17 tests`, `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과
- 직접 대조:
  - 대상: `.pipeline/claude_handoff.md`, `e2e/tests/controller-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`
  - 결과: seq 293이 전제한 controller scenario 10 gap은 current 작업 트리에서 이미 해소되어 있음을 확인했습니다.
- 이번 라운드에서는 controller Playwright나 broader runtime suite는 다시 실행하지 않았습니다.
  - 이유: blocked triage의 핵심은 latest watcher `/work` truth 재검증과 stale controller handoff 대체였고, controller 쪽은 파일 대조만으로 `already_implemented` 여부를 충분히 판정할 수 있었기 때문입니다.

## 남은 리스크
- `pipeline_runtime/supervisor.py::_build_active_round()`는 여전히 latest `updated_at` 중심으로 round를 고르므로, stale `VERIFY_PENDING`/older verify job이 controller/launcher/pipeline GUI의 current `active_round` surface를 다시 섞어 보일 가능성은 남아 있습니다.
- 이번 verify는 watcher dispatch guard와 stale controller handoff triage만 닫았습니다. supervisor current-surface selection 보정 전에는 예전 round가 current처럼 보이는 다른 경로가 남아 있을 수 있습니다.
