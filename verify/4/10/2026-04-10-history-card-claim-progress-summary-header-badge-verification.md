# history-card claim-progress summary header-badge verification

## 변경 파일
- `verify/4/10/2026-04-10-history-card-claim-progress-summary-header-badge-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/10/2026-04-10-history-card-claim-progress-summary-surfacing-closeout.md`가 현재 코드와 문서 범위를 truthful하게 설명하는지 다시 확인해야 했습니다.
- 동시에 이전 same-day `/verify` 이후 최신 `/work`가 갱신되었으므로, stale 판단을 그대로 이어가지 않고 현재 truth 기준으로 다음 단일 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work` closeout 자체는 현재 truthful합니다.
  - `storage/web_search_store.py`는 `list_session_record_summaries`에서 `claim_coverage_progress_summary`를 summary payload에 포함합니다.
  - `app/serializers.py`는 `session.web_search_history[*]` 직렬화에 같은 필드를 포함합니다.
  - `app/static/app.js`는 history-card meta에서 non-empty progress summary를 detail line으로 렌더링합니다.
  - focused unit 2건과 exact Playwright 1시나리오를 이번 라운드에서 다시 실행했고 모두 통과했습니다.
- 다만 same-family smoke coverage 설명에는 새 drift가 있습니다.
  - `README.md:138`과 `docs/ACCEPTANCE_CRITERIA.md:1366`는 "web-search history card header badges" 시나리오가 non-empty `claim_coverage_progress_summary` 표시까지 검증한다고 적습니다.
  - 실제 `e2e/tests/web-smoke.spec.mjs:1102-1175`의 해당 시나리오는 `claim_coverage_progress_summary` fixture를 넣지 않고, progress summary assertion도 하지 않습니다.
  - progress summary 가시성 검증은 현재 `e2e/tests/web-smoke.spec.mjs:1200`의 entity-card reload 시나리오에만 들어 있습니다.
- 따라서 `CONTROL_SEQ: 16`의 가장 작은 truthful next slice는 새 product behavior 추가가 아니라, generic header-badge smoke contract를 docs가 이미 설명하는 범위까지 실제 테스트에 맞추는 same-family current-risk reduction입니다.
- 이번 verify round에서 실행한 검증과 생략한 검증을 분리했습니다.
  - rerun 완료: focused unit 2건, exact Playwright 1시나리오, 대상 파일 `git diff --check`
  - rerun하지 않음: `python3 -m unittest -v tests.test_web_app` 전체 suite, `history-card entity-card` 13-scenario family, full Playwright suite, `make e2e-test`

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_progress_summary tests.test_web_app.WebAppServiceTest.test_web_search_history_serializer_includes_claim_coverage_progress_summary`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 클릭 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 유지됩니다" --reporter=line`
- `git diff --check -- storage/web_search_store.py app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/10/2026-04-10-history-card-claim-progress-summary-surfacing-closeout.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1100,1195p'`
- `nl -ba README.md | sed -n '134,141p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1362,1368p'`

## 남은 리스크
- 현재 shipped UI는 progress summary를 generic history-card detail line에 렌더링하지만, header-badge smoke scenario는 그 계약을 아직 직접 잠그지 못합니다.
- README/acceptance의 scenario wording이 현재 test보다 앞서 있기 때문에, 다음 라운드가 이 drift를 닫지 않으면 smoke coverage truth가 다시 흔들립니다.
- 이번 라운드는 narrow rerun만 다시 실행했으므로 broader browser family drift나 전체 `tests.test_web_app` 재통과까지는 독립적으로 재확인하지 않았습니다.
