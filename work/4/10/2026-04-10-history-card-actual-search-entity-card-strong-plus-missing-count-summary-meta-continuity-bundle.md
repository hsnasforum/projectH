# history-card actual-search entity-card strong-plus-missing count-summary meta continuity bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 `test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_claim_coverage_count_summary` 는 그대로 두고 (baseline equality 패턴 유지), 그 뒤에 click-reload 카운터파트 `test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_claim_coverage_count_summary` 를 추가. 신규 회귀는 실제 런타임 분기(`verification_label == "설명형 다중 출처 합의"`, `strong > 0`, `weak == 0`, `missing > 0`, 빈 `claim_coverage_progress_summary`) 를 명시적으로 잠그고, show-only reload → 첫 follow-up → 두 번째 follow-up 각 단계에서 baseline strong/missing 카운트가 그대로 유지되는지 확인
- `e2e/tests/web-smoke.spec.mjs` — 기존 actual-search 두 시나리오를 stale 단일-strong fixture 에서 실제 런타임에 대응되는 strong-plus-missing 분기로 truth-sync:
  - `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다` (click-reload chain, `:3627`)
  - `entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up에서 source path(namu.wiki, ko.wikipedia.org)가 context box에 유지되고 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다` (natural-reload chain, `:6587`)
  - 두 시나리오 모두 디스크 record 의 `claim_coverage` 를 3 strong + 2 missing slot 으로 시드하고 stale 한 `교차 확인 1건.` progress-summary 를 빈 문자열로 전환, client-seeded `claim_coverage_summary: {strong:3, weak:0, missing:2}` 로 render 해, 첫/두 번째 follow-up 이후 모두 history-card `.meta === "사실 검증 교차 확인 3 · 미확인 2"` + 합성 순서/leading/trailing/doubled separator 부정 + answer-mode label 누출 부정 어서션을 잠금

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-dual-probe-entity-card-mixed-count-summary-meta-continuity-bundle.md`) 와 그 `/verify` 는 dual-probe mixed count-summary chain 을 잠갔고, 같은 라운드의 검증 단계에서 다음 현재 위험으로 actual-search entity-card 의 strong-plus-missing 분기가 명확히 드러남
- latest-update mixed-source 가족은 focused probe 결과 현재 런타임이 zero-count/empty-progress history summary 를 내서 non-empty user-visible `.meta` 분기가 존재하지 않음. 따라서 actual-search 가 다음으로 직접적인 user-visible `.meta` 위험
- focused probe 결과: 실제 actual-search 런타임은 `strong=3`, `weak=0`, `missing=2`, `claim_coverage_progress_summary=""`, `verification_label="설명형 다중 출처 합의"` 를 냄 → `app/static/app.js:2225-2231` + `:2958-2969` 의 렌더러 경로에 의해 `.meta` 는 `사실 검증 교차 확인 3 · 미확인 2` 한 줄이어야 함
- 기존 actual-search browser scenarios (`:2526`, `:3505`, `:3627`, `:6385`, `:6505`, `:6587`) 는 source-path / origin continuity 만 잠갔고, record 의 `claim_coverage` 는 단일 strong slot + `"교차 확인 1건."` progress 로 stale 하게 고정되어 있어 실제 런타임 `.meta` 분기를 exercise 하지 못함
- 기존 서비스 회귀 `test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_claim_coverage_count_summary` (`:9233`) 는 baseline equality 만 잠갔고 click-reload 카운터파트가 없음
- 이 슬라이스는 런타임 변경 없이 서비스 회귀 하나와 두 개의 기존 browser scenario tighten 으로 actual-search entity-card 의 strong-plus-missing 분기를 한 라운드에 닫는 범위임. dual-probe / latest-update / zero-strong / noisy / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` click-reload 카운터파트 회귀 추가**
   - `test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_claim_coverage_count_summary`
     - 기존 natural-reload 테스트와 동일한 `_FakeWebSearchTool` (namu.wiki + ko.wikipedia.org 두 결과) 와 `AppSettings` / `WebAppService` fixture 를 사용
     - baseline `handle_chat({user_text})` 호출 후:
       - `verification_label == "설명형 다중 출처 합의"`
       - `claim_coverage_summary.strong > 0`
       - `claim_coverage_summary.weak == 0`
       - `claim_coverage_summary.missing > 0`
       - 빈 `claim_coverage_progress_summary`
     - 를 명시적으로 잠금 (handoff 지시의 "explicit branch lock")
   - 내부 헬퍼 `_assert_strong_plus_missing_continuity(result, stage)` 로 show-only reload → 첫 follow-up → 두 번째 follow-up 각 단계에서:
     - `actions_taken` 에 `load_web_search_record` 포함
     - 동일 `record_id` 항목 존재
     - `verification_label == "설명형 다중 출처 합의"`
     - `strong == baseline_strong`, `weak == 0`, `missing == baseline_missing`
     - 빈 progress_summary
     - 를 잠금
   - 기존 natural-reload 회귀(`:9233`) 는 handoff 지시대로 그대로 유지했고 두 테스트는 동일한 mock fixture 구성을 공유함. 기존 helper 없이 신규 imports 도 추가하지 않음
2. **`e2e/tests/web-smoke.spec.mjs` 기존 두 actual-search 시나리오 tighten**
   - 두 시나리오 모두 디스크 record 의 `claim_coverage` 를 단일 strong slot → 3 strong + 2 missing slot 으로 전환 (`개발사/장르/플랫폼 = strong`, `출시일/가격 = missing`)
   - 두 시나리오 모두 `claim_coverage_progress_summary` 를 `"교차 확인 1건."` → `""` 로 전환 (실제 런타임과 일치)
   - 두 시나리오 모두 `renderSearchHistory` item 에 `claim_coverage_summary: {strong:3, weak:0, missing:2}` 와 빈 `claim_coverage_progress_summary` 를 시드해 server 재직렬화 결과와 client seed 가 동일하도록 정렬
   - click-reload 시나리오(`:3627`): click-reload → 첫 follow-up → `.meta` 어서션 → 두 번째 follow-up → `.meta` 어서션
   - natural-reload 시나리오(`:6587`): click-reload → `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` → 첫 follow-up → `.meta` 어서션 → 두 번째 follow-up → `.meta` 어서션
   - 공통 `.meta` 어서션 (첫/두 번째 follow-up 각각):
     - `toHaveCount(1)` / `toHaveText("사실 검증 교차 확인 3 · 미확인 2")`
     - `not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색"` — investigation 카드는 answer-mode label 이 skip 되어야 함
     - handoff 지시대로 `not.toContainText("·")` blanket rule 은 **사용하지 않음** — count line 자체에 ` · ` 가 합법적으로 포함되기 때문
     - `not.toContainText(" ·  · ")` — doubled separator artifact 부정
     - `startsWith("·") === false` / `endsWith("·") === false` — leading/trailing separator artifact 부정
   - 기존 `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box` 어서션은 모두 유지하고 두 번째 follow-up 이후에 추가 `web` class / visibility 체크를 포함
   - 두 시나리오의 selector (`#search-history-box`, `.history-item`, `.meta`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 noisy/zero-strong/latest-update/general 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_claim_coverage_count_summary` → `ok`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_claim_coverage_count_summary` → `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다" --reporter=line` → `1 passed (7.4s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up에서 source path(namu.wiki, ko.wikipedia.org)가 context box에 유지되고 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다" --reporter=line` → `1 passed (6.7s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 `handle_chat` 경로에 순수 추가 회귀 하나만 붙였고 기존 로직 변경이 없음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 두 개의 기존 시나리오만 in-place tighten 함
- 기존 actual-search source-path / origin 계열 다른 시나리오 (`:2526`, `:3505`, `:6385`, `:6505`) — handoff 는 가장 깊은 두 second-follow-up chain 만 tighten 하도록 명시함

## 남은 리스크
- 두 브라우저 시나리오의 `.meta` 어서션은 디스크 record 에 시드한 `claim_coverage` 의 strong/missing 비율(`3 strong + 2 missing`) 에 의존함. 이 비율을 바꾸면 서버가 재직렬화하는 count dict 도 함께 바뀌므로 `toHaveText("사실 검증 교차 확인 3 · 미확인 2")` 를 같이 조정해야 함. 의존성은 시드 배열 단일 지점에서 관리됨
- click-reload 서비스 회귀는 `strong > 0`, `weak == 0`, `missing > 0` 정규화 패턴과 baseline drift 부재를 단언함. 실제 런타임이 다른 분기(예: weak 포함) 로 drift 하면 baseline 단계 assertion 에서 먼저 실패해 원인을 빠르게 가리킴 — failure-first 설계. 기존 natural-reload 회귀는 baseline equality 만 유지해 두 회귀가 서로 다른 각도에서 같은 경로를 잠금
- 내부 헬퍼 `_assert_strong_plus_missing_continuity` 의 `result` 인자는 `Any` 타입 힌트를 의도적으로 사용하지 않음 (`from typing import Any` 가 해당 파일 상단에 import 되어 있지 않음). dict-like 구조를 전제로 한 assertion 시퀀스만 수행함
- `formatClaimCoverageCountSummary({strong:3, missing:2})` 이 현재 `"교차 확인 3 · 미확인 2"` 를 내는 포맷 가정(`app/static/app.js:2225-2232`) 에 의존함. 포맷이 바뀌면 두 스모크가 먼저 깨짐 — 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- handoff 지시에 따라 `not.toContainText("·")` blanket rule 을 사용하지 않고 exact text + `not.toContainText(" ·  · ")` + leading/trailing `·` 부정 만으로 separator artifact 를 잠금. join separator 가 ` · ` 외 다른 문자로 바뀌면 이 조합이 먼저 깨짐
- dual-probe / latest-update / zero-strong / noisy / general 가족의 `.meta` continuity 는 이전 라운드 또는 향후 라운드에서 별도로 다룸. 각각 다른 `_infer_reloaded_answer_mode` 분기와 source-role 필터링을 함께 고려해야 하므로 본 슬라이스 범위 밖
- 기존 시나리오를 in-place tighten 했으므로 이름은 그대로 두었지만 record/`renderSearchHistory` seed 와 `.meta` 어서션이 변경되었음. 이름은 source-path / origin continuity 를 강조하지만 실제로는 그것과 더불어 strong-plus-missing count-summary 까지 잠그는 것으로 확장됨. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
