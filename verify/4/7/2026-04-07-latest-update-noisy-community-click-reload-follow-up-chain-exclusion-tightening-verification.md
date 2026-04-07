## 변경 파일
- `verify/4/7/2026-04-07-latest-update-noisy-community-click-reload-follow-up-chain-exclusion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 latest-update noisy-community click-reload follow-up chain tightening이 현재 트리와 실제 rerun 결과에 맞는지 다시 확인하고, same-family risk가 사실상 닫힌 뒤 남는 다음 한 슬라이스를 current tree 기준으로 하나로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`에서 `/work`가 주장한 click-reload follow-up/second-follow-up noisy-community exclusion contract와 smoke scenario count `69` 반영을 재확인했습니다.
- focused rerun 결과 `unittest 2건`, Playwright scenario `68`, `69`, 대상 파일 `git diff --check`가 모두 통과했습니다.
- same-day 이전 `/verify`가 noisy-community natural-reload follow-up chain을 truth-sync했고, 이번 라운드가 click-reload follow-up chain을 truth-sync했으므로 latest-update noisy-community exclusion family는 현재 scope에서 truthful하게 닫혔습니다.
- 다음 same-family current-risk reduction 후보를 다시 찾으면, entity-card noisy single-source claim은 exact noisy natural-reload exclusion contract와 자연어 reload follow-up continuity contract는 이미 있으나, 같은 자연어 reload follow-up/second-follow-up 체인에서 `출시일` / `2025` / noisy single-source claim이 다시 노출되지 않는 dedicated negative contract는 아직 없습니다.
- 따라서 다음 단일 슬라이스는 `entity-card noisy single-source claim natural-reload follow-up chain exclusion tightening`으로 고정했습니다. click-reload variant보다 natural-reload를 먼저 고른 이유는 exact noisy exclusion과 follow-up continuity 뼈대가 이미 service/browser/docs에 있어서, 이번에는 negative assertion tightening만 추가하면 되는 더 작은 same-family risk reduction이기 때문입니다.

## 검증
- `git status --short`
- `rg -n "test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up|test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up|scenario 68|scenario 69|69 browser scenarios|count 69|68\\.|69\\.|history-card latest-update noisy community source가 다시 불러오기 후 follow-up|history-card latest-update noisy community source가 다시 불러오기 후 두 번째 follow-up" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `sed -n '17160,17360p' tests/test_web_app.py`
- `sed -n '6000,6165p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '174,186p' README.md`
- `sed -n '1382,1398p' docs/ACCEPTANCE_CRITERIA.md`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update noisy community source가 다시 불러오기 후 follow-up에서도 origin detail과 본문에 다시 노출되지 않습니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update noisy community source가 다시 불러오기 후 두 번째 follow-up에서도 origin detail과 본문에 다시 노출되지 않습니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `rg -n "test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload|test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload|history-card entity-card 다시 불러오기 후 noisy single-source claim이 본문과 origin detail에 노출되지 않습니다|방금 검색한 결과 다시 보여줘.*출시일|entity-card.*noisy.*follow_up|entity-card.*noisy.*follow-up|noisy single-source claim.*follow-up" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `rg -n "붉은사막.*follow-up.*response origin|entity-card 붉은사막.*follow-up|test_handle_chat_entity_card_.*crimson|붉은사막.*follow_up|붉은사막.*두 번째 follow-up" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `sed -n '9630,9895p' tests/test_web_app.py`
- `sed -n '4740,4925p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '16080,16270p' tests/test_web_app.py`
- `sed -n '5030,5158p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '5120,5198p' e2e/tests/web-smoke.spec.mjs`
- `rg -n "entity-card 붉은사막 자연어 reload 후 follow-up.*출시일|entity-card 붉은사막 자연어 reload 후 두 번째 follow-up.*출시일|test_handle_chat_.*natural.*follow.*출시일|test_handle_chat_.*natural.*second.*출시일|붉은사막.*방금 검색한 결과 다시 보여줘.*출시일" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- latest-update noisy-community exclusion family는 현재 scope에서 닫혔지만, entity-card noisy single-source claim의 자연어 reload follow-up/second-follow-up negative contract는 아직 dedicated coverage가 없습니다.
- click-reload variant의 entity-card noisy single-source claim follow-up chain도 이후 same-family 후보로 남아 있습니다. 다만 현재 트리 기준으로는 natural-reload 쪽이 exact noisy exclusion + continuity anchor를 이미 갖고 있어 더 작은 다음 슬라이스입니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 관련 파일만 좁게 건드려야 합니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 재실행하지 않았습니다.
