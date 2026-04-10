# history-card noisy entity-card strong-plus-missing count-summary meta continuity bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 noisy 두 second-follow-up 서비스 회귀에 count-summary continuity 어서션을 in-place 추가 (exclusion/provenance 어서션은 그대로 유지):
  - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up`
  - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up`
  - 두 회귀 모두 마지막 `fourth` 단계에서 `session.web_search_history` 의 해당 record 항목이 `verification_label == "설명형 다중 출처 합의"`, `claim_coverage_summary.strong > 0`, `.weak == 0`, `.missing > 0`, 빈 `claim_coverage_progress_summary` 를 유지하는지 확인
- `e2e/tests/web-smoke.spec.mjs` — 기존 noisy 두 second-follow-up 브라우저 시나리오를 stale 단일-strong fixture 에서 실제 런타임 strong-plus-missing 분기로 truth-sync:
  - `entity-card 붉은사막 자연어 reload 후 두 번째 follow-up에서 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance continuity가 유지됩니다`
  - `history-card entity-card noisy single-source claim(출시일/2025/blog.example.com)이 다시 불러오기 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`
  - 두 시나리오 모두 디스크 record `claim_coverage` 를 1 strong → 3 strong + 2 missing slot 으로 확장, `claim_coverage_progress_summary: "교차 확인 1건."` → `""` 로 전환, `renderSearchHistory` item 에 `claim_coverage_summary: {strong:3, weak:0, missing:2}` + 빈 progress 시드, 첫/두 번째 follow-up 각 단계에서 history-card `.meta === "사실 검증 교차 확인 3 · 미확인 2"` + 합성 순서/leading/trailing/doubled separator 부정 + answer-mode label 누출 부정 어서션 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-actual-search-entity-card-strong-plus-missing-count-summary-meta-continuity-bundle.md`) 와 그 `/verify` 는 actual-search strong-plus-missing 가족을 잠갔고, 같은 라운드의 검증 단계에서 다음 현재 위험으로 noisy entity-card 의 strong-plus-missing 분기가 명확히 드러남
- latest-update 가족은 focused probe 결과 현재 런타임이 zero-count / empty-progress 를 내서 non-empty user-visible `.meta` 분기가 존재하지 않음. 따라서 noisy entity-card 가 다음으로 직접적인 user-visible `.meta` 위험
- focused probe 결과: noisy 런타임(`namu.wiki` + `ko.wikipedia.org` + `blog.example.com`) 은 `verification_label="설명형 다중 출처 합의"`, `strong=3`, `weak=0`, `missing=2`, `claim_coverage_progress_summary=""`, `source_roles=["백과 기반"]` 을 내서 `app/static/app.js:2225-2231` + `:2954-2969` 의 렌더러 경로에 의해 `.meta` 는 `사실 검증 교차 확인 3 · 미확인 2` 한 줄이어야 함
- 기존 noisy browser scenarios (`:6770`, `:8042`) 는 `claim_coverage: [단일 strong slot]` 과 `claim_coverage_progress_summary: "교차 확인 1건."` 을 stale 하게 시드해 실제 런타임 `.meta` 분기를 exercise 하지 못함. 기존 noisy 서비스 테스트 (`:18772`, `:18889`) 는 exclusion/provenance 만 잠갔고 count-summary continuity 에 대한 명시적 회귀가 없음
- 이 슬라이스는 런타임 변경 없이 기존 noisy 두 서비스 테스트에 count-summary 어서션을 in-place 추가하고, 기존 noisy 두 브라우저 시나리오의 record/seed 를 strong-plus-missing 분기로 truth-sync 하는 범위임. 기존 exclusion/provenance 어서션은 모두 유지. actual-search / dual-probe / latest-update / zero-strong / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` count-summary continuity in-place 추가**
   - 두 noisy 두-번째-follow-up 회귀 모두 마지막 `fourth` 단계에서 동일한 pattern 을 추가:
     - `noisy_history = fourth["session"]["web_search_history"]` 에서 해당 `record_id` 항목을 찾음
     - `verification_label == "설명형 다중 출처 합의"` 잠금
     - `claim_coverage_summary.strong > 0`, `.weak == 0`, `.missing > 0` 정규화 패턴 잠금
     - `claim_coverage_progress_summary == ""` 잠금
   - 기존 exclusion (`출시일`/`2025`/`blog.example.com`) 과 provenance (`source_paths` 에 세 URL 유지) 어서션은 전부 그대로 유지
   - 신규 helper/import/fixture 파일 없음. 기존 mock `_FakeWebSearchTool` 구성과 `AppSettings` / `WebAppService` fixture 를 그대로 재사용
2. **`e2e/tests/web-smoke.spec.mjs` noisy 두 browser 시나리오 in-place tighten**
   - 디스크 record 의 `claim_coverage` 를 stale 한 1 slot (`[{장르 strong}]`) 에서 5 slot (`장르/개발사/플랫폼 = strong`, `출시일/가격 = missing`) 으로 확장해 실제 runtime mix 와 일치
   - `claim_coverage_progress_summary` 를 `"교차 확인 1건."` → `""` 로 전환 (실제 runtime 과 일치)
   - `renderSearchHistory` item 에 `claim_coverage_summary: {strong:3, weak:0, missing:2}` 와 빈 progress 를 시드해 server 재직렬화 결과와 client seed 가 동일하도록 정렬
   - 자연어 reload 시나리오(`:6770`): click-reload → `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` → 첫 follow-up → `.meta` 어서션 → 두 번째 follow-up → `.meta` 어서션
   - click-reload 시나리오(`:8042`): click-reload → 첫 follow-up → `.meta` 어서션 → 두 번째 follow-up → `.meta` 어서션
   - 두 시나리오 공통 `.meta` 어서션 (첫/두 번째 follow-up 각각):
     - `toHaveCount(1)` / `toHaveText("사실 검증 교차 확인 3 · 미확인 2")`
     - `not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색"` — investigation 카드는 answer-mode label 이 skip 되어야 함
     - handoff 지시대로 `not.toContainText("·")` blanket rule 은 사용하지 않음 — count line 자체에 ` · ` 가 합법적으로 포함됨
     - `not.toContainText(" ·  · ")` — doubled separator artifact 부정
     - `startsWith("·") === false` / `endsWith("·") === false` — leading/trailing separator artifact 부정
   - 기존 exclusion (`originDetail` 과 `responseText` 에서 `출시일`/`2025`/`blog.example.com` 미노출), provenance (`#context-box` 에 `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` 유지), origin badge / answer-mode badge / origin detail 어서션은 전부 그대로 유지
   - 두 시나리오의 selector, `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 actual-search / dual-probe / latest-update / zero-strong / general 계열 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up` → 두 테스트 모두 `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 두 번째 follow-up에서 noisy single-source claim" --reporter=line` → `1 passed (6.9s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card noisy single-source claim.*두 번째 follow-up" --reporter=line` → `1 passed (7.4s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 두 noisy 회귀에 순수 추가 어서션만 붙였고 기존 로직 변경이 없음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 기존 두 시나리오만 in-place tighten 함
- 기존 actual-search / dual-probe / latest-update / zero-strong / general 계열 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 두 브라우저 시나리오의 `.meta` 어서션은 디스크 record 에 시드한 `claim_coverage` 의 strong/missing 비율(`3 strong + 2 missing`) 에 의존함. 이 비율을 바꾸면 서버가 재직렬화하는 count dict 도 함께 바뀌므로 `toHaveText("사실 검증 교차 확인 3 · 미확인 2")` 를 같이 조정해야 함. 의존성은 시드 배열 단일 지점에서 관리됨
- 두 서비스 회귀는 `strong > 0`, `weak == 0`, `missing > 0` 정규화 패턴을 단언함. 실제 런타임이 다른 분기(예: weak 포함, missing 없음) 로 drift 하면 첫 번째 관련 assertion 에서 실패해 원인을 빠르게 가리킴 — failure-first 설계
- `formatClaimCoverageCountSummary({strong:3, missing:2})` 이 현재 `"교차 확인 3 · 미확인 2"` 를 내는 포맷 가정(`app/static/app.js:2225-2232`) 에 의존함. 포맷이 바뀌면 두 스모크가 먼저 깨짐 — 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- handoff 지시에 따라 `not.toContainText("·")` blanket rule 을 사용하지 않고 exact text + `not.toContainText(" ·  · ")` + leading/trailing `·` 부정 만으로 separator artifact 를 잠금. join separator 가 ` · ` 외 다른 문자로 바뀌면 이 조합이 먼저 깨짐
- 기존 시나리오를 in-place tighten 했으므로 이름은 그대로 두었지만 seed 와 `.meta` 어서션이 변경되었음. 이름은 exclusion/provenance continuity 를 강조하지만 실제로는 count-summary 까지 잠그는 것으로 확장됨. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
- latest-update / general / zero-strong / dual-probe / actual-search 가족의 `.meta` continuity 는 이미 이전 라운드에서 다루었거나 본 슬라이스 범위 밖이며, 각각 다른 `_infer_reloaded_answer_mode` 분기와 source-role 필터링을 함께 고려해야 하므로 별도 라운드로 남겨둠
