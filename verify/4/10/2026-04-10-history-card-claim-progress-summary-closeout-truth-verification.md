# history-card claim-progress summary closeout truth verification

## 변경 파일
- `verify/4/10/2026-04-10-history-card-claim-progress-summary-closeout-truth-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/10/2026-04-10-history-card-claim-progress-summary-surfacing-closeout.md`가 현재 코드/커밋 상태를 truthfully 설명하는지 다시 확인해야 했습니다.
- 동시에 이전 same-day `/work`와 실제 커밋 이력을 대조해, 다음 Claude 라운드가 새 기능으로 넘어가도 되는지 아니면 persistent closeout truth부터 바로잡아야 하는지 좁혀야 했습니다.

## 핵심 변경
- 기능 자체는 현재 shipped truth로 확인되었습니다.
  - `storage/web_search_store.py:317`에서 `list_session_record_summaries`가 `claim_coverage_progress_summary`를 포함합니다.
  - `app/serializers.py:285`에서 `web_search_history` 직렬화가 해당 필드를 노출합니다.
  - `app/static/app.js:2962`에서 history-card meta가 non-empty progress summary를 표시합니다.
  - focused unit regression 2건과 history-card entity-card Playwright family가 현재 통과합니다.
- 하지만 최신 `/work` closeout은 fully truthful하지 않습니다.
  - `work/4/10/2026-04-10-history-card-claim-progress-summary-surfacing-closeout.md`는 `storage/web_search_store.py`를 `## 변경 파일`과 `## 핵심 변경`에서 누락합니다.
  - 같은 note는 "seq13 핸드오프 이후 dirty tree에 이미 구현·테스트·docs가 들어와 있었으나 `/work` closeout이 없어 canonical truth가 닫히지 않은 상태"라고 적지만, 더 이른 same-day `/work`인 `work/4/10/2026-04-10-history-card-claim-coverage-progress-summary-surfacing.md`가 이미 존재하고, 기능 파일들은 현재 clean/committed 상태입니다.
  - 커밋 `21b756f`(`feat: surface claim_coverage_progress_summary on history cards`)의 실제 diff/stat도 `storage/web_search_store.py`를 포함합니다.
- 따라서 seq15의 가장 작은 truthful next slice는 새 product behavior나 추가 smoke tightening이 아니라, 최신 `/work` closeout을 실제 shipped bundle에 맞게 in-place truth-sync하는 것입니다.
- 이번 verify round에서는 narrowest relevant rerun만 다시 실행했습니다.
  - rerun 완료: targeted unit regression 2건, isolated Playwright history-card entity-card family, `git diff --check`
  - rerun하지 않음: `python3 -m unittest -v tests.test_web_app` 전체 228-test suite

## 검증
- `git status --short -- app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --cached -- app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git log --oneline -n 3 -- app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git show --stat --summary 21b756f`
- `git show --unified=20 21b756f -- storage/web_search_store.py`
- `git diff --no-index -- work/4/10/2026-04-10-history-card-claim-coverage-progress-summary-surfacing.md work/4/10/2026-04-10-history-card-claim-progress-summary-surfacing-closeout.md`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_progress_summary tests.test_web_app.WebAppServiceTest.test_web_search_history_serializer_includes_claim_coverage_progress_summary`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card" --reporter=line`
- `git diff --check`

## 남은 리스크
- 최신 `/work`를 그대로 두면 다음 자동 handoff가 `storage/web_search_store.py` 경로와 이미 닫힌 same-day closeout 존재를 놓친 채 시작될 수 있습니다.
- 이번 verify round는 narrow rerun만 다시 실행했으므로, 최신 closeout이 주장한 full `tests.test_web_app` 재실행 자체를 독립적으로 재확인한 것은 아닙니다.
