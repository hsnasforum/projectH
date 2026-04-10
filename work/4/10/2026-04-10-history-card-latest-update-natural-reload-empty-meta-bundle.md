# history-card latest-update natural-reload empty-meta bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 latest-update 자연어 reload follow-up 여섯 서비스 회귀에 history-entry empty-meta continuity 어서션을 in-place 추가 (기존 response-origin/source-path 어서션은 그대로 유지):
  - `test_handle_chat_latest_update_mixed_source_natural_reload_follow_up_preserves_response_origin_and_source_paths`
  - `test_handle_chat_latest_update_mixed_source_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`
  - `test_handle_chat_latest_update_single_source_natural_reload_follow_up_preserves_response_origin_and_source_paths`
  - `test_handle_chat_latest_update_single_source_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`
  - `test_handle_chat_latest_update_news_only_natural_reload_follow_up_preserves_response_origin_and_source_paths`
  - `test_handle_chat_latest_update_news_only_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`
  - 여섯 회귀 모두 마지막 follow-up 응답(shallow 는 `third`, second-follow-up 는 `fourth`) 에서 `session.web_search_history` 의 해당 record 항목이 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 0}`, 빈 `claim_coverage_progress_summary` 를 유지하는지 확인
- `e2e/tests/web-smoke.spec.mjs` — 기존 latest-update 자연어 reload follow-up 여섯 브라우저 시나리오에 history-card empty-meta no-leak 어서션을 in-place 추가 (기존 badge/origin/source-path 어서션은 그대로 유지):
  - `latest-update mixed-source 자연어 reload 후 follow-up에서 ...`
  - `latest-update mixed-source 자연어 reload 후 두 번째 follow-up에서 ...`
  - `latest-update single-source 자연어 reload 후 follow-up에서 ...`
  - `latest-update single-source 자연어 reload 후 두 번째 follow-up에서 ...`
  - `latest-update news-only 자연어 reload 후 follow-up에서 ...`
  - `latest-update news-only 자연어 reload 후 두 번째 follow-up에서 ...`
  - 여섯 시나리오 모두 마지막 follow-up 이후 기존 origin/context-box 어서션 다음에 `historyCard.locator(".meta") toHaveCount(0)` 과 `historyCard not.toContainText("사실 검증")` 두 줄을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-latest-update-non-noisy-reload-follow-up-empty-meta-bundle.md`) 와 그 `/verify` 는 latest-update non-noisy **click-reload** follow-up 분기의 empty-meta no-leak 가족을 잠갔고, 같은 라운드의 검증 단계에서 다음 현재 위험으로 latest-update **자연어 reload** follow-up / second-follow-up 분기에 동일한 empty-meta no-leak 계약이 여전히 잠기지 않았음을 관찰함
- `storage/web_search_store.py:316-317` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 에 의해 latest-update 자연어 reload 런타임도 동일하게:
  - history entry 가 zero-count `claim_coverage_summary` 를 serialize 함
  - `claim_coverage_progress_summary` 가 빈 문자열로 유지됨
  - investigation 카드는 detailLines 에서 answer-mode label 을 skip 함
  - 결과적으로 history card 는 `.meta` detail node 를 생성하지 않아야 함
- 기존 서비스 회귀 여섯 개(`:18282`, `:18333`, `:18387`, `:18429`, `:18473`, `:18522`) 는 response-origin/source-path continuity 만 잠갔고, 기존 브라우저 시나리오 여섯 개(`:7281`, `:7346`, `:7415`, `:7476`, `:7541`, `:7605`) 는 badge/source-path continuity 만 잠가 empty-meta no-leak 계약을 직접 exercise 하지 않음
- 이 슬라이스는 런타임 변경 없이 여섯 서비스 회귀와 여섯 browser 시나리오에 empty-meta assertion block 을 in-place 추가해 "history card has no `.meta` detail node and leaks no `사실 검증` content for this branch" 라는 current shipped contract 를 자연어 reload 경로에도 명시적으로 잠그는 범위임. plain show-only latest-update reload / click-reload latest-update (직전 라운드 완료) / entity-card / actual-search / dual-probe / zero-strong / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` 여섯 서비스 회귀 in-place tighten**
   - 세 개 shallow (`_natural_reload_follow_up_preserves_response_origin_and_source_paths`) 테스트는 세 번째 `handle_chat` (`third`) 응답 단계에서 추가 assertion block 을 삽입
   - 세 개 second-follow-up (`_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`) 테스트는 네 번째 `handle_chat` (`fourth`) 응답 단계에서 동일 assertion block 을 삽입
   - 공통 assertion pattern (직전 click-reload 라운드와 동일):
     - `history_entry = next((item for item in ...["session"]["web_search_history"] if item.get("record_id") == record_id), None)`
     - `self.assertIsNotNone(history_entry)`
     - `self.assertEqual(history_entry.get("claim_coverage_summary") or {}, {"strong": 0, "weak": 0, "missing": 0})`
     - `self.assertEqual(str(history_entry.get("claim_coverage_progress_summary") or ""), "")`
   - 기존 response-origin / source-path / verification-label 어서션은 전부 그대로 유지. `_FakeWebSearchTool` / `AppSettings` / `WebAppService` fixture 는 재사용, 신규 helper/import/fixture 파일은 추가하지 않음
2. **`e2e/tests/web-smoke.spec.mjs` 여섯 browser 시나리오 in-place tighten**
   - 여섯 시나리오 모두 마지막 follow-up 이후 기존 origin/context-box 어서션 다음에 다음 두 줄을 추가:
     ```
     const historyCard = historyBox.locator(".history-item").first();
     await expect(historyCard.locator(".meta")).toHaveCount(0);
     await expect(historyCard).not.toContainText("사실 검증");
     ```
   - `toHaveCount(0)` 은 investigation empty branch 에서 detail `.meta` 가 전혀 생성되지 않음을 잠금. `app/static/app.js:2939-2943` 의 header timestamp `<span>` 은 className 이 없는 raw span 이므로 `.meta` CSS selector 에 매칭되지 않아 false positive 없음 (직전 click-reload 라운드에서 이미 검증됨)
   - `not.toContainText("사실 검증")` 은 accidental `.meta` creation 으로 count line 이 leak 되면 `사실 검증 ...` 접두어가 전체 카드 텍스트에 등장할 텐데 그 leak 자체를 막는 double-guard. 카드의 header/badge/summary 영역에는 `사실 검증` 문자열이 등장하지 않으므로 false positive 없음
   - handoff 지시에 따라 `not.toContainText("최신 확인")` / `not.toContainText("기사 교차 확인")` blanket rule 은 **사용하지 않음** — 이 두 문자열은 각각 `.answer-mode-badge` 와 `.verification-badge` DOM 에 정상적으로 등장하므로 전체 카드에 대한 blanket 부정이 false negative 가 됨. `.meta toHaveCount(0)` 이 accidental `.meta` 생성 자체를 원천 차단하므로 future drift 가 detailMeta 에 `최신 확인` 이나 `기사 교차 확인` 을 담으면 count 가 0 이 아니게 되어 바로 실패함
   - 기존 `WEB` badge / `최신 확인` answer-mode badge / origin detail verification-label & source-roles / `#context-box` source-path 어서션은 전부 그대로 유지
   - 여섯 시나리오 모두 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - click-reload latest-update 시나리오(직전 라운드 완료), plain show-only reload 시나리오, entity-card / actual-search / dual-probe / zero-strong / general / non-latest-update 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_natural_reload_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_natural_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_natural_reload_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_natural_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_natural_reload_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` → 여섯 테스트 모두 `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update (mixed-source|single-source|news-only) 자연어 reload 후 follow-up" --reporter=line` → `3 passed (18.0s)` (shallow 세 개 시나리오)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update (mixed-source|single-source|news-only) 자연어 reload 후 두 번째 follow-up" --reporter=line` → `3 passed (16.0s)` (second follow-up 세 개 시나리오)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 여섯 latest-update 자연어 reload 회귀에 순수 추가 어서션만 붙였고 기존 로직 변경이 없음. handoff 도 focused 여섯 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 기존 여섯 시나리오만 in-place tighten 함
- 기존 click-reload latest-update / plain show-only latest-update / entity-card / actual-search / dual-probe / zero-strong / general 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 여섯 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 전부 false-fail 됨. 같은 가정이 이전 click-reload latest-update / noisy empty-meta bundle 에서도 이미 사용되고 있어 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역(badge row, 제목, summary head) 이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 다른 곳에서 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- 여섯 서비스 회귀는 정확 dict equality (`{"strong": 0, "weak": 0, "missing": 0}`) 로 count-summary 를 잠금. `_summarize_claim_coverage` 가 추가 key 를 내거나 zero-count 표현이 None 로 바뀌면 equality 가 먼저 실패해 원인을 빠르게 가리킴 — failure-first 설계이며, 직전 click-reload 라운드의 동일 패턴과 상호 일관적
- handoff 지시에 따라 `최신 확인` / `기사 교차 확인` 에 대한 직접 blanket `not.toContainText` 는 의도적으로 피함 (false negative 방지). 대신 `.meta toHaveCount(0)` 으로 accidental `.meta` 생성 자체를 원천 차단. 이 전략은 이전 click-reload / noisy 라운드에서 이미 입증됨
- 이번 라운드로 latest-update (noisy + non-noisy) × (click-reload + 자연어 reload) × (shallow + second-follow-up) 분기가 모두 empty-meta no-leak 으로 잠기게 되었음. plain show-only latest-update reload 는 여전히 범위 밖이며 별도 라운드로 남겨둠
- 여섯 시나리오를 in-place tighten 했으므로 이름은 그대로 두었지만 실제로는 empty-meta no-leak 어서션까지 확장되었음. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
