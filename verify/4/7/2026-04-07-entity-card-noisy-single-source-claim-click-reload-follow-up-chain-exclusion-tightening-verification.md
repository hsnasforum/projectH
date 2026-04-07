## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-click-reload-follow-up-chain-exclusion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 entity-card noisy single-source claim click-reload follow-up chain exclusion tightening이 현재 트리와 실제 rerun 결과에 맞는지 다시 확인하고, 같은 family에서 남은 가장 작은 current-risk reduction 슬라이스를 하나로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`에서 `/work`가 주장한 click-reload follow-up/second-follow-up exclusion contract와 smoke scenario count `73`, backlog `78-79` 반영을 재확인했습니다.
- focused rerun 결과 `unittest 2건`, Playwright scenario `72`, `73`, 대상 파일 `git diff --check`가 모두 통과했습니다. 따라서 latest `/work`의 핵심 구현과 검증 주장은 현재 트리와 일치합니다.
- 다만 이번 라운드에서 추가된 click-reload service test는 `active_context.source_paths`에 `namu.wiki`, `ko.wikipedia.org`만 재확인하고 있으며, browser scenario `72`, `73`도 `#context-box`에서 그 두 URL의 유지까지만 잠급니다. 반면 [`app/static/app.js`](/home/xpdlqj/code/projectH/app/static/app.js#L2401)에서는 `context.source_paths` 전체를 그대로 `#context-box`에 렌더합니다.
- 같은 날 직전 `/verify`인 `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-natural-reload-follow-up-chain-exclusion-tightening-verification.md`의 one-off probe는 natural-reload와 click-reload follow-up/second-follow-up 모두 `active_context.source_paths`에 `https://blog.example.com/crimson-desert`가 남는 current runtime truth를 이미 확인했습니다. 즉 현재 truthful closure는 noisy claim exclusion을 `response.text` / `response_origin detail` 축에 잠근 것이고, noisy provenance URL은 user-visible `#context-box`에 남는 상태입니다.
- 따라서 다음 단일 슬라이스는 `entity-card noisy single-source claim follow-up provenance truth-sync tightening`으로 고정했습니다. 목표는 natural-reload와 history-card click-reload의 first/second follow-up 체인에서 `blog.example.com`이 `context/source_paths`에는 남고, `response.text`와 `response_origin detail`에는 계속 나타나지 않는 현재 truth를 explicit service/browser/docs contract로 잠그는 것입니다.

## 검증
- `git status --short`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-click-reload-follow-up-chain-exclusion-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-natural-reload-follow-up-chain-exclusion-tightening-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `rg -n "test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up|test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up|history-card entity-card noisy single-source claim이 다시 불러오기 후 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다|history-card entity-card noisy single-source claim이 다시 불러오기 후 두 번째 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다|72\\.|73\\.|73 browser scenarios|count 73|scenario 72|scenario 73" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `sed -n '17340,17510p' tests/test_web_app.py`
- `sed -n '6290,6465p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '176,194p' README.md`
- `sed -n '1388,1406p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '44,64p' docs/MILESTONES.md`
- `sed -n '70,95p' docs/TASK_BACKLOG.md`
- `sed -n '1,120p' docs/NEXT_STEPS.md`
- `rg -n 'blog\\.example\\.com|crimson-desert' e2e/tests/web-smoke.spec.mjs tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba app/static/app.js | sed -n '2396,2405p'`
- `nl -ba tests/test_web_app.py | sed -n '17360,17478p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6310,6445p'`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card noisy single-source claim이 다시 불러오기 후 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card noisy single-source claim이 다시 불러오기 후 두 번째 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- entity-card noisy single-source claim follow-up chain exclusion 자체는 natural-reload와 click-reload 모두 truthful하게 닫혔지만, noisy provenance URL `https://blog.example.com/crimson-desert`가 `active_context.source_paths`와 `#context-box`에 남는 current behavior는 아직 dedicated service/browser/docs contract로 고정되어 있지 않습니다.
- 다음 라운드는 runtime/helper 변경 없이 기존 자연어 reload 2건 + click reload 2건의 service/browser assertion과 문서 wording만 tightened 하는 쪽이 가장 안전합니다. 현재 동작과 다를 때만 runtime 수정 여부를 다시 판단해야 합니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 관련 파일만 좁게 건드려야 합니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 재실행하지 않았습니다.
