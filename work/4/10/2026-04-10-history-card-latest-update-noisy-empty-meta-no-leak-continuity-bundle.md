# history-card latest-update noisy empty-meta no-leak continuity bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 latest-update noisy 네 follow-up 서비스 회귀에 history-card empty-meta continuity 어서션을 in-place 추가 (exclusion/provenance 어서션은 그대로 유지):
  - `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up`
  - `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_second_follow_up`
  - `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up`
  - `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up`
  - 네 회귀 모두 follow-up / second follow-up 응답 단계에서 `session.web_search_history` 의 해당 record 항목이 `verification_label == "기사 교차 확인"`, `claim_coverage_summary == {strong:0, weak:0, missing:0}`, 빈 `claim_coverage_progress_summary` 를 유지하는지 확인
- `e2e/tests/web-smoke.spec.mjs` — 기존 latest-update noisy 네 브라우저 시나리오(`:7625`, `:7702` 자연어 reload shallow/second, `:7781`, `:7855` click-reload shallow/second) 에 history-card empty-meta no-leak 어서션을 in-place 추가 (exclusion/provenance 어서션은 그대로 유지). 각 시나리오의 마지막 follow-up 이후 `historyCard.locator(".meta") toHaveCount(0)` 과 `historyCard not.toContainText("사실 검증")` 를 잠금

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-noisy-entity-card-shallow-strong-plus-missing-count-summary-meta-continuity-bundle.md`) 와 그 `/verify` 는 noisy entity-card strong-plus-missing 가족을 deep + shallow 모두 잠갔지만, 인접한 latest-update noisy 계열은 여전히 exclusion/provenance 만 잠겨 있고 history-card empty-meta no-leak 계약에 대한 명시적 회귀가 없음
- `storage/web_search_store.py:316-317` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 에 의해 현재 shipped 사실은:
  - latest-update noisy 런타임의 history entry 는 zero-count `claim_coverage_summary` 와 빈 progress 를 serialize 함
  - investigation 카드 (entity_card/latest_update) 는 `.meta` detailLines 에서 answer-mode label 을 skip 함
  - 따라서 해당 branch 는 `.meta` detail node 가 전혀 생성되지 않아야 함 (count line 없음, progress line 없음, label skip)
- 이 슬라이스는 런타임 변경 없이 기존 네 service 테스트와 네 browser 시나리오에 empty-meta + zero-count assertion block 을 in-place 추가해 "history card has no `.meta` detail node for this branch" 라는 current shipped contract 를 명시적으로 잠그는 범위임. entity-card / actual-search / dual-probe / zero-strong / general / docs / pipeline 은 의도적으로 범위 밖이며 handoff 지시에 따라 건드리지 않음

## 핵심 변경
1. **`tests/test_web_app.py` 네 latest-update noisy follow-up 회귀 in-place tighten**
   - 네 테스트 모두 마지막 follow-up 단계(`third` 또는 `fourth`) 의 `session.web_search_history` 에서 해당 `record_id` 항목을 찾고:
     - `verification_label == "기사 교차 확인"`
     - `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 0}` (dict equality, 완전 zero-count 패턴)
     - `claim_coverage_progress_summary == ""`
     - 를 잠금
   - 기존 exclusion/provenance 어서션은 전부 그대로 유지 (`brunch`/`보조 커뮤니티` 미노출, `hankyung.com`/`mk.co.kr` source_paths 유지)
   - 신규 helper/import/fixture 파일 없음. 기존 `_FakeWebSearchTool` / `AppSettings` / `WebAppService` fixture 를 그대로 재사용
2. **`e2e/tests/web-smoke.spec.mjs` 네 latest-update noisy 시나리오 in-place tighten**
   - 네 시나리오 모두 마지막 follow-up 이후(기존 `originBadge` / `answerModeBadge` / `originDetail` / `#context-box` 어서션 바로 뒤) 아래 두 assertion 을 추가:
     - `historyBox.locator(".history-item").first().locator(".meta") toHaveCount(0)` — investigation empty branch 에서 `.meta` detail node 가 전혀 생성되지 않음을 잠금. app.js 의 header timestamp span 은 className 이 없는 raw `<span>` 이므로 `.meta` CSS selector 에 매칭되지 않아 false positive 없음
     - `historyBox.locator(".history-item").first() not.toContainText("사실 검증")` — 혹시 accidental `.meta` creation 으로 count/progress line 이 leak 되면 `사실 검증 ...` 접두어가 전체 카드 텍스트에 나타날 텐데, 그 leak 자체를 막는 double-guard. history card 의 badge row / 제목 / summary 영역에는 `사실 검증` 문자열이 등장하지 않으므로 false positive 없음
   - handoff 가 요구한 `최신 확인` / `기사 교차 확인` 에 대한 직접 `not.toContainText` guard 는 의도적으로 사용하지 않음 — 이 두 문자열은 각각 `.answer-mode-badge` 와 `.verification-badge` DOM 에 **정상적으로** 등장하기 때문에 history card 전체 텍스트에 대한 blanket 부정이 false negative 가 됨. 대신 `.meta toHaveCount(0)` 이 accidental `.meta` 생성을 원천 차단하므로, 만약 future drift 가 detailMeta 를 만들어 `최신 확인` 이나 `기사 교차 확인` 을 거기에 담는다면 `.meta` count 가 0 이 아니게 되어 바로 실패함. 같은 이유로 doubled separator / leading-trailing separator artifact 도 `.meta` 존재 여부 하나로 origin 에서 차단됨
   - 기존 exclusion (`originDetail`/`responseText`/`#context-box` 에서 `보조 커뮤니티`/`brunch` 미노출) 과 provenance (`hankyung.com`/`mk.co.kr` 유지) 어서션은 전부 그대로 유지
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - entity-card / actual-search / dual-probe / zero-strong / general / non-noisy 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_second_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up` → 네 테스트 모두 `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update noisy community source가 자연어 reload 후 .*follow-up에서도" --reporter=line` → `2 passed (13.4s)` (shallow + second-follow-up 모두 실행됨)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update noisy community source가 다시 불러오기 후 .*follow-up에서도" --reporter=line` → `2 passed (11.7s)` (shallow + second-follow-up 모두 실행됨)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 네 latest-update noisy 회귀에 순수 추가 어서션만 붙였고 기존 로직 변경이 없음. handoff 도 focused 네 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 기존 네 latest-update noisy 시나리오만 in-place tighten 함
- 기존 entity-card noisy / actual-search / dual-probe / zero-strong / general 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 네 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 전부 false-fail 됨. 같은 가정이 이전 entity-card strong-plus-missing 시나리오에서도 `.history-item .meta toHaveCount(1)` 식으로 이미 사용되고 있어 이 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역(badge row, 제목, summary head) 이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 다른 곳에서 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- 네 서비스 회귀는 정확 dict equality (`{"strong": 0, "weak": 0, "missing": 0}`) 로 count-summary 를 잠금. `_summarize_claim_coverage` 가 추가 key 를 내거나 zero-count 표현이 None 로 바뀌면 equality 가 먼저 실패해 원인을 빠르게 가리킴 — failure-first 설계이며, 직전 라운드들의 `strong/weak/missing` 분기 단언과 상호 보완적
- `verification_label == "기사 교차 확인"` 은 현재 noisy latest-update 분기의 shipped 문자열에 의존함. 향후 label 문구가 바뀌면 네 서비스 회귀와 origin-detail 어서션이 함께 깨져야 하므로 drift 감지 자체는 유지됨
- handoff 지시에 따라 `최신 확인` / `기사 교차 확인` 에 대한 직접 blanket `not.toContainText` 는 의도적으로 피함 (false negative 방지). 대신 `.meta toHaveCount(0)` 으로 accidental `.meta` 생성 자체를 원천 차단
- entity-card / actual-search / dual-probe / zero-strong / general 가족의 `.meta` 계약은 이전 라운드들에서 각자 다른 방식(count-summary exact text, `not.toContainText(" ·  · ")` 등) 으로 잠금. 본 슬라이스는 latest-update noisy empty-branch 만 다루며 다른 가족은 범위 밖
- 네 시나리오를 in-place tighten 했으므로 이름은 그대로 두었지만 실제로는 empty-meta no-leak 어서션까지 확장되었음. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
