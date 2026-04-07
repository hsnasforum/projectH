## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-reload-exact-field-provenance-truth-sync-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `entity-card noisy single-source claim reload exact-field provenance truth-sync tightening` 주장이 현재 트리와 focused rerun 결과에 맞는지 다시 확인하고, 같은 family에서 실제로 남은 가장 작은 current-risk reduction 슬라이스를 하나로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- 최신 `/work`가 말한 핵심 변경 중 service initial reload exact-path truth-sync는 현재 트리와 일치했습니다. [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9764)와 [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9886)에서 `response.text`의 `출시일` / `2025` / `blog.example.com` 미노출, `response_origin`의 `WEB` / `entity_card` / `설명형 다중 출처 합의` / `백과 기반`, 그리고 `active_context.source_paths`의 `blog.example.com` provenance 유지가 모두 explicit assertion으로 잠겨 있습니다.
- history-card click-reload browser/docs truth-sync도 현재 트리와 일치했습니다. [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1701)는 `설명형 다중 출처 합의`, agreement-backed 사실 카드 유지, 본문과 origin detail에서의 noisy claim exclusion, `#context-box`의 `blog.example.com` provenance를 함께 확인하고, [`README.md`](/home/xpdlqj/code/projectH/README.md#L134)와 [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1343)도 그 truth에 맞춰 갱신돼 있습니다.
- focused rerun 결과도 latest `/work`가 적은 범위 자체는 통과했습니다. `unittest` 2건, Playwright 3건, 대상 파일 `git diff --check`가 모두 통과했습니다. 다만 이 통과는 natural-reload exact-path까지 noisy provenance truth-sync가 닫혔다는 뜻은 아니었습니다.
- 실제 남은 갭은 natural-reload browser/docs입니다. [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4242)는 여전히 `result_count: 2`의 generic fixture로 `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반`만 확인하고, noisy claim negative assertion이나 `blog.example.com` provenance를 다루지 않습니다. [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4355)는 더 직접적으로 stale하며, generic 2-source fixture에 아직 `설명형 단일 출처`를 심어 둔 채 [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4390) [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4420), context box에서도 `namu.wiki` / `ko.wikipedia.org`만 확인합니다.
- 문서도 같은 half에서 generic 또는 stale 상태입니다. [`README.md`](/home/xpdlqj/code/projectH/README.md#L152)와 [`README.md`](/home/xpdlqj/code/projectH/README.md#L158), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1361)와 [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367)는 natural-reload exact-path를 아직 generic retention / plurality wording으로만 설명합니다. [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L70) [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L76), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L59) [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L65), [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)도 same-family current truth를 아직 반영하지 못했습니다.
- 따라서 latest `/work`는 "reload exact-field provenance truth-sync" family 전체를 닫았다고 보기에는 과장되어 있습니다. 이번 검증 라운드에서는 truth를 `service initial reload exact-path + history-card click-reload browser/docs`까지로 정리했고, 다음 단일 슬라이스를 `entity-card noisy single-source claim natural-reload exact-field provenance truth-sync completion`으로 고정했습니다. 목표는 natural-reload exact path에서도 `blog.example.com`이 `context/source_paths`에는 남고 `response.text` / `response_origin detail`에는 나타나지 않으며 verification label이 `설명형 다중 출처 합의`로 유지된다는 점을 browser/docs contract로 끝까지 맞추는 것입니다.

## 검증
- `git status --short`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-reload-exact-field-provenance-truth-sync-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-follow-up-provenance-truth-sync-tightening-verification.md`
- `rg -n "test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload|test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload|history-card entity-card 다시 불러오기 후 noisy single-source claim이 본문과 origin detail에 노출되지 않습니다|entity-card 붉은사막 검색 결과 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다|entity-card 붉은사막 자연어 reload에서 source path가 context box에 유지됩니다|22\\.|설명형 다중 출처 합의|blog\\.example\\.com" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '9645,9885p' tests/test_web_app.py`
- `sed -n '1701,1835p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '4233,4465p' e2e/tests/web-smoke.spec.mjs`
- `sed -n '132,160p' README.md`
- `sed -n '1340,1369p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '68,78p' docs/MILESTONES.md`
- `sed -n '40,66p' docs/TASK_BACKLOG.md`
- `sed -n '14,18p' docs/NEXT_STEPS.md`
- `nl -ba tests/test_web_app.py | sed -n '9760,9920p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1701,1838p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4240,4445p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4445,4475p'`
- `nl -ba README.md | sed -n '132,160p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1340,1372p'`
- `nl -ba docs/MILESTONES.md | sed -n '68,80p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '40,66p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '1,24p'`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 noisy single-source claim이 본문과 origin detail에 노출되지 않습니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 검색 결과 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload에서 source path가 context box에 유지됩니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- natural-reload exact-path browser smoke 2건은 현재도 통과하지만, one은 generic 2-source exact-field 수준에 머물고 다른 one은 `설명형 단일 출처`까지 남아 있어서 noisy provenance truth-sync를 닫았다고 보기 어렵습니다.
- docs의 same-family anchors 중 `README` / `ACCEPTANCE` natural-reload 항목과 `MILESTONES` / `TASK_BACKLOG` / `NEXT_STEPS`는 아직 stale 또는 generic wording 상태입니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 관련 파일만 좁게 건드려야 합니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 재실행하지 않았습니다.
