# history-card noisy entity-card shallow strong-plus-missing count-summary meta continuity bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 noisy 두 **shallow follow-up** 서비스 회귀에 count-summary continuity 어서션을 in-place 추가 (exclusion/provenance 어서션은 그대로 유지):
  - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up`
  - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up`
  - 두 회귀 모두 `third` (first follow-up) 단계에서 `session.web_search_history` 의 해당 record 항목이 `verification_label == "설명형 다중 출처 합의"`, `claim_coverage_summary.strong > 0`, `.weak == 0`, `.missing > 0`, 빈 `claim_coverage_progress_summary` 를 유지하는지 확인
- `e2e/tests/web-smoke.spec.mjs` — 기존 noisy 두 **shallow follow-up** 브라우저 시나리오를 stale 단일-strong fixture 에서 실제 런타임 strong-plus-missing 분기로 truth-sync:
  - `entity-card 붉은사막 자연어 reload 후 follow-up에서 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance continuity가 유지됩니다` (자연어 reload shallow)
  - `history-card entity-card noisy single-source claim(출시일/2025/blog.example.com)이 다시 불러오기 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다` (click-reload shallow)
  - 두 시나리오 모두 디스크 record 의 `claim_coverage` 를 1 strong slot + stale `"교차 확인 1건."` progress 에서 3 strong + 2 missing slot + `""` progress 로 전환하고, `renderSearchHistory` item 에 `claim_coverage_summary: {strong:3, weak:0, missing:2}` + 빈 progress 를 시드해, first follow-up 이후 history-card `.meta === "사실 검증 교차 확인 3 · 미확인 2"` + 합성 순서/leading/trailing/doubled separator 부정 + answer-mode label 누출 부정 어서션을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-noisy-entity-card-strong-plus-missing-count-summary-meta-continuity-bundle.md`) 와 그 `/verify` 는 noisy **second** follow-up 가족(`:18772`, `:18889`, `:6770`, `:8085`) 을 잠갔지만, 같은 가족의 **shallow (first) follow-up** 분기는 stale 한 단일-strong `claim_coverage` 와 `"교차 확인 1건."` progress 를 그대로 시드해 실제 런타임 분기를 관찰하지 못함
- 기존 shallow 서비스 테스트(`:18715`, `:18831`) 는 `response_origin` exclusion/provenance 만 잠갔고, `claim_coverage_summary` 의 strong-plus-missing 패턴에 대한 명시적 회귀가 없음
- 실제 noisy 런타임은 이전 focused probe 와 deeper 시나리오에서 이미 알려져 있음: `verification_label="설명형 다중 출처 합의"`, `strong=3`, `weak=0`, `missing=2`, `claim_coverage_progress_summary=""` → `app/static/app.js:2225-2231` + `:2954-2969` 의 렌더러 경로에 의해 `.meta` 는 `사실 검증 교차 확인 3 · 미확인 2` 한 줄이어야 함
- 이 슬라이스는 런타임 변경 없이 기존 shallow noisy 두 서비스 테스트에 count-summary 어서션을 in-place 추가하고, 기존 shallow noisy 두 브라우저 시나리오의 record/seed 를 strong-plus-missing 분기로 truth-sync 하는 범위임. 기존 exclusion/provenance 어서션은 모두 유지. actual-search / dual-probe / zero-strong / general / latest-update / docs / pipeline / non-noisy browser 가족은 의도적으로 범위 밖이며 handoff 지시에 따라 건드리지 않음

## 핵심 변경
1. **`tests/test_web_app.py` shallow noisy 두 회귀 in-place tighten**
   - 두 shallow first-follow-up 회귀 모두 `third` (첫 follow-up 응답) 단계에서 동일한 pattern 을 추가:
     - `noisy_history = third["session"]["web_search_history"]` 에서 해당 `record_id` 항목을 찾음
     - `verification_label == "설명형 다중 출처 합의"` 잠금
     - `claim_coverage_summary.strong > 0`, `.weak == 0`, `.missing > 0` 정규화 패턴 잠금
     - `claim_coverage_progress_summary == ""` 잠금
   - 기존 exclusion (`출시일`/`2025`/`blog.example.com`) 과 provenance (`source_paths` 에 세 URL 유지) 어서션은 전부 그대로 유지
   - 신규 helper/import/fixture 파일 없음. 기존 `_FakeWebSearchTool` / `AppSettings` / `WebAppService` fixture 를 그대로 재사용. 두 번째 follow-up 회귀에 추가한 동일한 assertion block 을 shallow 단계에 동일 형태로 적용해 일관된 failure-first 설계 유지
2. **`e2e/tests/web-smoke.spec.mjs` shallow noisy 두 시나리오 in-place tighten**
   - 디스크 record 의 `claim_coverage` 를 stale 한 1 slot (`[{장르 strong}]`) 에서 5 slot (`장르/개발사/플랫폼 = strong`, `출시일/가격 = missing`) 으로 확장해 실제 runtime mix 와 일치
   - `claim_coverage_progress_summary` 를 `"교차 확인 1건."` → `""` 로 전환 (실제 runtime 과 일치)
   - `renderSearchHistory` item 에 `claim_coverage_summary: {strong:3, weak:0, missing:2}` 와 빈 progress 를 시드해 server 재직렬화 결과와 client seed 가 동일하도록 정렬
   - 자연어 reload 시나리오(`:6691`): click-reload → `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` → 첫 follow-up → 본문/origin/source-path 어서션 + `.meta` 어서션
   - click-reload 시나리오(`:8051`): click-reload → 첫 follow-up → 본문/origin/source-path 어서션 + `.meta` 어서션
   - 두 시나리오 공통 `.meta` 어서션 (first follow-up 이후):
     - `toHaveCount(1)` / `toHaveText("사실 검증 교차 확인 3 · 미확인 2")`
     - `not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색"` — investigation 카드는 answer-mode label 이 skip 되어야 함
     - handoff 지시대로 `not.toContainText("·")` blanket rule 은 사용하지 않음 — count line 자체에 ` · ` 가 합법적으로 포함됨
     - `not.toContainText(" ·  · ")` — doubled separator artifact 부정
     - `startsWith("·") === false` / `endsWith("·") === false` — leading/trailing separator artifact 부정
   - 기존 exclusion (`originDetail`/`responseText` 에서 `출시일`/`2025`/`blog.example.com` 미노출), provenance (`#context-box` 에 `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` 유지), origin badge / answer-mode badge / origin detail 어서션은 전부 그대로 유지
   - 두 시나리오의 selector, `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 second-follow-up noisy 시나리오와 actual-search/dual-probe/zero-strong/general/latest-update/non-noisy 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up` → 두 테스트 모두 `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 noisy single-source claim" --reporter=line` → `1 passed (7.3s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card noisy single-source claim.*follow-up에서도" --reporter=line` → `2 passed (12.3s)` (`-g` 정규식이 shallow 와 second-follow-up scenario 두 개에 모두 매칭되어 둘 다 실행됨 — 둘 다 `ok`)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 두 shallow noisy 회귀에 순수 추가 어서션만 붙였고 기존 로직 변경이 없음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 기존 두 shallow 시나리오만 in-place tighten 함
- 기존 noisy second-follow-up 시나리오는 handoff 가 건드리지 말라고 지시했지만, handoff 의 `-g` 패턴이 shallow + second-follow-up 두 개를 함께 매칭해 click-reload 쪽에서는 두 개 모두 재실행되었음. 두 번째 시나리오는 변경하지 않았고 재실행 결과도 `ok` 이므로 drift 가 관찰되지 않음

## 남은 리스크
- 두 브라우저 시나리오의 `.meta` 어서션은 디스크 record 에 시드한 `claim_coverage` 의 strong/missing 비율(`3 strong + 2 missing`) 에 의존함. 이 비율을 바꾸면 서버가 재직렬화하는 count dict 도 함께 바뀌므로 `toHaveText("사실 검증 교차 확인 3 · 미확인 2")` 를 같이 조정해야 함. 의존성은 시드 배열 단일 지점에서 관리됨
- 두 서비스 회귀는 `strong > 0`, `weak == 0`, `missing > 0` 정규화 패턴을 단언함. 실제 런타임이 다른 분기(예: weak 포함, missing 없음) 로 drift 하면 해당 assertion 에서 먼저 실패해 원인을 빠르게 가리킴 — failure-first 설계
- `formatClaimCoverageCountSummary({strong:3, missing:2})` 이 현재 `"교차 확인 3 · 미확인 2"` 를 내는 포맷 가정(`app/static/app.js:2225-2232`) 에 의존함. 포맷이 바뀌면 두 스모크가 먼저 깨짐 — 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- handoff 지시에 따라 `not.toContainText("·")` blanket rule 을 사용하지 않고 exact text + `not.toContainText(" ·  · ")` + leading/trailing `·` 부정 만으로 separator artifact 를 잠금. join separator 가 ` · ` 외 다른 문자로 바뀌면 이 조합이 먼저 깨짐
- 기존 시나리오를 in-place tighten 했으므로 이름은 그대로 두었지만 seed 와 `.meta` 어서션이 변경되었음. 이름은 exclusion/provenance continuity 를 강조하지만 실제로는 count-summary 까지 잠그는 것으로 확장됨. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
- 이번 라운드로 click-reload / 자연어 reload × shallow / second-follow-up 네 noisy 분기가 모두 strong-plus-missing count-summary 를 잠그게 되었음. actual-search / dual-probe / zero-strong 가족은 이전 라운드에서 잠겼고, latest-update / general 가족은 현재 런타임에 non-empty `.meta` 분기가 없어 본 슬라이스 범위 밖
