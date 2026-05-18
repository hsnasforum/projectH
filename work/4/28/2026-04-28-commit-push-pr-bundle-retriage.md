# 2026-04-28 Commit Push PR Bundle Retriage

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `.pipeline/operator_request.md` (runtime control slot, git 미추적)
- `verify/4/28/2026-04-28-commit-push-pr-bundle-retriage.md`
- `work/4/28/2026-04-28-commit-push-pr-bundle-retriage.md`

## 사용 skill
- `onboard-lite`: 현재 RUNNING pipeline status, active control, 관련 runtime entrypoint를 좁게 확인했습니다.
- `security-gate`: commit/push/PR publish follow-up이 operator boundary를 우회하지 않고 verify/handoff-owner 경계로만 흐르는지 확인했습니다.
- `doc-sync`: reason 정규화와 runtime health 계약 변경을 기술설계서/RUNBOOK에 반영했습니다.
- `finalize-lite`: 변경 파일, 검증 범위, 남은 리스크를 마무리 기준으로 확인했습니다.
- `work-log-closeout`: 이번 운영/구현 변경을 `/work` closeout으로 정리했습니다.

## 변경 이유
- 현재 `.pipeline/operator_request.md`의 `REASON_CODE: commit_push_pr_creation_m68_bundle`가 shared reason 정규화에 잡히지 않아 `OPERATOR_POLICY: internal_only`인데도 `hibernate`로 분류되었습니다.
- 그 결과 세 lane이 죽은 것은 아니지만, status가 `operator_request_gated_hibernate`로 머물며 M68 publish follow-up이 진행되지 않았습니다.
- 같은 유형의 ad-hoc publish bundle label이 다시 생겨도 operator stop/hibernate로 빠지지 않게 정규화 규칙과 회귀 테스트가 필요했습니다.

## 핵심 변경
- `normalize_reason_code()`가 `commit_push`와 `pr_creation` 계열 marker를 함께 가진 ad-hoc bundle reason을 `commit_push_bundle_authorization`으로 정규화하도록 보강했습니다.
- 현재 runtime control slot header를 canonical `REASON_CODE: commit_push_bundle_authorization`, `OPERATOR_POLICY: internal_only`, `DECISION_CLASS: release_gate`로 정리해 live watcher가 `VERIFY_FOLLOWUP`으로 재진입하게 했습니다.
- watcher/supervisor/operator schema 테스트에 `commit_push_pr_creation_m68_bundle` 회귀 케이스를 추가했습니다.
- supervisor의 기존 dispatch/completion stall 테스트 기대값을 현재 shared automation-health 계약(`verify_followup`)에 맞춰 정리했습니다.
- 기술설계서와 RUNBOOK에 ad-hoc publish bundle reason 정규화 및 stall follow-up surface를 문서화했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py`
- 통과: `python3 -m unittest -v tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_ad_hoc_commit_push_pr_creation_bundle_routes_to_internal_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_ad_hoc_commit_push_pr_creation_bundle_routes_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_ad_hoc_commit_push_pr_creation_bundle_surfaces_as_triage`
- 통과: `python3 -m unittest -v tests.test_operator_request_schema tests.test_pipeline_runtime_automation_health` (55 tests)
- 통과: `python3 -m unittest -v tests.test_watcher_core` (208 tests)
- 통과: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor` (152 tests)
- 통과: `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/4/28/2026-04-28-commit-push-pr-bundle-retriage.md verify/4/28/2026-04-28-commit-push-pr-bundle-retriage.md`
- 확인: live status가 `runtime_state=RUNNING`, `turn_state=VERIFY_FOLLOWUP`, `automation_reason_code=commit_push_bundle_authorization`, `automation_next_action=verify_followup`, Claude lane `WORKING`으로 전환되었습니다.
- 참고: 초기에 잘못 지정한 unittest 클래스명과 기존 supervisor 테스트 기대값 드리프트로 실패가 있었고, 경로/기대값을 수정한 뒤 위 전체 관련 suite가 통과했습니다.

## 남은 리스크
- `.pipeline/operator_request.md`는 rolling runtime slot이라 git 추적 변경에는 포함되지 않습니다. 현재 실행 상태를 즉시 풀기 위해 header만 canonical 값으로 정리했습니다.
- Claude verify/handoff lane이 현재 M68 commit/push/PR follow-up을 처리 중입니다. merge 실행 자체는 여전히 `pr_merge_gate` operator boundary로 남아야 합니다.
- 전체 repo browser/E2E와 장기 soak는 실행하지 않았습니다. 이번 변경은 pipeline runtime control 분류와 status surface에 한정했습니다.
