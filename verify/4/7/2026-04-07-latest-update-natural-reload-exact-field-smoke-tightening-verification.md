## 변경 파일
- `verify/4/7/2026-04-07-latest-update-natural-reload-exact-field-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/7/2026-04-07-latest-update-natural-reload-exact-field-smoke-tightening.md`의 주장이 현재 트리와 focused rerun 기준으로 truthful한지 다시 확인하고, 같은 `latest-update natural-reload` family에서 다음 단일 current-risk reduction slice를 좁히기 위해서입니다.
- 이번 라운드는 새 구현이 아니라 verification-backed handoff이므로, 직전 라운드의 service/browser/docs 반영과 실제 재실행 결과를 다시 맞춘 뒤, same-family 안에서 실제로 깨진 경로를 다음 슬라이스로 확정해야 했습니다.

## 핵심 변경
- 최신 `/work`가 적은 구현 범위를 다시 확인했습니다. `tests/test_web_app.py`의 mixed/single/news-only latest-update natural-reload exact-field service test 3개, `e2e/tests/web-smoke.spec.mjs`의 scenario 57/58/59, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`의 scenario count `59` 및 checklist sync가 현재 트리와 일치했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_mixed_source_latest_update_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_single_source_latest_update_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_news_only_latest_update_reload_exact_fields` 재실행 결과 `Ran 3 tests in 0.065s`, `OK`였습니다.
- Playwright isolated rerun 3건도 다시 통과했습니다.
  - scenario 57 mixed-source natural reload: `1 passed (7.4s)`
  - scenario 58 single-source natural reload: `1 passed (8.1s)`
  - scenario 59 news-only natural reload: `1 passed (7.3s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`는 clean이었습니다.
- 추가 service direct probe에서는 자연어 reload 뒤 follow-up chain의 현재 runtime truth를 다시 확인했습니다.
  - mixed-source는 initial natural reload 직후에는 정상이지만, 그 뒤 first follow-up과 second follow-up에서 둘 다 `verification_label='단일 출처 참고'`, `source_roles=['보조 기사']`, `source_paths=['https://www.yna.co.kr/view/AKR20260401000100017']`로 드리프트했습니다. 즉 `공식+기사 교차 확인`, `['보조 기사', '공식 기반']`, `store.steampowered.com`가 사라졌습니다.
  - single-source는 follow-up과 second follow-up 모두 `단일 출처 참고`, `['보조 출처']`, `example.com/seoul-weather`를 유지했습니다.
  - news-only는 follow-up과 second follow-up 모두 `기사 교차 확인`, `['보조 기사']`, `hankyung.com` + `mk.co.kr`를 유지했습니다.
- natural-reload follow-up chain에 대한 explicit contract는 아직 없습니다. `rg -n "latest-update mixed-source 자연어 reload 후 follow-up|latest-update single-source 자연어 reload 후 follow-up|latest-update news-only 자연어 reload 후 follow-up|latest-update mixed-source 자연어 reload 후 두 번째|latest_update.*natural.*follow_up|mixed_source.*natural.*follow_up|single_source.*natural.*follow_up|news_only.*natural.*follow_up" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`는 매치 없이 종료됐습니다.
- 그래서 다음 Claude 실행 슬라이스를 `latest-update mixed-source natural-reload follow-up chain continuity tightening`으로 좁혀 `.pipeline/claude_handoff.md`를 갱신했습니다. initial natural-reload exact-field 3갈래는 이미 닫혔고, same-family current-risk reduction으로는 실제 드리프트가 확인된 mixed-source follow-up chain이 가장 우선입니다. single/news natural-reload follow-up chain은 direct probe상 안정적이지만 explicit contract 부재만 남아 있으므로, 깨진 mixed-source를 먼저 닫는 편이 truthful합니다.

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_mixed_source_latest_update_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_single_source_latest_update_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_news_only_latest_update_reload_exact_fields`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update mixed-source 자연어 reload에서 source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update single-source 자연어 reload에서 source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update news-only 자연어 reload에서 기사 source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `python3 - <<'PY' ... latest-update natural-reload -> first follow-up -> second follow-up direct probe for mixed/single/news_only ... PY`
- `rg -n "latest-update mixed-source 자연어 reload 후 follow-up|latest-update single-source 자연어 reload 후 follow-up|latest-update news-only 자연어 reload 후 follow-up|latest-update mixed-source 자연어 reload 후 두 번째|latest_update.*natural.*follow_up|mixed_source.*natural.*follow_up|single_source.*natural.*follow_up|news_only.*natural.*follow_up" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `git status --short`

## 남은 리스크
- latest-update natural-reload initial exact-field contract는 mixed-source, single-source, news-only 세 branch 모두 truthful하게 닫혔습니다.
- 현재 같은 family의 가장 큰 current risk는 mixed-source natural-reload 후속 질의 체인입니다. initial reload는 정상인데, follow-up부터 `공식 기반`과 공식 URL이 탈락해 단일 출처 수준으로 드리프트합니다.
- single/news natural-reload follow-up chain은 direct probe상 안정적이지만, explicit service/browser/docs contract는 아직 없습니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위가 아니라 재실행하지 않았습니다.
