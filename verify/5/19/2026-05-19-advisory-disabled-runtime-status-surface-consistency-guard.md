STATUS: verified
WORK: work/5/19/2026-05-19-advisory-disabled-runtime-status-surface-consistency-guard.md
PREVIOUS_VERIFY: verify/5/19/2026-05-19-advisory-disabled-publish-held-backlog-inventory.md
CONTROL_SEQ_NEXT: 1962
ADVISORY_ENABLED: false

# 검증 기록

## 요약

최신 `/work`는 advisory-disabled profile에서 watcher runtime exporter가 `runtime_controls`를 status payload에 포함하지 않아 `stale_control_advisory`가 `advisory_followup`으로 표면화될 수 있던 경로를 닫은 구현 기록입니다.

현재 작업트리 기준으로 compile, focused unittest, whitespace 검사를 재실행했고 모두 통과했습니다. `watcher_core._write_runtime_status()`가 `runtime_controls`를 포함하도록 바뀐 점과 `tests/test_watcher_core.py`의 dispatch surface 테스트가 `automation_next_action: verify_followup`을 확인하는 점도 확인했습니다.

## 확인한 대상

- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `watcher_prompt_assembly.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/19/2026-05-19-advisory-disabled-runtime-status-surface-consistency-guard.md`

## 실행한 검증

- `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.AutomationHealthTest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_advisory_disabled_operator_candidate_routes_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_next_direction_after_launcher_close tests.test_watcher_core.WatcherPromptAssemblyTest.test_verify_prompt_context_includes_runtime_dispatch_surface tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_advisory_disabled_returns_to_verify`
  - 통과: `Ran 11 tests ... OK`.
- `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-advisory-disabled-runtime-status-surface-consistency-guard.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 실행하지 않은 검증

- Playwright/E2E, `make e2e-test`, socket-dependent controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다. 이번 변경은 runtime status exporter와 단위 회귀 테스트 범위입니다.
- `pipeline_runtime.cli` source-reload 단위 테스트와 supervisor watcher self-restart 단위 테스트는 이번 검증에서 실행하지 않았습니다. 다만 최신 `/work`의 잔여 리스크가 "이미 떠 있는 old watcher/supervisor가 새 코드를 아직 import하지 않았을 수 있음"이므로, 다음 로컬 slice에서 이 reload 안전망을 focused unit guard로 확인하는 것이 적절합니다.

## 변경 파일

- 없음. 이번 검증은 최신 `/work`의 구현 주장을 재확인했으며 제품 코드, 테스트, 문서 파일은 수정하지 않았습니다.

## 판정

- `VERIFY_DONE`.
- `ADVISORY_ENABLED=false` 조건에서는 `.pipeline/advisory_request.md`를 쓰지 않습니다.
- 현재 `RUNTIME_STATUS_AT_DISPATCH`는 `automation_health: ok`, `automation_next_action: continue`이므로 lane-local runtime command conflict나 operator-only runtime boundary는 확인되지 않았습니다.
- publication backlog는 여전히 별도 외부 publication boundary이지만, 이번 verify dispatch에는 명시적인 publication execution approval이 없습니다. commit, push, branch publication, PR creation/reuse/update, merge, release는 실행하지 않았고 implement lane으로 넘기지 않습니다.

## 다음 컨트롤 판단

COUNCIL_DECISION: implement
REASON_CODE: advisory_disabled_runtime_reload_unit_guard
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 1962
EVIDENCE:
- `work/5/19/2026-05-19-advisory-disabled-runtime-status-surface-consistency-guard.md`
- `verify/5/19/2026-05-19-advisory-disabled-runtime-status-surface-consistency-guard.md`
- `pipeline_runtime/cli.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_pipeline_runtime_supervisor.py`
REJECTED:
- `.pipeline/advisory_request.md`: advisory is disabled for this chain.
- `.pipeline/operator_request.md`: publication remains a real boundary, but no explicit publication execution approval exists and a local reload guard can reduce the current runtime risk without publishing.
- commit/push/PR/merge handoff: implement prompts forbid publication work.
