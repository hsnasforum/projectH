# history-card entity-card noisy single-source initial-render strong-plus-missing meta browser bundle

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 신규 브라우저 시나리오 `history-card entity-card noisy single-source initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다` 를 기존 noisy entity-card show-only reload 시나리오 (`:2503`) 직전에 삽입. 디스크 record 에 noisy single-source blog (`blog.example.com/crimson-desert`) 를 `results` 에 포함하되 `source_roles` 는 `["백과 기반"]` 로 이미 excluded 된 shipped 상태를 재현. `claim_coverage` 에 3 strong (`장르`/`개발사`/`플랫폼`) + 2 missing (`엔진`/`난이도`) slot 을 시드하고, `renderSearchHistory` item 에 `claim_coverage_summary: {strong:3, weak:0, missing:2}` + 빈 progress 를 explicit 하게 시드. `다시 불러오기` / 자연어 reload / follow-up 을 **전혀 수행하지 않고** pre-click 상태에서 reload button 텍스트 + noisy 키워드 (`출시일`/`2025`/`blog.example.com`) 부정 + `historyCardMeta.toHaveCount(1)` + `toHaveText("사실 검증 교차 확인 3 · 미확인 2")` + answer-mode label 누출 부정 어서션을 잠금
- `tests/test_web_app.py` 는 전혀 건드리지 않음 (handoff 지시에 따라 `tests/test_web_app.py:19457`, `:19532`, `:19611`, `:19687` 을 semantic anchor 로만 활용)

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-initial-render-strong-plus-missing-plus-mixed-count-summary-meta-browser-bundle.md`, CONTROL_SEQ 56) 는 entity-card 가족의 **non-noisy** 변형 두 개 (actual-search strong-plus-missing, dual-probe mixed count-summary) 에 대한 initial-render 단계 non-empty count-summary meta 계약을 browser 측에서 독립적으로 잠갔음
- handoff 는 "Do not keep shrinking the already-closed non-noisy initial-render family" 라고 명시하고, 가장 인접한 next user-visible gap 으로 **noisy entity-card** 가족의 initial-render 단계에서 shipped strong-plus-missing meta 분기를 지목함
- 기존 noisy entity-card 가족의 브라우저 시나리오들은 strong-plus-missing 분기를 post-click 단계에서만 잠갔음:
  - `:2503` show-only reload 이후 provenance/exclusion 만 잠금 (count-summary `.meta` exact text 는 post-click 경로에서만)
  - `:9548`, `:9620` 자연어 reload follow-up / second follow-up
  - `:9695`, `:9798` click-reload follow-up / second follow-up
- 이들 post-click 시나리오는 이미 noisy strong-plus-missing branch 의 `.meta === "사실 검증 교차 확인 3 · 미확인 2"` 를 잠갔으나, **pre-click initial-render** 상태에서 shipped non-empty count-summary dict + noisy-filtered source_roles 를 받아도 `.meta` 가 정확히 rendering 됨을 user-visible 로 exercise 하는 회귀는 없었음
- `storage/web_search_store.py:316` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 의 렌더러 경로는 investigation entity_card 에서 answer-mode label 을 skip 하고, `formatClaimCoverageCountSummary({strong:3, weak:0, missing:2})` = `"교차 확인 3 · 미확인 2"` 를 내므로 `.meta` 는 `사실 검증 교차 확인 3 · 미확인 2` 한 줄이어야 함. noisy 가족에서도 동일 렌더러 분기가 적용되며 noisy exclusion 은 `source_roles` 에서 이미 처리된 상태여야 함
- 본 슬라이스는 service refactor 없이 bounded browser 회귀 한 개를 추가해 noisy entity-card 가족의 initial-render 단계에서 `.meta` exact text + noisy source exclusion 두 계약을 동시에 잠그는 범위임. latest-update / dual-probe / zero-count / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오**
   - 신규 테스트 이름: `history-card entity-card noisy single-source initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다`
   - 기존 noisy entity-card show-only reload 시나리오 (`:2503`) 직전에 삽입해 noisy entity-card 가족이 initial-render → post-click show-only reload → 자연어/click-reload follow-up 체인 순서로 파일 내에서 인접 배치되도록 함
   - 구조:
     - 디스크 record 에 noisy single-source blog (`blog.example.com/crimson-desert`) 를 `results` 에 포함하되 `source_roles` 는 `["백과 기반"]` 로 좁혀 noisy exclusion 이 serialization 시점에 이미 적용된 상태를 재현
     - `claim_coverage` 에 3 strong slot (`장르`/`개발사`/`플랫폼`) + 2 missing slot (`엔진`/`난이도`) 를 시드. slot 이름은 noisy 키워드(`출시일`/`2025`/`brunch`/`blog.example.com`) 와 충돌하지 않도록 의도적으로 선택함
     - `renderSearchHistory` item 에 shipped non-empty count-summary 를 explicit 하게 시드:
       - `claim_coverage_summary: { strong: 3, weak: 0, missing: 2 }`
       - `claim_coverage_progress_summary: ""`
       - `verification_label: "설명형 다중 출처 합의"`
       - `source_roles: ["백과 기반"]` (noisy-filtered)
     - **`다시 불러오기` 클릭 / 자연어 reload / follow-up 을 전혀 수행하지 않음**
     - pre-click 어서션:
       - `#search-history-box` visible
       - `historyCard.locator(".history-item-actions button.secondary")` 가 `"다시 불러오기"` 텍스트 포함
       - `historyCard not.toContainText("출시일")` — noisy 단일-source claim 키워드 누출 방지
       - `historyCard not.toContainText("2025")` — noisy 단일-source 연도 키워드 누출 방지
       - `historyCard not.toContainText("blog.example.com")` — noisy source domain 누출 방지
     - `.meta` 어서션:
       - `historyCardMeta.toHaveCount(1)`
       - `historyCardMeta.toHaveText("사실 검증 교차 확인 3 · 미확인 2")`
       - `historyCardMeta.not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색"` — investigation card 는 answer-mode label skip
   - 기존 selector (`#search-history-box`, `.history-item`, `.history-item-actions button.secondary`, `.meta`) 와 `prepareSession`, `renderSearchHistory`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 noisy entity-card post-click show-only reload / 자연어 reload follow-up / click-reload follow-up 시나리오와 non-noisy entity-card initial-render / store-seeded actual-search initial-render / latest-update initial-render 시나리오는 **전혀 건드리지 않음** (handoff 지시)
2. **`tests/test_web_app.py` 는 전혀 건드리지 않음**
   - handoff 가 "keep existing service tests untouched unless you discover a concrete mismatch" 라고 명시했고, 기존 `tests/test_web_app.py:19457`, `:19532`, `:19611`, `:19687` 의 noisy entity-card 회귀들이 이미 strong-plus-missing count-summary + 빈 progress + noisy source exclusion 을 post-reload/follow-up 단계에서 잠가둔 상태
   - 본 라운드는 그 service 회귀들을 semantic anchor 로만 활용해 browser 측 신규 시나리오가 동일한 non-empty count-summary + noisy-filtered source_roles 분기를 pre-click user-visible DOM 레벨에서 direct 하게 검증하는 구조를 취함
3. latest-update / dual-probe / zero-count / general / docs / pipeline 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up` → 두 테스트 모두 `ok` (baseline noisy entity-card 의 strong-plus-missing + exclusion 계약이 post-click chain 에서 여전히 잠겨 있음을 재확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy .*initial-render.*strong-plus-missing|history-card entity-card noisy .*initial-render.*strong-plus-missing" --reporter=line` → `1 passed (5.3s)` (신규 noisy entity-card initial-render 시나리오 한 개가 정규식에 매칭되어 실행; `ok`)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 `tests/test_web_app.py` 를 전혀 건드리지 않았고, handoff 도 focused 두 service anchor 만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 noisy entity-card initial-render 시나리오 한 개만 추가함
- 기존 noisy entity-card post-click / non-noisy entity-card initial-render / runtime-backed / latest-update / store-seeded actual-search 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 신규 브라우저 시나리오의 `toHaveText("사실 검증 교차 확인 3 · 미확인 2")` exact 문자열은 `formatClaimCoverageCountSummary({strong:3, weak:0, missing:2})` 의 `"교차 확인 3 · 미확인 2"` 포맷 규약에 의존함. 포맷이 바뀌면 시나리오가 먼저 깨져 drift 를 빠르게 가리킴 — 같은 문자열이 다른 claim-coverage UI 에서도 사용 중이라 drift 범위는 런타임 전반과 동일
- `not.toContainText("출시일")` / `"2025"` / `"blog.example.com")` guard 는 noisy single-source 가 serialization 단계에서 이미 source_roles 에서 제외되어 history card 의 badge row / 제목 / summary head 어디에서도 등장하지 않는다는 현재 계약에 의존함. 향후 noisy source 표시 정책이 바뀌면 이 세 guard 가 함께 조정되어야 함
- slot 이름은 `엔진`/`난이도` 로 선택해 noisy 키워드 (`출시일`/`2025`/`brunch`/`blog.example.com`) 와 충돌하지 않도록 함. 이 설계 덕분에 seeded claim-coverage 행이 noisy exclusion assertion 과 충돌하지 않음. 향후 noisy 키워드 목록이 확장되면 slot 이름도 함께 재검토해야 함
- 본 시나리오는 `renderSearchHistory` item 에 explicit non-empty `claim_coverage_summary: {strong:3, weak:0, missing:2}` 를 시드하는 **의도된 설계** 임. 이는 CONTROL_SEQ 53/54/55 의 zero-count dict branch 와는 다른 렌더러 분기 (conditions 중 하나 이상이 true 인 경로) 를 exercise 하며, CONTROL_SEQ 56 의 non-noisy entity-card initial-render 시나리오들과 동일한 non-zero branch 를 noisy 가족의 필터된 source_roles 맥락에서 잠금
- 이 시나리오는 어떤 user interaction 도 수행하지 않으므로, 향후 server 측 noisy source filtering 이나 count-summary serialization 이 바뀌면 본 시나리오는 그 변경을 즉시 잡지 못함. 그 drift 는 noisy entity-card service 회귀들 (`:19457`, `:19532`, `:19611`, `:19687`) 이 1차 방어를 담당하며, 본 시나리오는 client-side `.meta` exact text + noisy source exclusion 규약을 initial-render 단계에서 보완적으로 잠금
- 기존 noisy entity-card post-click 시나리오 다섯 개와 본 라운드의 initial-render 시나리오는 같은 stored record 모양 (noisy single-source 가 results 에 포함되지만 source_roles 에서는 제외) 과 같은 count-summary 분포를 공유하고, 파일 내에서 initial-render → post-click show-only reload → 자연어 reload follow-up / second follow-up → click-reload follow-up / second follow-up 순서로 확장되는 noisy 가족의 user-visible meta 계약이 single file 안에서 end-to-end 로 보완됨
- handoff 가 "service tests untouched unless a concrete mismatch" 라고 명시했고 본 라운드는 service 측을 건드리지 않아 CONTROL_SEQ 31/32/41/42/44-56 및 기존 noisy entity-card 회귀들의 잠금 상태를 그대로 유지함
- CONTROL_SEQ 56 (entity-card non-noisy initial-render × 2) → 본 CONTROL_SEQ 57 (entity-card noisy single-source initial-render × 1) 루프는 "**explicit non-empty count-summary dict branch at pre-click render time**" user-visible contract 를 entity-card 가족의 non-noisy actual-search / dual-probe / noisy single-source 세 변형에 걸쳐 독립적으로 잠그는 진행 패턴임. 렌더러의 non-zero branch 가 다양한 verification_label / source_roles / noisy-exclusion 조합에서 drift-free 함을 확인함
- 시나리오를 한 개 신규 추가했으므로 기존 coverage 와 겹치지 않고 파일 내에서 noisy entity-card 가족이 initial-render → post-click show-only reload → 자연어/click-reload follow-up 순서로 시각적으로 인접 배치됨
