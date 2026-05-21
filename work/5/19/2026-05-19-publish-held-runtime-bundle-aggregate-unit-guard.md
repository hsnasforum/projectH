# 2026-05-19 publish held runtime bundle aggregate unit guard

## 변경 파일

- `work/5/19/2026-05-19-publish-held-runtime-bundle-aggregate-unit-guard.md`
- 검증 대상 기존 dirty runtime/docs bundle
  - `pipeline_runtime/automation_health.py`
  - `pipeline_runtime/supervisor.py`
  - `watcher_core.py`
  - `watcher_prompt_assembly.py`
  - `tests/test_pipeline_runtime_automation_health.py`
  - `tests/test_pipeline_runtime_supervisor.py`
  - `tests/test_watcher_core.py`
  - `.pipeline/README.md`
  - `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- 이번 라운드에서는 source/test/docs 파일을 수정하지 않았습니다.

## 사용 skill

- `work-log-closeout`: handoff #1967의 aggregate unit guard 결과, 실제 검증 명령, publication hold 상태, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1967`이 advisory-disabled runtime/docs dirty bundle을 하나의 local aggregate unit guard로 확인하라고 지시했습니다.
- 확인 대상은 runtime status surface, prompt assembly, publish-held operator retriage, source-reload guard, fail-closed metadata guard가 함께 깨지지 않는지였습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `tests.test_pipeline_runtime_automation_health` 전체 모듈과 지정된 supervisor/watcher focused tests를 함께 재실행했습니다.
- advisory-disabled profile에서 `advisory_followup` 계열 reason이 `verify_followup`으로 표면화되는 경로를 aggregate evidence로 확인했습니다.
- `commit_push_bundle_authorization` / publish-held retriage prompt / source-reload watcher restart / fail-closed follow-up 경로가 함께 통과하는지 확인했습니다.
- aggregate evidence가 모두 통과해 source/test/docs 수정은 하지 않았습니다.

## 검증

- `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_commit_push_bundle_authorization_operator_gate_routes_to_triage tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_advisory_disabled_operator_candidate_routes_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_source_change_restarts_watcher_without_operator_decision tests.test_watcher_core.WatcherPromptAssemblyTest.test_verify_prompt_context_includes_runtime_dispatch_surface tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_keeps_commit_push_in_verify_owner tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_advisory_disabled_commit_push_holds_publication_locally tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_preserves_source_reason tests.test_watcher_core.TurnResolutionTest.test_satisfied_commit_push_bundle_authorization_routes_to_verify_followup tests.test_watcher_core.TurnResolutionTest.test_dirty_commit_push_bundle_authorization_routes_to_verify_followup tests.test_watcher_core.RollingSignalTransitionTest.test_operator_retriage_no_next_control_advisory_disabled_returns_to_verify tests.test_watcher_core.RollingSignalTransitionTest.test_pr_merge_recovery_no_next_control_advisory_disabled_returns_to_verify`
  - 통과: `Ran 48 tests ... OK`.
- `rg -n "advisory_disabled|verify_followup|commit_push_bundle_authorization|PUBLISH_HELD|hold the publish backlog|runtime_controls|fail-closed|classification_fallback_detected" pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 확인: runtime/docs/test surface가 advisory-disabled, publish-held, fail-closed 계약을 같은 방향으로 설명/검증하고 있음을 확인했습니다.
- `git status --short -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-publish-held-runtime-bundle-aggregate-unit-guard.md .pipeline/implement_handoff.md .pipeline/advisory_request.md .pipeline/operator_request.md`
  - closeout 작성 전 기존 dirty runtime/docs bundle만 남아 있고, 이번 라운드 source/test/docs 수정은 없음을 확인했습니다.
- `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/19/2026-05-19-publish-held-runtime-bundle-aggregate-unit-guard.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 aggregate local unit evidence 확인 범위였으며 Playwright/E2E, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
