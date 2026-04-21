# 2026-04-21 commit/push bundle authorization routing

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
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/README.md`
- `verify/README.md`
- `work/4/21/2026-04-21-commit-push-bundle-authorization-routing.md`

## 사용 skill
- `security-gate`: commit/push 자동화가 작은 local slice나 무감사 publish로 번지지 않도록 승인/감사 경계를 확인했습니다.
- `doc-sync`: 새 `commit_push_bundle_authorization` reason과 routing 계약을 runtime docs, pipeline docs, agent/operator rule docs에 맞춰 반영했습니다.
- `work-log-closeout`: 실제 변경, 실행한 검증, live 확인 결과, 남은 리스크를 이 closeout에 기록했습니다.

## 변경 이유
- `.pipeline/operator_request.md` seq 713은 이미 큰 automation bundle에 대한 commit/push 승인 follow-up이었지만, `REASON_CODE: commit_push_bundle_authorization`이 canonical reason으로 등록되어 있지 않아 `OPERATOR_POLICY: internal_only`와 결합될 때 `codex_followup`이 아니라 `hibernate`로 분류됐습니다.
- 그 결과 사용자가 다시 호출되는 모양이 되었고, "큰 묶음은 자동 commit/push follow-up으로 처리하되 작은 slice는 publish하지 않는다"는 운영 방향과 충돌했습니다.

## 핵심 변경
- `COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON`을 shared reason constant로 추가하고 `SUPPORTED_REASON_CODES`에 포함되도록 `_INTERNAL_REASON_CODES`에 등록했습니다.
- `commit_push_bundle_authorization + internal_only`은 `mode=triage`, `routed_to=codex_followup`으로 분류되게 해 idle hibernate로 눕지 않게 했습니다.
- `release_gate`를 supported decision class로 등록해 live operator_request header가 schema drift로 빠지지 않게 했습니다.
- `is_commit_push_approval_stop(...)`은 기존 `approval_required`뿐 아니라 `commit_push_bundle_authorization`도 commit/push approval stop으로 인식합니다. 이미 push까지 끝난 clean/upstream 상태는 기존 `operator_approval_completed` recovery로 닫습니다.
- automation health는 이 reason의 triage를 `verify_followup`으로 표시하고, status label에는 `커밋/푸시 자동 정리 중`을 추가했습니다.
- watcher/supervisor/operator schema/automation health 테스트에 dirty bundle follow-up, completed publish recovery, supervisor gate routing 회귀 테스트를 추가했습니다.
- docs와 agent/operator README에는 이 reason이 "이미 승인된 큰 묶음 publish follow-up"이며 small/local dirty slice 자동 publish가 아니라는 경계를 명시했습니다.
- live 확인 중 verify/handoff owner가 commit/push 후속을 `.pipeline/claude_handoff.md` implement handoff로 다시 넘기는 2차 루프가 드러났습니다. `watcher_prompt_assembly.py`의 operator retriage / blocked triage prompt를 보강해 `commit_push_bundle_authorization + internal_only` publish follow-up은 verify/handoff owner가 처리하거나 advisory로 넘기고, implement lane에는 commit/push를 재발행하지 않도록 했습니다.
- normal verify/followup prompt도 다음 control을 작성할 수 있으므로, `watcher_prompt_assembly.py`와 `pipeline_runtime/supervisor.py` 양쪽의 verify/followup prompt에 commit/push publish work를 `.pipeline/claude_handoff.md`로 넘기지 말라는 guard를 추가했습니다.
- agent/operator docs에도 같은 경계를 추가해 implement lane의 "commit/push 금지" 규칙과 자동 publish follow-up 예외가 충돌하지 않게 했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py pipeline_runtime/status_labels.py watcher_core.py` -> 통과
- `python3 -m unittest tests.test_operator_request_schema` -> 12 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health` -> 17 tests OK
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest.test_satisfied_commit_push_bundle_authorization_routes_to_codex_followup tests.test_watcher_core.TurnResolutionTest.test_dirty_commit_push_bundle_authorization_routes_to_codex_followup tests.test_watcher_core.TurnResolutionTest.test_satisfied_commit_push_operator_request_routes_to_codex_followup tests.test_watcher_core.TurnResolutionTest.test_commit_push_operator_request_dirty_source_stays_operator_turn` -> 4 tests OK
- `python3 -m unittest tests.test_watcher_core` -> 178 tests OK
- `python3 -m unittest tests.test_pipeline_launcher.TestPipelineLauncherSessionContract.test_build_snapshot_localizes_operator_approval_completed_reason` -> 1 test OK
- `python3 -m unittest tests.test_pipeline_gui_home_presenter` -> 18 tests OK
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py` -> 통과
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_commit_push_bundle_authorization_operator_gate_routes_to_triage tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_operator_approval_completed_turn_suppresses_active_operator_control tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_progress_hint_marks_operator_approval_completed` -> 3 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_suppresses_stale_verify_round_during_operator_gated_hibernate_idle` -> 1 test OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` -> 127 tests OK
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/automation_health.py pipeline_runtime/status_labels.py pipeline_runtime/supervisor.py tests/test_operator_request_schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md AGENTS.md CLAUDE.md GEMINI.md PROJECT_CUSTOM_INSTRUCTIONS.md work/README.md verify/README.md` -> 통과
- `python3 -m py_compile watcher_prompt_assembly.py watcher_core.py pipeline_runtime/supervisor.py` -> 통과
- `python3 -m unittest tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_keeps_commit_push_in_verify_owner tests.test_watcher_core.WatcherPromptAssemblyTest.test_blocked_triage_prompt_rejects_commit_push_reissue_to_implement tests.test_watcher_core.WatcherPromptAssemblyTest.test_blocked_triage_spec_carries_raw_event_payload` -> 3 tests OK
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest.test_dirty_commit_push_bundle_authorization_routes_to_codex_followup tests.test_watcher_core.TurnResolutionTest.test_satisfied_commit_push_bundle_authorization_routes_to_codex_followup` -> 2 tests OK
- `python3 -m unittest tests.test_watcher_core.WatcherPromptAssemblyTest.test_operator_retriage_prompt_keeps_commit_push_in_verify_owner tests.test_watcher_core.WatcherPromptAssemblyTest.test_blocked_triage_prompt_rejects_commit_push_reissue_to_implement tests.test_watcher_core.WatcherPromptAssemblyTest.test_blocked_triage_spec_carries_raw_event_payload tests.test_watcher_core.RuntimePlanConsumptionTest.test_prompt_contract_follows_nondefault_role_owners` -> 4 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_verify_prompt_prefers_gemini_before_operator_for_slice_ambiguity tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_followup_prompt_only_uses_operator_after_inconclusive_gemini_advice tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_prompt_templates_follow_role_bound_prompt_owners_when_lanes_exist` -> 3 tests OK
- `python3 -m unittest tests.test_watcher_core` -> 180 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` -> 127 tests OK
- `git diff --check -- watcher_prompt_assembly.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md work/README.md verify/README.md` -> 통과
- live runtime 확인: `.pipeline/logs/experimental/raw.jsonl`에 seq 713 operator gate가 기존 `mode=hibernate`에서 새 watcher restart 후 `mode=triage`, `routed_to=codex_followup`으로 재분류됐고, `verify_operator_retriage_notify`가 기록됐습니다.
- live runtime 확인: verify/handoff owner가 `.pipeline/claude_handoff.md` `CONTROL_SEQ: 714`, `REASON_CODE: commit_push_bundle_authorization` implement handoff를 작성했습니다.
- live runtime 확인: seq 714는 implement lane 규칙과 충돌해 `commit_push_forbidden_by_lane_rules` / `handoff_requires_commit_push_but_rules_forbid_commit_push` sentinel로 되돌아왔습니다. 이 충돌을 기준으로 blocked triage prompt가 같은 commit/push handoff를 implement lane에 다시 발행하지 않도록 회귀 테스트를 추가했습니다.

## 남은 리스크
- 이번 변경은 watcher/supervisor가 commit/push를 직접 shell로 실행하는 기능을 추가하지 않았습니다. 자동화는 "operator 재호출 없이 verify/handoff owner가 auditable publish follow-up handoff를 열도록 라우팅"하는 단계입니다.
- live seq 714 handoff는 prompt 보강 전에 이미 작성된 stale handoff입니다. 이후 watcher prompt 계약은 같은 commit/push 요청을 implement lane에 재발행하지 않도록 바뀌었지만, 실제 commit/push 완료 여부는 이 round에서 확인되지 않았습니다.
- worktree에는 여러 라운드 변경이 섞여 있으므로, seq 714 실행자는 handoff에 적힌 stage 목록과 현재 dirty tree를 다시 대조해야 합니다.
