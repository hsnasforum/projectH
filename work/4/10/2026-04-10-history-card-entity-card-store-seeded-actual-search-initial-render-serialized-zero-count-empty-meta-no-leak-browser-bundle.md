# history-card entity-card store-seeded actual-search initial-render serialized-zero-count empty-meta no-leak browser bundle

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 신규 브라우저 시나리오 `history-card entity-card store-seeded actual-search initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다` 를 기존 store-seeded 자연어 reload-only 시나리오 직전에 삽입. store-seeded 가족이 이제 **initial-render (serialized zero-count) → 자연어 reload-only → click-reload reload-only → click-reload first follow-up → click-reload second follow-up → 자연어 reload chain** 여섯 시나리오로 파일 내에서 인접 배치되도록 함. 이 신규 시나리오는 `다시 불러오기` 클릭 / 자연어 reload / follow-up 을 **전혀 수행하지 않고**, `renderSearchHistory` item 에 실제 server 가 serialize 하는 zero-count shape (`claim_coverage_summary: {strong:0, weak:0, missing:0}`, `claim_coverage_progress_summary: ""`) 를 직접 시드해 renderer 의 formatClaimCoverageCountSummary 분기 (`{0,0,0}` → empty string → empty detailLines → no `.meta`) 를 user-visible 로 잠그는 bounded browser 회귀임
- `tests/test_web_app.py` 는 전혀 건드리지 않음 (handoff 지시에 따라 `tests/test_web_app.py:17179`, `:17266-17279`, `:10981` 을 semantic anchor 로만 활용)

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-store-seeded-actual-search-natural-reload-only-empty-meta-no-leak-browser-bundle.md`, CONTROL_SEQ 52) 는 store-seeded actual-search 가족의 **natural-reload-only** edge 를 browser 측에서 독립적으로 잠갔음
- 기존 store-seeded 가족의 browser 시나리오 다섯 개 (자연어 reload-only, click-reload reload-only, click-reload first follow-up, click-reload second follow-up, 자연어 reload chain) 는 모두 어떤 reload 나 follow-up 단계에서 `.meta toHaveCount(0)` 를 검증했으나, **user-visible initial-render (pre-click) 단계에서 실제 server 가 내는 serialized zero-count shape 를 그대로 받아도 `.meta` 가 생성되지 않음** 을 user-visible 로 exercise 하는 회귀는 없었음
- 기존 다섯 시나리오는 모두 `renderSearchHistory` item 에 `claim_coverage_summary` / `claim_coverage_progress_summary` 를 **전혀 seed 하지 않는** 방식을 사용함. 이는 `undefined` 입력 경로 (`formatClaimCoverageCountSummary(undefined)`, `(undefined || "").trim()`) 를 exercise 하지만, 실제 서버가 내는 **explicit zero-count dict** 경로 (`formatClaimCoverageCountSummary({strong:0, weak:0, missing:0})` — 각 counts 가 존재하지만 전부 0 이라 조건문을 통과 못해 parts 가 비어 빈 문자열을 내는 분기) 를 직접 exercise 하지 못함
- `storage/web_search_store.py:316` 의 `_summarize_claim_coverage` 는 `claim_coverage` 가 비어 있을 때 `{strong:0, weak:0, missing:0}` 을 emit 하고, `app/serializers.py:280-287` 은 이 dict 를 `CoverageStatus.STRONG/WEAK/MISSING` key 로 재직렬화해 `session.web_search_history` 에 그대로 전달함. Frontend 는 이 dict 를 `claim_coverage_summary` 필드에 받고, `app/static/app.js:2954-2960` 의 `formatClaimCoverageCountSummary` 가 `Number(normalized.strong || 0) > 0` 등 세 조건을 모두 false 로 판정해 `parts = []` → `parts.join(" · ") === ""` 을 반환하고, `detailLines.push(...)` 가 실행되지 않아 `.meta` 가 생성되지 않는 분기를 지남
- 따라서 기존 `undefined` seed 경로와 본 라운드의 explicit zero-count dict seed 경로는 **서로 다른 branch** 를 exercise 하며, 두 branch 모두에서 `.meta toHaveCount(0)` 이 성립해야 store-seeded actual-search 가족의 empty-meta no-leak 계약이 user-visible 로 완전히 잠김
- 이 슬라이스는 service refactor 없이 store-seeded 가족에 initial-render 분기를 exercise 하는 bounded browser 회귀 한 개를 추가하는 범위임. runtime-backed strong-plus-missing / dual-probe / zero-strong / latest-update / noisy / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오**
   - 신규 테스트 이름: `history-card entity-card store-seeded actual-search initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
   - 기존 store-seeded 자연어 reload-only 시나리오 (CONTROL_SEQ 52 에서 추가) 직전에 삽입해 store-seeded 가족이 initial-render → 자연어 reload-only → click-reload reload-only → first follow-up → second follow-up → 자연어 reload chain 여섯 시나리오로 파일 내에서 인접 배치되도록 함
   - 구조:
     - 디스크 record 에 `claim_coverage: []` + 빈 `claim_coverage_progress_summary` 시드 (기존 store-seeded 가족과 동일한 stored record 모양)
     - `renderSearchHistory` item 에 **실제 server 가 serialize 하는 zero-count shape 를 직접 시드**:
       - `claim_coverage_summary: { strong: 0, weak: 0, missing: 0 }`
       - `claim_coverage_progress_summary: ""`
     - 이는 기존 다섯 시나리오의 "seed 생략" 전략과 **의도적으로 다름** — 기존 다섯 시나리오가 `undefined` 입력 경로를 exercise 하는 반면, 본 시나리오는 explicit zero-count dict 입력 경로를 exercise 함
     - **`다시 불러오기` 클릭 / 자연어 reload / follow-up 을 전혀 수행하지 않음**
     - pre-click 어서션:
       - `#search-history-box` visible
       - history item 의 `button.secondary` 가 `"다시 불러오기"` 텍스트 포함 (history item 자체는 정상 렌더링됨을 확인)
     - 신규 empty-meta no-leak 어서션 (pre-click 단계에서 바로):
       - `historyCard.locator(".meta") toHaveCount(0)` — serialized zero-count shape 를 받아도 detail `.meta` 가 전혀 생성되지 않음
       - `historyCard not.toContainText("사실 검증")` — accidental `.meta` creation 으로 count line 이 leak 되는 경우 방어 double-guard
   - 기존 selector (`#search-history-box`, `.history-item`, `.history-item-actions button.secondary`, `.meta`) 와 `prepareSession`, `renderSearchHistory`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 store-seeded 자연어 reload-only / click-reload reload-only / first follow-up / second follow-up / 자연어 reload chain 시나리오와 runtime-backed actual-search 시나리오는 **전혀 건드리지 않음** (handoff 지시)
2. **`tests/test_web_app.py` 는 전혀 건드리지 않음**
   - handoff 가 "keep existing service tests untouched unless you discover a concrete mismatch" 라고 명시했고, 기존 `tests/test_web_app.py:17179` (store-seeded natural-reload chain 회귀), `:17266-17279` (다른 stage 의 `_assert_empty_meta_continuity` 호출), `:10981` (`test_web_search_store_list_summaries_includes_claim_coverage_summary` — `_summarize_claim_coverage([])` 이 `{0,0,0}` 을 emit 함을 잠그는 generic anchor) 가 이미 server 측 serialized zero-count 계약을 잠그고 있어 mismatch 가 없음
   - 본 라운드는 그 service 회귀들을 semantic anchor 로만 활용해 browser 측 신규 시나리오가 동일한 zero-count 분기를 user-visible DOM 레벨에서 direct 하게 검증하는 구조를 취함
3. runtime-backed strong-plus-missing / dual-probe / zero-strong / latest-update / noisy / general / docs / pipeline 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary` → `ok` (`WebSearchStore.list_session_record_summaries` 가 `claim_coverage` 없는 record 에 대해 `{strong:0, weak:0, missing:0}` 을 emit 하는 service 계약이 그대로 유지됨을 재확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "store-seeded actual-search.*initial-render.*empty-meta|store-seeded actual-search.*pre-click.*empty-meta" --reporter=line` → `1 passed (5.5s)` (신규 initial-render 시나리오 한 개가 정규식에 매칭되어 실행; `ok`)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 `tests/test_web_app.py` 를 전혀 건드리지 않았고, handoff 도 focused service anchor 한 개만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 store-seeded initial-render 시나리오 한 개만 추가함
- 기존 runtime-backed actual-search / click-reload reload-only / first/second follow-up / 자연어 reload-only / 자연어 reload chain / dual-probe / zero-strong / latest-update / noisy / general 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 false-fail 됨. 같은 가정이 이전 latest-update / store-seeded reload-only / first/second follow-up / 자연어 reload chain 라운드들에서도 이미 사용 중이라 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 badge/summary 영역에서 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- 본 시나리오는 `renderSearchHistory` item 에 explicit zero-count `claim_coverage_summary: {strong:0, weak:0, missing:0}` 를 시드하는 **의도된 설계** 임. 이는 기존 store-seeded 가족의 다섯 시나리오가 사용하는 `undefined` 생략 패턴과는 **다른 branch** 를 exercise 함. 두 branch 모두를 잠가야 `formatClaimCoverageCountSummary` 의 `undefined` 분기와 explicit zero dict 분기가 각각 drift-free 가 됨. 향후 frontend 가 `formatClaimCoverageCountSummary` 의 `normalized && typeof normalized === "object"` 검사를 바꾸거나 `Number(...) > 0` 분기 로직을 바꾸면 두 시나리오 중 하나가 먼저 깨짐 — 의도된 failure-first 설계
- 이 시나리오는 어떤 `다시 불러오기` 클릭 / 자연어 reload / follow-up 도 수행하지 않음. Server interaction 없이 pure client-side 렌더러 분기만 잠그므로, 향후 server 측 시리얼라이저가 zero-count shape 를 바꾸더라도 본 시나리오는 그 변경을 즉시 잡지 못함. 그 드리프트는 `test_web_search_store_list_summaries_includes_claim_coverage_summary` 와 `_assert_empty_meta_continuity` service 회귀들이 1차 방어를 담당하며, 본 시나리오는 client-side `.meta` 렌더링 규약을 보완적으로 잠금
- 기존 store-seeded 다섯 시나리오 (undefined 경로) 와 본 라운드의 initial-render 시나리오 (explicit zero-count dict 경로) 는 같은 stored record 모양을 공유하고, 파일 내에서 여섯 가지 user-visible edge (initial-render / 자연어 reload-only / click-reload reload-only / first follow-up / second follow-up / 자연어 reload chain) 가 인접 배치되어 각 edge 별 no-leak 계약이 서로 보완함
- handoff 가 "service tests untouched unless a concrete mismatch" 라고 명시했고 본 라운드는 service 측을 건드리지 않아 CONTROL_SEQ 45/46/48/51/52 의 잠금 상태를 그대로 유지함. 향후 service 측에서 `_assert_empty_meta_continuity` 가 다른 stage 로 확장되거나 initial-render 별도 regression 으로 분리될 필요가 생기면 별도 라운드에서 다룰 수 있음
- CONTROL_SEQ 51 (click-reload reload-only) → CONTROL_SEQ 52 (자연어 reload-only) → 본 CONTROL_SEQ 53 (initial-render serialized zero-count) 루프는 store-seeded actual-search 가족의 "**바로 정지**" 혹은 "**interaction 전 상태**" user-visible contract 를 click-reload / natural-reload / initial-render 세 경로에서 독립적으로 잠그는 진행 패턴으로, 동일 가족의 early-stage edge 계약이 이 라운드로 browser-side 에서 완전히 닫힘
- 시나리오를 신규 추가했으므로 기존 coverage 와 겹치지 않고 파일 내에서 store-seeded 가족이 여섯 시나리오로 인접 배치되어 향후 reader 가 initial-render → 자연어 reload-only → click-reload reload-only → first follow-up → second follow-up → 자연어 reload chain 의 점진적 user interaction 구조를 시각적으로 구분할 수 있음
