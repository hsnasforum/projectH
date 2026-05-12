# 2026-04-29 Publish Bundle — M84 doc-sync + stale advisory cancel guard

## 변경 파일

### PR #71 — fix/stale-advisory-cancel-guard (base: feat/m83-promote-result-ui)
커밋 1 (`f3661f4`): stale cancel guard + runtime docs
- `watcher_core.py`
- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

커밋 2 (`4dea8af`): operator_autonomy 정규화 fix
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`

### PR #72 — feat/m84-doc-sync-m81-m83 (base: feat/m83-promote-result-ui)
커밋 (`4f4677b`): M84 doc-sync
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- `security-gate`: runtime control, shell/git permission prompt, publish boundary 변경의 승인/감사 경계를 확인했다.
- `github:yeet`: local branch commit/push/PR publish 흐름과 scope 확인 기준을 적용했다.
- `doc-sync`: runtime 정규화/guard 동작을 `.pipeline/README.md`와 runtime docs에 맞췄다.
- `finalize-lite`: 실행한 검증, doc-sync, `/work` closeout 준비 상태를 확인했다.
- `work-log-closeout`: 이번 publish closeout note를 정리했다.

## 실행 결과

| 단계 | 결과 |
|------|------|
| `fix/stale-advisory-cancel-guard` 브랜치 생성 + 커밋 | ✓ |
| `feat/m84-doc-sync-m81-m83` 브랜치 생성 + 커밋 | ✓ |
| `git push origin fix/stale-advisory-cancel-guard` | ✓ |
| `git push origin feat/m84-doc-sync-m81-m83` | ✓ |
| PR #71 생성 (fix/stale-advisory-cancel-guard → feat/m83-promote-result-ui) | ✓ https://github.com/hsnasforum/projectH/pull/71 |
| PR #72 생성 (feat/m84-doc-sync-m81-m83 → feat/m83-promote-result-ui) | ✓ https://github.com/hsnasforum/projectH/pull/72 |
| PR #71/#72 draft 변환 | ✓ |
| PR #71 body 검증 내역 정정 | ✓ |

## operator_autonomy 정규화 배경

operator_request 1305에서 비표준 `REASON_CODE: m84_publish_bundle_authorization`,
`DECISION_CLASS: publish_authorization`을 사용했고 runtime 정규화 규칙이 없었다.
이번 commit (`4dea8af`)으로:
- `m*_publish_bundle_authorization` → `COMMIT_PUSH_BUNDLE_AUTHORIZATION_REASON`
- `publish_authorization` / `publish_bundle_authorization` → `release_gate`
규칙을 추가해 동일 패턴이 앞으로 자동으로 `verify_followup` (triage)로 라우팅된다.

## PR 스택 전체 상태

```
PR #62(M76) ← … ← PR #69(M83) ← PR #71(fix) ← main으로 retarget 대기
                               ← PR #72(M84 docs) ← main으로 retarget 대기
```

머지 순서: PR #62→…→#69 먼저, 이후 #71·#72 retarget 후 머지.
→ operator 결정 대기.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py watcher_dispatch.py` — PASS.
- `python3 -m unittest -v tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_milestone_publish_bundle_authorization_routes_to_internal_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_milestone_publish_bundle_authorization_surfaces_as_triage` — 2 tests OK.
- `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovery_cancels_busy_advisory_lane tests.test_watcher_core.BusyLaneNotificationDeferTest.test_inactive_advisory_lane_cancel_sends_escape_after_grace tests.test_watcher_core.BusyLaneNotificationDeferTest.test_inactive_advisory_lane_cancel_skips_current_active_advisory tests.test_watcher_core.CodexDispatchConfirmationTest.test_gemini_git_permission_prompt_requires_readonly_git_command tests.test_watcher_core.CodexDispatchConfirmationTest.test_gemini_git_permission_prompt_rejects_mutating_git_command tests.test_watcher_core.CodexDispatchConfirmationTest.test_answer_gemini_git_permission_prompt_selects_session_allow tests.test_watcher_core.CodexDispatchConfirmationTest.test_watcher_poll_answers_gemini_git_permission_prompt_before_startup_grace` — 7 tests OK.
- `python3 -m unittest -v tests.test_operator_request_schema tests.test_pipeline_runtime_automation_health` — 56 tests OK.
- `python3 -m unittest -v tests.test_watcher_core` — 215 tests OK.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_milestone_publish_bundle_authorization_surfaces_as_triage tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_normalizes_milestone_publish_bundle_authorization_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_normalizes_m21_publish_bundle_stop_to_verify_followup` — 3 tests OK.
- `git diff --check -- pipeline_runtime/operator_autonomy.py watcher_core.py watcher_dispatch.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — PASS.
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` — PASS.

## 남은 리스크

- PR 머지는 operator 결정 대기.
- tracked diff는 비어 있지만, 기존부터 누적된 untracked `work/`, `verify/`, `report/gemini/` 로컬 기록은 남아 있다.
- M85 이후 방향은 advisory에서 결정.
