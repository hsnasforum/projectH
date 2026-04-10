# history-card entity-card initial-render strong-plus-missing + mixed count-summary meta browser bundle

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 기존 entity-card actual-search reload 시나리오 (`:2650`) 직전에 두 개의 신규 initial-render 시나리오를 한 블록으로 삽입:
  - `history-card entity-card actual-search initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다`
  - `history-card entity-card dual-probe initial-render 단계에서 mixed count-summary meta contract가 유지됩니다`
  - 두 시나리오 모두 디스크 record 에 baseline runtime 분포와 일치하는 `claim_coverage` 슬롯 시드, `renderSearchHistory` item 에 shipped `claim_coverage_summary` (actual-search: `{strong:3, weak:0, missing:2}`, dual-probe: `{strong:1, weak:4, missing:0}`) + 빈 progress 를 explicit 하게 시드, `다시 불러오기` 클릭 / 자연어 reload / follow-up 을 **전혀 수행하지 않고** pre-click 상태에서 `reloadButton.toHaveText("다시 불러오기")` + `historyCardMeta.toHaveCount(1)` + `toHaveText` exact 문자열 + answer-mode label 누출 부정 어서션을 잠금
- `tests/test_web_app.py` 는 전혀 건드리지 않음 (handoff 지시에 따라 `tests/test_web_app.py:9473-9474`, `:9796`, `:9921` 를 semantic anchor 로만 활용)

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-latest-update-noisy-initial-render-serialized-zero-count-empty-meta-browser-bundle.md`, CONTROL_SEQ 55) 는 latest-update noisy 가족의 initial-render 단계 zero-count no-leak 계약을 browser 측에서 독립적으로 잠갔음
- handoff 는 "Do not keep shrinking the already-closed latest-update empty-meta family into more note-only or docs-only micro-slices" 라고 명시하고, 가장 인접한 next user-visible gap 으로 **entity-card** 가족의 initial-render 단계에서 **non-empty count-summary** 분기를 지목함
- 기존 entity-card 가족의 browser 시나리오들은 actual-search / dual-probe 의 non-empty count-summary 분기를 post-click (reload-only / follow-up / second follow-up) 단계에서 잠갔지만, **pre-click initial-render** 상태에서 shipped non-empty count-summary dict 를 받아도 `.meta` 가 정확한 exact 문자열로 렌더링됨을 user-visible 로 exercise 하는 회귀는 없었음. 유일한 entity-card initial-render 시나리오 (`:3955`, CONTROL_SEQ 53) 는 zero-count empty-meta no-leak 경로만 exercise
- `storage/web_search_store.py:316` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 의 렌더러 경로는 investigation entity_card 에서 answer-mode label 을 skip 하고:
  - actual-search strong-plus-missing → `formatClaimCoverageCountSummary({strong:3, weak:0, missing:2})` = `"교차 확인 3 · 미확인 2"` → `.meta = "사실 검증 교차 확인 3 · 미확인 2"`
  - dual-probe mixed → `formatClaimCoverageCountSummary({strong:1, weak:4, missing:0})` = `"교차 확인 1 · 단일 출처 4"` → `.meta = "사실 검증 교차 확인 1 · 단일 출처 4"`
- 이 두 분기는 각각 CONTROL_SEQ 32/42/44 (actual-search) 와 CONTROL_SEQ 31/41 (dual-probe) 에서 post-click 경로로 잠겨 있었고, 본 라운드는 동일 분기를 **pre-click initial-render** 경로로도 확장해 렌더러가 explicit non-empty count-summary dict 를 받자마자 정확히 잠긴 shape 를 내도록 잠금
- 본 슬라이스는 service refactor 없이 두 개의 bounded browser 회귀를 한 bundle 로 추가하는 범위임. latest-update / zero-count / noisy latest-update follow-up / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`e2e/tests/web-smoke.spec.mjs` 두 개의 신규 initial-render 시나리오**
   - 두 시나리오 공통 패턴:
     - 디스크 record 에 baseline runtime 분포와 일치하는 `claim_coverage` 슬롯을 시드
     - `response_origin`: `answer_mode: "entity_card"`, `verification_label: "설명형 다중 출처 합의"`, 각 변형별 `source_roles`
     - `renderSearchHistory` item 에 shipped `claim_coverage_summary` (explicit non-empty dict) + 빈 progress 를 시드
     - **`다시 불러오기` 클릭 / 자연어 reload / follow-up 을 전혀 수행하지 않음**
     - pre-click 어서션:
       - `#search-history-box` visible
       - `historyCard.locator(".history-item-actions button.secondary")` 가 `"다시 불러오기"` 텍스트 포함
     - `.meta` 어서션:
       - `historyCardMeta.toHaveCount(1)`
       - `historyCardMeta.toHaveText(<exact string>)`
       - `historyCardMeta.not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색"` (investigation card 는 answer-mode label skip)
   - **actual-search 변형** (`:2650`, 본 라운드 추가):
     - 디스크 `claim_coverage`: 3 strong slots (`장르`, `개발사`, `플랫폼`) + 2 missing slots (`엔진`, `난이도`) — slot 이름은 noisy 키워드(`출시일`/`2025`/`brunch`) 와 충돌 없이 future fixture reuse 보존
     - `renderSearchHistory` seed: `claim_coverage_summary: { strong: 3, weak: 0, missing: 2 }`
     - `.meta` exact text: `"사실 검증 교차 확인 3 · 미확인 2"`
     - `source_roles: ["백과 기반"]`
   - **dual-probe 변형** (`:2753`, 본 라운드 추가):
     - 디스크 `claim_coverage`: 1 strong slot (`개발사`) + 4 weak slots (`장르`, `플랫폼`, `서비스`, `출시일`) — CONTROL_SEQ 31/41 와 동일한 baseline distribution
     - `renderSearchHistory` seed: `claim_coverage_summary: { strong: 1, weak: 4, missing: 0 }`
     - `.meta` exact text: `"사실 검증 교차 확인 1 · 단일 출처 4"` — count line 자체가 ` · ` 구분자를 합법적으로 포함하므로 `not.toContainText("·")` blanket rule 은 사용하지 않음. exact `toHaveText` + answer-mode label negatives 로 충분
     - `source_roles: ["공식 기반", "백과 기반"]`
   - 기존 selector (`#search-history-box`, `.history-item`, `.history-item-actions button.secondary`, `.meta`) 와 `prepareSession`, `renderSearchHistory`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 entity-card actual-search / dual-probe post-click / follow-up / second follow-up 시나리오와 latest-update / store-seeded actual-search initial-render 시나리오는 **전혀 건드리지 않음** (handoff 지시)
2. **`tests/test_web_app.py` 는 전혀 건드리지 않음**
   - handoff 가 "keep existing service tests untouched unless you discover a concrete mismatch" 라고 명시했고, 기존 `tests/test_web_app.py:9473-9474` (baseline actual-search strong-plus-missing 회귀), `:9796` / `:9921` (baseline dual-probe mixed count-summary 회귀) 가 이미 두 분기의 server-side serialization 계약을 잠가둔 상태
   - 본 라운드는 그 service 회귀들을 semantic anchor 로만 활용해 browser 측 신규 시나리오가 동일한 non-empty count-summary 분기를 pre-click user-visible DOM 레벨에서 direct 하게 검증하는 구조를 취함
3. latest-update / zero-count / noisy latest-update / general / docs / pipeline 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_claim_coverage_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_card_history_card_reload_second_follow_up_preserves_mixed_count_summary` → 두 테스트 모두 `ok` (baseline actual-search 와 dual-probe 의 non-empty count-summary 계약이 post-click chain 에서 여전히 잠겨 있음을 재확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card .*initial-render.*(strong-plus-missing|mixed count-summary)" --reporter=line` → `2 passed (8.2s)` (두 신규 initial-render 시나리오가 정규식에 매칭되어 실행; 둘 다 `ok`)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 `tests/test_web_app.py` 를 전혀 건드리지 않았고, handoff 도 focused 두 service anchor 만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 entity-card initial-render 시나리오 두 개만 추가함
- 기존 entity-card post-click reload-only / follow-up / second follow-up / runtime-backed 시나리오 — handoff 는 이들을 그대로 두도록 명시함
- 기존 latest-update / store-seeded actual-search initial-render 시나리오 — handoff 는 본 라운드를 entity-card 가족의 non-empty count-summary 분기로 한정함

## 남은 리스크
- 두 브라우저 시나리오의 `toHaveText` exact 문자열은 `formatClaimCoverageCountSummary` 의 `"교차 확인 N · 단일 출처 N · 미확인 N"` 포맷 규약에 의존함. 포맷이 바뀌면 두 시나리오가 먼저 깨져 drift 를 빠르게 가리킴 — 같은 문자열이 다른 claim-coverage UI 에서도 사용 중이라 drift 범위는 런타임 전반과 동일
- 두 시나리오 모두 `renderSearchHistory` item 에 explicit non-empty `claim_coverage_summary` dict 를 시드하는 **의도된 설계** 임. 이는 기존 store-seeded actual-search / latest-update 가족의 zero-count dict branch 와는 **다른 렌더러 분기** (conditions 중 하나 이상이 true 인 경로) 를 exercise 함. 두 branch 모두 잠가야 `formatClaimCoverageCountSummary` 의 zero / non-zero 분기가 각각 drift-free 가 됨
- 두 시나리오는 어떤 `다시 불러오기` 클릭 / 자연어 reload / follow-up 도 수행하지 않음. Server interaction 없이 pure client-side 렌더러 분기만 잠그므로, 향후 server 측 시리얼라이저가 count-summary shape 를 바꾸면 본 시나리오는 그 변경을 즉시 잡지 못함. 그 drift 는 baseline service 회귀 (`:9473-9474`, `:9796`, `:9921`) 가 1차 방어를 담당하며, 본 시나리오들은 client-side renderer 의 non-empty count-summary branch 규약을 initial-render 단계에서 보완적으로 잠금
- actual-search 시나리오는 `.meta` exact text 가 `"사실 검증 교차 확인 3 · 미확인 2"` — 5 slot (3 strong + 2 missing) 이 각 N 값을 결정하므로 디스크 `claim_coverage` 배열이 바뀌면 exact 문자열도 바뀌어야 함. 본 시나리오는 exact text 를 `renderSearchHistory` client seed 와 일치시키므로 디스크 seed 와 client seed 가 서로 synced 되어야 함
- dual-probe 시나리오는 `.meta` exact text 가 `"사실 검증 교차 확인 1 · 단일 출처 4"` — count line 자체가 ` · ` 를 legitimately 포함해 `not.toContainText("·")` blanket rule 을 사용할 수 없음. 대신 exact `toHaveText` + answer-mode label negatives 로 충분하며, CONTROL_SEQ 31/41 에서 이미 입증된 패턴을 그대로 따름
- handoff 가 "service tests untouched unless a concrete mismatch" 라고 명시했고 본 라운드는 service 측을 건드리지 않아 CONTROL_SEQ 31/32/41/42/44/45/46/48/51-55 및 기존 entity-card / latest-update / store-seeded actual-search 회귀들의 잠금 상태를 그대로 유지함
- CONTROL_SEQ 53 (store-seeded actual-search zero-count initial-render) → CONTROL_SEQ 54 (latest-update non-noisy zero-count × 3) → CONTROL_SEQ 55 (latest-update noisy zero-count × 1) → 본 CONTROL_SEQ 56 (entity-card non-zero count-summary × 2) 루프는 렌더러의 `formatClaimCoverageCountSummary` 분기를 zero-count / non-zero 두 축 전반에 걸쳐 pre-click initial-render 단계에서 독립적으로 잠그는 진행 패턴으로, 본 라운드가 해당 contract 의 non-zero edge 를 entity-card 가족의 actual-search / dual-probe 두 variant 에서 완성함
- 시나리오를 두 개 신규 추가했으므로 기존 coverage 와 겹치지 않고 파일 내에서 entity-card 가족의 initial-render (actual-search) → initial-render (dual-probe) → post-click show-only reload 순서로 시각적으로 인접 배치됨
