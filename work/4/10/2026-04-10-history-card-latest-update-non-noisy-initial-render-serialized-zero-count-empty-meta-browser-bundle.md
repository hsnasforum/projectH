# history-card latest-update non-noisy initial-render serialized-zero-count empty-meta browser bundle

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 기존 latest-update non-noisy show-only reload 시나리오(`e2e/tests/web-smoke.spec.mjs:2801` mixed-source) 직전에 세 개의 신규 initial-render 시나리오를 한 블록으로 삽입:
  - `history-card latest-update mixed-source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
  - `history-card latest-update single-source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
  - `history-card latest-update news-only initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
  - 세 시나리오 모두 디스크 record 에 `claim_coverage: []` + 빈 progress 를 시드하고, `renderSearchHistory` item 에 실제 server 가 emit 하는 `claim_coverage_summary: {strong:0, weak:0, missing:0}` + `claim_coverage_progress_summary: ""` 를 explicit 하게 시드한 뒤 `다시 불러오기` / 자연어 reload / follow-up 을 **전혀 수행하지 않고** pre-click 상태에서 `historyCard.locator(".meta") toHaveCount(0)` + `historyCard not.toContainText("사실 검증")` 을 잠금
- `tests/test_web_app.py` 는 전혀 건드리지 않음 (handoff 지시대로 `tests/test_web_app.py:10981`, `:8156`, `:8250`, `:8333` 을 semantic anchor 로만 활용)

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-store-seeded-actual-search-initial-render-serialized-zero-count-empty-meta-no-leak-browser-bundle.md`, CONTROL_SEQ 53) 는 store-seeded actual-search 가족의 initial-render 단계에서 serialized zero-count shape 를 직접 받는 경로의 empty-meta no-leak 계약을 browser 측에서 독립적으로 잠갔음
- handoff 는 "Do not keep shrinking the same closed family into artificial micro-slices" 라고 명시하고, 가장 인접한 next user-visible gap 으로 latest-update non-noisy (mixed-source / single-source / news-only) 가족의 initial-render 단계를 지목함
- 기존 latest-update non-noisy 가족의 브라우저 시나리오 (`:2801`, `:2919`, `:3024`) 는 **post-click** (show-only reload / follow-up) 단계에서 badge / origin / source-path continuity 를 잠그지만, **pre-click initial-render** 상태에서 실제 server 가 내는 serialized zero-count shape (`{strong:0, weak:0, missing:0}` + 빈 progress) 를 받아도 `.meta` 가 생성되지 않음을 user-visible 로 exercise 하는 회귀는 없었음
- `storage/web_search_store.py:316` 의 `_summarize_claim_coverage` 는 `claim_coverage` 가 비어 있을 때 `{strong:0, weak:0, missing:0}` 을 emit 하고, `app/serializers.py:280-287` 은 이 dict 를 `CoverageStatus.STRONG/WEAK/MISSING` key 로 재직렬화해 `session.web_search_history` 에 전달함. `app/static/app.js:2954-2960` 의 `formatClaimCoverageCountSummary` 는 `Number(normalized.strong || 0) > 0` 등 세 조건을 모두 false 로 판정해 `parts = []` → `parts.join(" · ") === ""` 를 반환하고, `detailLines.push(...)` 가 실행되지 않아 `.meta` 가 생성되지 않는 분기를 지남
- 이 렌더러 분기는 store-seeded actual-search 가족에서 CONTROL_SEQ 53 이 exercise 하는 것과 **동일한 explicit zero-count dict branch** 임. latest-update 는 entity_card 가 아닌 `latest_update` answer_mode 를 가지지만, 렌더러의 `isInvestigation` 분기는 두 answer_mode 를 동일하게 취급해 detailLines 에서 answer-mode label 을 skip 함. 따라서 latest-update 세 non-noisy 변형에서도 동일한 empty-meta no-leak 이 성립해야 함
- 본 슬라이스는 service refactor 없이 세 개의 bounded browser 회귀를 한 bundle 로 추가해 latest-update non-noisy 가족의 initial-render 단계에서 user-visible empty-meta no-leak 계약을 독립적으로 잠그는 범위임. 기존 latest-update 시나리오 (show-only reload / follow-up 가족) 와 runtime-backed 계열은 전혀 건드리지 않음. noisy latest-update / entity-card / dual-probe / zero-strong / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`e2e/tests/web-smoke.spec.mjs` 세 개의 신규 initial-render 시나리오**
   - 세 시나리오 모두 다음 공통 패턴을 따름:
     - 디스크 record 에 `claim_coverage: []` + 빈 `claim_coverage_progress_summary` 시드
     - `response_origin`: `provider: "web"`, `badge: "WEB"`, `label: "웹 검색"`, `answer_mode: "latest_update"`, 그리고 각 변형별 `verification_label` / `source_roles`
     - `renderSearchHistory` item 에 실제 server 가 emit 하는 `claim_coverage_summary: { strong: 0, weak: 0, missing: 0 }` + `claim_coverage_progress_summary: ""` 를 explicit 하게 시드
     - **`다시 불러오기` 클릭 / 자연어 reload / follow-up 을 전혀 수행하지 않음**
     - pre-click 어서션:
       - `#search-history-box` visible
       - `historyCard.locator(".history-item-actions button.secondary")` 가 `"다시 불러오기"` 텍스트 포함
     - 신규 empty-meta no-leak 어서션:
       - `historyCard.locator(".meta") toHaveCount(0)`
       - `historyCard not.toContainText("사실 검증")`
   - 변형별 차이:
     - **mixed-source**: `verification_label: "공식+기사 교차 확인"`, `source_roles: ["보조 기사", "공식 기반"]`, 두 results (`store.steampowered.com`, `yna.co.kr`)
     - **single-source**: `verification_label: "단일 출처 참고"`, `source_roles: ["보조 출처"]`, 한 result (`example.com/seoul-weather`)
     - **news-only**: `verification_label: "기사 교차 확인"`, `source_roles: ["보조 기사"]`, 두 results (`hankyung.com/economy/2025`, `mk.co.kr/economy/2025`)
   - 기존 selector (`#search-history-box`, `.history-item`, `.history-item-actions button.secondary`, `.meta`) 와 `prepareSession`, `renderSearchHistory`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 latest-update post-click / follow-up / runtime-backed / noisy 시나리오는 **전혀 건드리지 않음** (handoff 지시)
2. **`tests/test_web_app.py` 는 전혀 건드리지 않음**
   - handoff 가 "keep existing service tests untouched unless you discover a concrete mismatch" 라고 명시했고, 기존 `tests/test_web_app.py:10981` (`test_web_search_store_list_summaries_includes_claim_coverage_summary`) 가 `_summarize_claim_coverage([])` 의 `{strong:0, weak:0, missing:0}` 계약을 이미 잠그고, `:8156` / `:8250` / `:8333` 의 세 variant 에 대한 reload exact-fields 회귀들이 serialized zero-count + 빈 progress 를 post-reload 단계에서 이미 잠가둔 상태
   - 본 라운드는 그 service 회귀들을 semantic anchor 로만 활용해 browser 측 신규 시나리오가 동일한 zero-count 분기를 pre-click user-visible DOM 레벨에서 direct 하게 검증하는 구조를 취함
3. noisy latest-update / entity-card / dual-probe / zero-strong / general / docs / pipeline 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary` → `ok` (generic semantic anchor 가 `_summarize_claim_coverage([])` → `{strong:0, weak:0, missing:0}` 계약을 여전히 잠그고 있음을 재확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update .*initial-render.*empty-meta|latest-update .*pre-click.*empty-meta" --reporter=line` → `3 passed (10.4s)` (mixed-source / single-source / news-only 세 신규 시나리오 모두 정규식에 매칭되어 실행; 셋 다 `ok`)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 `tests/test_web_app.py` 를 전혀 건드리지 않았고, handoff 도 focused service anchor 한 개만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 latest-update initial-render 시나리오 세 개만 추가함
- 기존 latest-update post-click show-only reload / follow-up / runtime-backed / noisy 시나리오 — handoff 는 이들을 그대로 두도록 명시함
- 기존 store-seeded actual-search initial-render / reload-only / follow-up / chain 시나리오 — handoff 는 본 라운드를 latest-update 가족으로 한정함

## 남은 리스크
- 세 신규 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 전부 false-fail 됨. 같은 가정이 이전 latest-update / store-seeded actual-search 가족의 empty-meta 라운드들에서도 이미 사용 중이라 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역 (badge row, 제목, summary head) 이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 재사용하면 세 시나리오가 동시에 false-fail 하므로 함께 조정해야 함
- 세 시나리오 모두 `renderSearchHistory` item 에 explicit zero-count `claim_coverage_summary: {strong:0, weak:0, missing:0}` 를 시드하는 **의도된 설계** 임. 이는 store-seeded actual-search 가족의 기존 다섯 시나리오 (undefined 생략 경로) 와는 **다른 렌더러 분기** 를 exercise 함. 두 branch 모두 잠가야 `formatClaimCoverageCountSummary` 의 `undefined` 분기와 explicit zero dict 분기가 각각 drift-free 가 됨. 본 라운드는 latest-update 가족에서 explicit zero dict 분기만 잠그며, undefined 생략 경로는 이미 post-click 시나리오들이 exercise 하는 구조와 양립함
- 세 시나리오 모두 어떤 user interaction 도 수행하지 않으므로, 향후 server 측 시리얼라이저가 zero-count shape 를 바꾸더라도 본 시나리오는 그 변경을 즉시 잡지 못함. 그 드리프트는 `test_web_search_store_list_summaries_includes_claim_coverage_summary` 와 `test_handle_chat_*_latest_update_reload_exact_fields` service 회귀들이 1차 방어를 담당하며, 본 시나리오들은 client-side renderer 의 explicit-zero-dict branch 규약을 보완적으로 잠금
- 기존 latest-update post-click 시나리오 (`:2801`, `:2919`, `:3024` → 본 라운드 이후 각각 다섯 라인 밀림) 와 본 라운드의 세 pre-click initial-render 시나리오는 같은 stored record 모양을 공유하고, 파일 내에서 initial-render (mixed) → initial-render (single) → initial-render (news) → post-click show-only reload (mixed) → ... 순서로 인접 배치되어 pre-click vs post-click 단계의 no-leak 계약이 서로 보완함
- handoff 가 "service tests untouched unless a concrete mismatch" 라고 명시했고 본 라운드는 service 측을 건드리지 않아 CONTROL_SEQ 45/46/48/51/52/53 및 기존 latest-update reload exact-fields 회귀들의 잠금 상태를 그대로 유지함
- CONTROL_SEQ 53 (store-seeded actual-search initial-render) → 본 CONTROL_SEQ 54 (latest-update non-noisy initial-render) 루프는 "**explicit zero-count dict branch at pre-click render time**" user-visible contract 를 store-seeded actual-search 가족에서 latest-update non-noisy 가족으로 확장하는 진행 패턴으로, 두 가족 모두에서 렌더러의 동일 분기가 독립적으로 잠겨 drift 가 감지됨
- 시나리오를 세 개 신규 추가했으므로 기존 coverage 와 겹치지 않고 파일 내에서 latest-update 가족의 pre-click initial-render → post-click show-only reload / follow-up 단계가 시각적으로 인접 배치됨
