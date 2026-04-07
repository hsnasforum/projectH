## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-natural-reload-follow-up-chain-exclusion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 entity-card noisy single-source claim natural-reload follow-up chain tightening이 현재 트리와 실제 rerun 결과에 맞는지 다시 확인하고, same-family에서 남은 가장 작은 current-risk reduction 슬라이스를 하나로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`에서 `/work`가 주장한 entity-card noisy single-source natural-reload follow-up/second-follow-up exclusion contract와 smoke scenario count `71` 반영을 재확인했습니다.
- focused rerun 결과 `unittest 2건`, Playwright scenario `70`, `71`, 대상 파일 `git diff --check`가 모두 통과했습니다.
- one-off probe 결과 natural-reload follow-up/second-follow-up과 click-reload follow-up/second-follow-up 모두 현재 runtime에서는 `response_origin`이 `WEB` / `entity_card` / `설명형 다중 출처 합의` / `['백과 기반']`를 유지하고, 본문에는 `출시일`, `2025`가 다시 노출되지 않았습니다.
- 같은 probe에서 `active_context.source_paths`는 natural-reload와 click-reload 모두 `https://blog.example.com/crimson-desert`를 provenance 용도로 계속 포함했습니다. 즉 이번 라운드의 truthful closure는 noisy exclusion을 `본문` / `origin detail` / `source_roles` 축에 잠근 것이고, source-path 자체를 제거한 것은 아닙니다.
- 따라서 다음 단일 슬라이스는 `entity-card noisy single-source claim click-reload follow-up chain exclusion tightening`으로 고정했습니다. current runtime 동작은 이미 안정적이지만, history-card click-reload 뒤 first/second follow-up에서 이를 explicit negative contract로 잠근 dedicated service/browser/docs contract는 아직 없습니다.

## 검증
- `git status --short`
- `rg -n "test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up|test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up|scenario 70|scenario 71|71 browser scenarios|count 71|70\\.|71\\.|entity-card noisy single-source claim이 자연어 reload 후 follow-up|entity-card noisy single-source claim이 자연어 reload 후 두 번째 follow-up" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `sed -n '17300,17540p' tests/test_web_app.py`
- `sed -n '6160,6345p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '178,190p' README.md`
- `sed -n '1386,1404p' docs/ACCEPTANCE_CRITERIA.md`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim이 자연어 reload 후 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim이 자연어 reload 후 두 번째 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `rg -n "history-card entity-card .*noisy single-source claim.*follow-up|history-card entity-card .*noisy single-source claim.*두 번째 follow-up|entity-card.*reload.*follow-up.*출시일|test_handle_chat_entity_card_.*history_card_reload.*follow_up.*claim|test_handle_chat_entity_card_.*reload.*second_follow.*claim|blog.example.com.*follow-up" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `rg -n "test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths|test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin|test_handle_chat_entity_card_actual_search_second_follow_up|test_handle_chat_entity_card_dual_probe_follow_up_preserves_source_paths|test_handle_chat_entity_card_.*reload.*follow_up|test_handle_chat_entity_card_.*second_follow_up.*reload" tests/test_web_app.py`
- `rg -n "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다|history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path가 context box에 유지됩니다|history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe response origin badge와 answer-mode badge가 drift하지 않습니다|history-card entity-card 다시 불러오기 후 noisy single-source claim이 본문과 origin detail에 노출되지 않습니다" e2e/tests/web-smoke.spec.mjs`
- one-off python probe: entity-card noisy single-source natural-reload follow-up path의 `active_context.source_paths`와 `response_origin` 출력 확인
- one-off python probe: entity-card noisy single-source click-reload follow-up/second-follow-up path의 `active_context.source_paths`와 `response_origin` 출력 확인

## 남은 리스크
- entity-card noisy single-source claim natural-reload follow-up chain은 `본문` / `origin detail` / `source_roles` 기준으로 now truthful하게 닫혔지만, `active_context.source_paths`에는 noisy provenance URL이 계속 남습니다.
- history-card click-reload 뒤 first/second follow-up에서 같은 noisy exclusion을 explicit하게 잠그는 dedicated service/browser/docs contract는 아직 없습니다. 다만 one-off probe상 현재 동작 자체는 안정적이었습니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 관련 파일만 좁게 건드려야 합니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 재실행하지 않았습니다.
