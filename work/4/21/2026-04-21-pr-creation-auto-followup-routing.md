# 2026-04-21 PR creation auto followup routing

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/status_labels.py`
- `pipeline_runtime/supervisor.py`
- `watcher_prompt_assembly.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/README.md`
- `verify/README.md`
- `report/gemini/2026-04-21-automation-axis-closure-and-pr-transition.md`
- `work/4/21/2026-04-21-pr-creation-gate-visible-boundary.md`
- `work/4/21/2026-04-21-pr-creation-auto-followup-routing.md`

## 사용 skill
- `security-gate`: draft PR 생성은 외부 publication surface라서 merge/destructive/auth/truth-sync 경계와 분리해 감사 가능하게 유지했습니다.
- `doc-sync`: runtime docs, pipeline README, agent/operator rules, work/verify README를 새 자동 PR follow-up 계약에 맞췄습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 이 closeout에 기록했습니다.
- `github:yeet`: 커밋, 푸시, draft PR 생성 경로를 확인하고 PR #25를 만들었습니다.

## 변경 이유
- 사용자가 PR 생성까지 자동화하라고 명시했으므로, 이전의 `pr_creation_gate = operator boundary` 결론을 유지하면 automation 목표와 충돌합니다.
- 다만 implement lane은 여전히 commit/push/PR publish가 금지되어 있으므로, PR 생성은 verify/handoff owner publish follow-up으로만 처리해야 합니다.
- merge, destructive publication change, auth/credential, approval-record/truth-sync blocker까지 자동화하면 안전 경계가 무너지므로 이번 slice는 draft PR 생성 또는 기존 PR 재사용까지만 다룹니다.

## 핵심 변경
- `pr_creation_gate`를 immediate operator reason에서 빼고 internal publish follow-up reason으로 등록했습니다.
- `pr_creation_gate + gate_24h + release_gate`는 `mode=triage`, `routed_to=codex_followup`, `automation_next_action=verify_followup`으로 surface됩니다.
- operator retriage prompt에 draft PR 생성 또는 기존 PR 재사용, PR URL `/work` 기록, 다음 control 작성 규칙을 추가했습니다.
- verify/followup prompt의 publish guard를 commit/push에서 commit/push/PR로 확장해 implement lane으로 PR 생성을 넘기지 않게 했습니다.
- GUI/status label에는 `PR 자동 생성 정리 중` 표시를 추가했습니다.
- 이전 closeout에는 supersede 메모를 남겨 `needs_operator + pr_boundary` 결론이 새 정책으로 대체됐음을 명시했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py pipeline_runtime/status_labels.py pipeline_runtime/supervisor.py watcher_prompt_assembly.py watcher_core.py` -> 통과
- `python3 -m unittest tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_pr_creation_gate_routes_to_verify_publish_followup tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_pr_creation_gate_maps_to_verify_followup_attention tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_routes_pr_creation_gate_to_verify_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_pr_creation_gate_routes_to_verify_owner_publish_followup` -> 4 tests OK
- `python3 -m unittest tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_keeps_commit_push_in_verify_owner tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_prompt_prefers_gemini_before_operator_for_slice_ambiguity tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_followup_prompt_only_uses_operator_after_inconclusive_gemini_advice tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_prompt_templates_follow_role_bound_prompt_owners_when_lanes_exist` -> 4 tests OK
- `python3 -m unittest tests.test_operator_request_schema` -> 13 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health` -> 18 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` -> 128 tests OK
- `python3 -m unittest tests.test_watcher_core` -> 181 tests OK
- `python3 -m unittest tests.test_pipeline_gui_home_presenter` -> 18 tests OK
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py pipeline_runtime/status_labels.py pipeline_runtime/supervisor.py watcher_prompt_assembly.py watcher_core.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py tests/test_pipeline_gui_home_presenter.py AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md work/README.md verify/README.md .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` -> 통과
- `git diff --cached --check` -> 통과
- `git commit -m "Route PR creation gates to publish follow-up"` -> `c82eeea`
- `git push -u origin feat/watcher-turn-state` -> 통과
- GitHub draft PR 생성 -> `https://github.com/hsnasforum/projectH/pull/25`
- live status 확인 전: 이전 supervisor/watcher 프로세스는 아직 old code를 물고 있어 `.pipeline/operator_request.md` seq 717을 `needs_operator`로 보고 있었습니다. 이 closeout 이후 runtime restart로 새 routing을 확인해야 합니다.

## 남은 리스크
- 이번 변경은 watcher가 직접 `gh pr create`를 실행하는 구현이 아니라, verify/handoff owner가 자동 publish follow-up으로 draft PR을 만들도록 라우팅하는 단계입니다.
- 현재 변경은 draft PR #25로 올라갔습니다. merge는 자동화하지 않았고, operator/release boundary로 남깁니다.
- auth/credential 실패, base/head 불명확, merge 또는 milestone 전환까지 요구되는 경우는 여전히 operator/advisory follow-up으로 남겨야 합니다.
