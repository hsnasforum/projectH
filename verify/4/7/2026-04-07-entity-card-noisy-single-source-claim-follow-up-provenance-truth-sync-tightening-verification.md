## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-follow-up-provenance-truth-sync-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 entity-card noisy single-source claim follow-up provenance truth-sync tightening이 현재 트리와 실제 rerun 결과에 맞는지 다시 확인하고, 같은 family에서 남은 가장 작은 current-risk reduction 슬라이스를 하나로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`에서 `/work`가 주장한 follow-up provenance truth-sync 반영을 재확인했습니다. focused rerun 결과 `unittest 4건`, Playwright scenario `70`, `71`, `72`, `73`, 대상 파일 `git diff --check`가 모두 통과했습니다. 따라서 latest `/work`의 핵심 구현과 검증 주장은 현재 트리와 일치합니다.
- 추가 one-off probe 결과 initial exact reload 경로에서도 current runtime truth는 이미 follow-up chain과 같습니다. history-card click reload와 자연어 reload exact path 모두 `response_origin`이 `WEB` / `entity_card` / `설명형 다중 출처 합의` / `['백과 기반']`를 유지했고, `response.text`에는 `출시일`, `2025`, `blog.example.com`이 다시 나타나지 않았으며, `active_context.source_paths`에는 `namu.wiki`, `ko.wikipedia.org`, `https://blog.example.com/crimson-desert`가 함께 남았습니다.
- 하지만 exact reload contract는 아직 stale하거나 partial합니다. service의 [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9649)와 [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9769)는 initial reload path에서 `blog.example.com` 본문 미노출과 provenance positive assertion을 잠그지 않습니다. browser의 [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1701)는 여전히 `설명형 단일 출처` fixture를 쓰고 context-box provenance를 확인하지 않으며, [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4233)와 [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4346)는 2-source generic fixture만 확인합니다.
- 문서도 같은 family의 initial exact-path truth를 아직 못 따라왔습니다. [`README.md`](/home/xpdlqj/code/projectH/README.md#L134), [`README.md`](/home/xpdlqj/code/projectH/README.md#L152), [`README.md`](/home/xpdlqj/code/projectH/README.md#L158), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1343), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1361), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L52), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L70), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L76), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L41), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L59), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L65), [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)는 follow-up chain보다 한 단계 앞선 reload exact-path에 대해 여전히 older wording 또는 generic wording을 남기고 있습니다.
- 따라서 다음 단일 슬라이스는 `entity-card noisy single-source claim reload exact-field provenance truth-sync tightening`으로 고정했습니다. 목표는 history-card click reload와 자연어 reload exact path에서도 current runtime truth대로 `blog.example.com`이 `context/source_paths`에는 남고 `response.text` / `response_origin detail`에는 나타나지 않으며, verification label이 `설명형 다중 출처 합의`로 유지된다는 점을 explicit service/browser/docs contract로 잠그는 것입니다.

## 검증
- `git status --short`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-follow-up-provenance-truth-sync-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-click-reload-follow-up-chain-exclusion-tightening-verification.md`
- `rg -n "test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up|test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up|test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up|test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up|entity-card noisy single-source claim이 자연어 reload 후 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다|entity-card noisy single-source claim이 자연어 reload 후 두 번째 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다|history-card entity-card noisy single-source claim이 다시 불러오기 후 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다|history-card entity-card noisy single-source claim이 다시 불러오기 후 두 번째 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다|70\\.|71\\.|72\\.|73\\.|blog\\.example\\.com" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `sed -n '17240,17490p' tests/test_web_app.py`
- `sed -n '6160,6455p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '178,190p' README.md`
- `sed -n '1389,1403p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '92,98p' docs/MILESTONES.md`
- `sed -n '86,94p' docs/TASK_BACKLOG.md`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim이 자연어 reload 후 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim이 자연어 reload 후 두 번째 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card noisy single-source claim이 다시 불러오기 후 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card noisy single-source claim이 다시 불러오기 후 두 번째 follow-up에서도 본문과 origin detail에 다시 노출되지 않습니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- one-off python probe: history-card click reload exact path와 자연어 reload exact path의 `response_origin`, `response.text`, `active_context.source_paths` 출력 확인
- `sed -n '9640,9885p' tests/test_web_app.py`
- `sed -n '1688,1835p' e2e/tests/web-smoke.spec.mjs`
- `rg -n '붉은사막|noisy single-source claim|agreement-backed fact card retention|방금 검색한 결과 다시 보여줘.*붉은사막|history-card entity-card 다시 불러오기 후 noisy single-source claim' README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4233,4398p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4398,4465p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1701,1828p'`
- `nl -ba tests/test_web_app.py | sed -n '9649,9878p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '1,40p'`

## 남은 리스크
- follow-up provenance truth-sync family는 now truthful하게 닫혔지만, initial click reload / natural reload exact path는 아직 explicit service/browser/docs contract가 current runtime truth를 끝까지 따라가지 못합니다.
- 특히 history-card click reload browser smoke와 `docs/NEXT_STEPS.md`는 여전히 older wording을 유지하고, natural reload exact-path browser smoke는 noisy provenance가 없는 generic 2-source fixture에 머물러 있습니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 관련 파일만 좁게 건드려야 합니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 재실행하지 않았습니다.
