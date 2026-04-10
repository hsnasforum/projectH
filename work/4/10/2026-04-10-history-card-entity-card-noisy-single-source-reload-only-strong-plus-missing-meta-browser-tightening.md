# history-card entity-card noisy single-source reload-only strong-plus-missing meta browser tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 기존 noisy entity-card show-only reload 시나리오 (`:2615`, `history-card entity-card 다시 불러오기 후 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`) 를 제자리에서 tighten.
  - 디스크 `claim_coverage` 를 단일 `장르 strong` slot + `"교차 확인 1건."` progress 에서 3 strong (`장르`/`개발사`/`플랫폼`) + 2 missing (`엔진`/`난이도`) slot + 빈 progress 로 확장해 shipped noisy strong-plus-missing 분포와 일치시킴. slot 이름은 noisy 제외 키워드(`출시일`/`2025`/`brunch`/`blog.example.com`) 와 충돌하지 않도록 의도적으로 선택.
  - `renderSearchHistory` item 에 shipped non-empty count-summary 를 explicit seed: `claim_coverage_summary: { strong: 3, weak: 0, missing: 2 }`, `claim_coverage_progress_summary: ""`.
  - 기존 reload-click 이후 provenance/exclusion/context-box 어서션은 그대로 유지하면서, post-reload 블록 말미에 history-card `.meta` 어서션을 추가:
    - `historyCardMeta.toHaveCount(1)`
    - `historyCardMeta.toHaveText("사실 검증 교차 확인 3 · 미확인 2")`
    - `.meta` 스코프 `not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색")` (investigation entity_card 는 answer-mode label skip)
- `tests/test_web_app.py` 는 전혀 건드리지 않음. handoff 지시에 따라 `tests/test_web_app.py:19532` / `:19687` 을 semantic anchor 로만 활용.

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- CONTROL_SEQ 57 (`2026-04-10-history-card-entity-card-noisy-single-source-initial-render-strong-plus-missing-meta-browser-bundle.md`) 가 noisy entity-card 가족의 **initial-render** 단계 strong-plus-missing `.meta` 계약을 browser 측에서 독립적으로 잠근 직후 상태였음.
- handoff (CONTROL_SEQ 58) 는 "Do not reopen the already-closed entity-card initial-render family" 라고 명시하고, 가장 인접한 next same-family current-risk reduction 으로 **post-click show-only reload** 단계의 strong-plus-missing `.meta` 직접 어서션을 지목함.
- 기존 `:2615` 시나리오는 reload 후 provenance/exclusion/context-box/response-origin detail 계약은 잠갔지만, history-card `.meta` 가 shipped strong-plus-missing branch 의 exact text (`사실 검증 교차 확인 3 · 미확인 2`) 로 rendering 됨을 user-visible 로 직접 exercise 하지는 않았음. `tests/test_web_app.py:19532`, `:19687` 는 이 분기가 post-reload/follow-up chain 에서 server 측에 잠겨 있음을 이미 증명한 상태.
- `storage/web_search_store.py:316` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 의 렌더러 경로는 investigation entity_card 에서 answer-mode label 을 skip 하고 `formatClaimCoverageCountSummary({strong:3, weak:0, missing:2})` = `"교차 확인 3 · 미확인 2"` 를 내므로 `.meta` 는 `사실 검증 교차 확인 3 · 미확인 2` 한 줄이어야 함. noisy 가족도 동일 렌더러 분기를 공유하고 noisy exclusion 은 `source_roles` 에서 이미 처리된 상태.
- 기존 시나리오를 제자리에서 tighten 하라는 handoff 지시를 따라 duplicate 시나리오를 만들지 않고 동일 시나리오의 디스크 seed / client seed / post-reload 어서션을 한 곳에서 정합화.

## 핵심 변경
1. **`e2e/tests/web-smoke.spec.mjs:2615` 시나리오 in-place tightening**
   - 디스크 `claim_coverage` 를 3 strong (`장르`/`개발사`/`플랫폼`) + 2 missing (`엔진`/`난이도`) slot 으로 확장. 각 strong slot 은 `support_count:2, candidate_count:2, source_role:"encyclopedia"` 로 shipped 분포와 일치. `claim_coverage_progress_summary` 를 `""` 로 비움.
   - `renderSearchHistory` item 에 `claim_coverage_summary: { strong: 3, weak: 0, missing: 2 }` 와 `claim_coverage_progress_summary: ""` 를 시드해 pre-click 에서도 동일 shape 가 준비되도록 함 (다만 본 시나리오 assert 는 reload 이후 상태에서 수행).
   - reload button 클릭 → provenance/exclusion/context-box/response-origin detail 어서션 블록 뒤에 `.meta` locator 확보 및 어서션 추가:
     - `historyCardMeta.toHaveCount(1)` — investigation entity_card 는 detailLines 가 최소 count-summary line 한 줄을 만들어냄
     - `historyCardMeta.toHaveText("사실 검증 교차 확인 3 · 미확인 2")` — `formatClaimCoverageCountSummary({3,0,2})` → `"교차 확인 3 · 미확인 2"` 에 `사실 검증 ` prefix
     - `.meta` 스코프 `not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색")` — investigation card 는 answer-mode label skip 이어야 함
   - 기존 noisy 키워드 배제 guard (`출시일`/`2025`/`blog.example.com` 에 대한 본문 / origin detail 부정) 와 `설명형 다중 출처 합의` / `백과 기반` / `namu.wiki` / `ko.wikipedia.org` / `blog.example.com` provenance 어서션은 그대로 유지.
   - 새 helper/selector/fixture 파일을 만들지 않고 기존 `#search-history-box`, `.history-item`, `.meta`, `prepareSession`, `renderSearchHistory` 만 재사용.
2. **`tests/test_web_app.py` 는 전혀 건드리지 않음**
   - handoff 가 "keep existing service tests untouched unless you discover a concrete mismatch" 라고 명시함. `tests/test_web_app.py:19532`, `:19687` 는 noisy entity-card click-reload / 자연어 reload 체인에서 strong-plus-missing count-summary + 빈 progress + noisy source exclusion 을 이미 잠가두고 있으며, 본 라운드는 이를 semantic anchor 로만 활용.
3. latest-update / dual-probe / zero-count / general / docs / pipeline / initial-render / follow-up / second follow-up / click-reload follow-up / 기존 non-noisy 시나리오는 전혀 건드리지 않음 (handoff 지시).

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up` → 두 테스트 모두 `ok` (noisy entity-card 의 strong-plus-missing + exclusion 계약이 server 측 natural / click reload 체인에서 여전히 잠겨 있음을 재확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 noisy single-source claim\(출시일/2025/blog.example.com\).*" --reporter=line` → `1 passed (7.1s)` (tighten 된 시나리오가 확장된 strong-plus-missing seed 와 새 `.meta` 어서션에서 통과)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 `tests/test_web_app.py` 를 전혀 건드리지 않았고, handoff 도 focused 두 service anchor 만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — 기존 시나리오 한 개를 제자리에서 tighten 했을 뿐 shared helper 나 browser-visible contract 를 확장하지 않음
- 기존 noisy entity-card initial-render (CONTROL_SEQ 57) / follow-up / second follow-up / click-reload follow-up / non-noisy entity-card / latest-update / store-seeded actual-search 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- `.meta` exact text `"사실 검증 교차 확인 3 · 미확인 2"` 는 `formatClaimCoverageCountSummary` 의 `"교차 확인 N · 단일 출처 N · 미확인 N"` 포맷 규약에 의존. 포맷이 바뀌면 본 시나리오가 먼저 깨져 drift 를 가리킴.
- 디스크 `claim_coverage` slot 이름은 `엔진`/`난이도` 로 선택해 noisy 제외 키워드 (`출시일`/`2025`/`brunch`/`blog.example.com`) 와 충돌을 피함. 향후 noisy 키워드 목록이 확장되면 slot 이름도 함께 재검토 필요.
- `renderSearchHistory` item 에 `claim_coverage_summary: {3,0,2}` 를 pre-click 시드로 남기되, 본 시나리오의 assert 는 reload 이후 상태에서 이뤄짐. pre-click 단계에서도 `.meta` 가 동일 문자열로 준비되지만 본 시나리오는 reload 이후 상태만 직접 검증하며, pre-click initial-render 브랜치는 CONTROL_SEQ 57 이 독립적으로 잠가둠.
- server 측 noisy source filtering / count-summary serialization 이 바뀌면 본 시나리오 하나만으로는 drift 를 즉시 포착하지 못할 수 있음. 1차 방어는 `tests/test_web_app.py:19532`, `:19687` 의 noisy entity-card service 회귀가 담당하고, 본 시나리오는 post-reload client-side `.meta` exact text 규약을 보완적으로 잠금.
- CONTROL_SEQ 56 (entity-card non-noisy initial-render × 2) → 57 (noisy initial-render × 1) → 58 (본 라운드: noisy post-click show-only reload tightening × 1) 루프는 noisy entity-card 가족의 strong-plus-missing branch 를 pre-click initial-render 와 post-click reload-only 두 축에서 browser-visible 로 잠그는 진행 패턴.
- handoff 가 "service tests untouched unless a concrete mismatch" 라고 명시했고 본 라운드는 service 측을 건드리지 않아 CONTROL_SEQ 31/32/41/42/44-57 및 기존 noisy entity-card 회귀들의 잠금 상태를 그대로 유지.
- 본 라운드는 duplicate 시나리오를 만들지 않고 `:2615` 를 in-place tighten 했으므로 파일 구조 / 시나리오 순서 / coverage 카운트는 변동 없음.
