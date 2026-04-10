# history-card latest-update noisy initial-render serialized-zero-count empty-meta browser bundle

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 신규 브라우저 시나리오 `history-card latest-update noisy community source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다` 를 기존 noisy latest-update post-click 시나리오 (`history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다`) 직전에 삽입. 디스크 record 에 `claim_coverage: []` + 빈 progress 를 시드하고, `renderSearchHistory` item 에 실제 server 가 emit 하는 `claim_coverage_summary: {strong:0, weak:0, missing:0}` + `claim_coverage_progress_summary: ""` 를 explicit 하게 시드한 뒤, `다시 불러오기` / 자연어 reload / follow-up 을 **전혀 수행하지 않고** pre-click 상태에서 `reloadButton.toHaveText("다시 불러오기")` + `historyCard not.toContainText("보조 커뮤니티")` + `historyCard not.toContainText("brunch")` + `historyCard.locator(".meta") toHaveCount(0)` + `historyCard not.toContainText("사실 검증")` 을 잠금
- `tests/test_web_app.py` 는 전혀 건드리지 않음 (handoff 지시에 따라 `tests/test_web_app.py:10981`, `:11565`, `:11675`, `:11792`, `:19206`, `:19284`, `:19360`, `:19437` 을 semantic anchor 로만 활용)

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-latest-update-non-noisy-initial-render-serialized-zero-count-empty-meta-browser-bundle.md`, CONTROL_SEQ 54) 는 latest-update **non-noisy** 가족의 세 변형 (mixed-source / single-source / news-only) 에 대한 initial-render 단계 serialized zero-count empty-meta no-leak 계약을 browser 측에서 독립적으로 잠갔음
- handoff 는 "Do not keep shrinking the already-closed non-noisy family into more docs-only or note-only micro-slices" 라고 명시하고, 가장 인접한 next user-visible gap 으로 **noisy** latest-update 가족의 initial-render 단계를 지목함
- 기존 noisy latest-update 가족의 브라우저 시나리오들은 post-click 단계에서 badge / origin / source-path / 본문 exclusion continuity 를 잠그지만 (show-only reload, 자연어 reload + first/second follow-up, click-reload + first/second follow-up), **pre-click initial-render** 상태에서 실제 server 가 내는 serialized zero-count shape (`{strong:0, weak:0, missing:0}` + 빈 progress) 를 받아도 `.meta` 가 생성되지 않음을 user-visible 로 exercise 하는 회귀는 없었음
- `storage/web_search_store.py:316` 의 `_summarize_claim_coverage` 는 `claim_coverage` 가 비어 있을 때 `{strong:0, weak:0, missing:0}` 을 emit 하고, `app/serializers.py:280-287` 은 이 dict 를 그대로 직렬화함. `app/static/app.js:2954-2960` 의 `formatClaimCoverageCountSummary` 는 세 counts 가 전부 0 이므로 `parts = []` → `parts.join(" · ") === ""` 를 반환하고, `detailLines.push(...)` 가 실행되지 않아 `.meta` 가 생성되지 않는 분기를 지남
- 이 렌더러 분기는 CONTROL_SEQ 53 (store-seeded actual-search) 와 CONTROL_SEQ 54 (latest-update non-noisy 세 변형) 가 exercise 하는 것과 **동일한 explicit zero-count dict branch** 이며, 본 라운드는 동일 branch 를 **noisy latest-update** 가족의 pre-click 경로로도 확장해 렌더러의 해당 분기가 가족별 source_roles / noisy exclusion 규약과 무관하게 항상 `.meta` 를 생성하지 않음을 명시적으로 잠금
- 본 슬라이스는 service refactor 없이 bounded browser 회귀 한 개를 추가하는 범위임. noisy latest-update 가족의 post-click 시나리오들과 entity-card / dual-probe / zero-strong / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오**
   - 신규 테스트 이름: `history-card latest-update noisy community source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다`
   - 기존 noisy latest-update post-click 시나리오 (`:2250` → 본 라운드 이후 한 scenario 밀림) 직전에 삽입해 noisy latest-update 가족이 initial-render → post-click show-only reload (본문/origin/context noisy exclusion) 순서로 파일 내에서 인접 배치되도록 함
   - 구조:
     - 디스크 record 에 `claim_coverage: []` + 빈 `claim_coverage_progress_summary` 시드 (store-seeded 분기)
     - 디스크 record 의 `results` 에는 noisy community source (`brunch.co.kr`) 를 포함해 stored record 가 noisy source 를 처음에 갖고 있었다는 점을 보존하지만, `response_origin.source_roles` 는 `["보조 기사"]` 로 좁혀져 noisy exclusion 이 serialization 시점에 이미 적용된 상태를 재현
     - `renderSearchHistory` item 에 **실제 server 가 serialize 하는 zero-count shape 와 noisy-filtered source_roles 를 그대로 시드**:
       - `claim_coverage_summary: { strong: 0, weak: 0, missing: 0 }`
       - `claim_coverage_progress_summary: ""`
       - `source_roles: ["보조 기사"]`
       - `verification_label: "기사 교차 확인"`
     - **`다시 불러오기` 클릭 / 자연어 reload / follow-up 을 전혀 수행하지 않음**
     - pre-click 어서션:
       - `#search-history-box` visible
       - `historyCard.locator(".history-item-actions button.secondary")` 가 `"다시 불러오기"` 텍스트 포함 (history item 자체는 정상 렌더링됨을 확인)
       - `historyCard not.toContainText("보조 커뮤니티")` — serialized source_roles 에서 noisy community 가 이미 excluded 된 상태여서 history card 뱃지 영역에도 등장해서는 안 됨
       - `historyCard not.toContainText("brunch")` — noisy community domain 문자열도 history card 뱃지/제목/summary 어디에서도 등장해서는 안 됨
     - 신규 empty-meta no-leak 어서션 (pre-click 단계에서 바로):
       - `historyCard.locator(".meta") toHaveCount(0)` — serialized zero-count shape 를 받아도 detail `.meta` 가 전혀 생성되지 않음
       - `historyCard not.toContainText("사실 검증")` — accidental `.meta` creation 으로 count line 이 leak 되는 경우 방어 double-guard
   - 기존 selector (`#search-history-box`, `.history-item`, `.history-item-actions button.secondary`, `.meta`) 와 `prepareSession`, `renderSearchHistory`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 noisy latest-update post-click 시나리오 (`:2250`, `:8927`, `:9004`, click-reload 가족의 회귀들) 는 **전혀 건드리지 않음** (handoff 지시)
2. **`tests/test_web_app.py` 는 전혀 건드리지 않음**
   - handoff 가 "keep existing service tests untouched unless you discover a concrete mismatch" 라고 명시했고, 기존 `tests/test_web_app.py:10981` (`test_web_search_store_list_summaries_includes_claim_coverage_summary`) 가 `_summarize_claim_coverage([])` 의 `{strong:0, weak:0, missing:0}` 계약을 이미 잠그고, `:11565` / `:11675` / `:11792` / `:19206` / `:19284` / `:19360` / `:19437` 의 noisy latest-update 회귀들이 serialized zero-count + 빈 progress + noisy source exclusion 을 post-reload / follow-up 단계에서 이미 잠가둔 상태
   - 본 라운드는 그 service 회귀들을 semantic anchor 로만 활용해 browser 측 신규 시나리오가 동일한 zero-count + noisy-filtered source_roles 분기를 pre-click user-visible DOM 레벨에서 direct 하게 검증하는 구조를 취함
3. entity-card / dual-probe / zero-strong / general / docs / pipeline 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_includes_claim_coverage_summary` → `ok` (generic semantic anchor 가 `_summarize_claim_coverage([])` → `{strong:0, weak:0, missing:0}` 계약을 여전히 잠그고 있음을 재확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update noisy .*initial-render.*empty-meta|latest-update noisy .*pre-click.*empty-meta" --reporter=line` → `1 passed (5.1s)` (신규 noisy initial-render 시나리오 한 개가 정규식에 매칭되어 실행; `ok`)
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 `tests/test_web_app.py` 를 전혀 건드리지 않았고, handoff 도 focused service anchor 한 개만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 noisy latest-update initial-render 시나리오 한 개만 추가함
- 기존 noisy latest-update post-click / click-reload 가족 / 자연어 reload 가족 / runtime-backed / non-noisy 시나리오 — handoff 는 이들을 그대로 두도록 명시함
- 기존 store-seeded actual-search 및 latest-update non-noisy initial-render 시나리오 — handoff 는 본 라운드를 noisy latest-update 가족으로 한정함

## 남은 리스크
- 신규 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 false-fail 됨. 같은 가정이 이전 latest-update 비-noisy / store-seeded actual-search 가족의 empty-meta 라운드들에서도 이미 사용 중이라 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역 (badge row, 제목, summary head) 이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- `not.toContainText("보조 커뮤니티")` / `not.toContainText("brunch")` guard 는 noisy source 가 serialization 단계에서 이미 source_roles 에서 제외되어 history card 의 badge row / 제목 / summary head 어디에서도 등장하지 않는다는 현재 계약에 의존함. 향후 noisy source 표시 정책이 바뀌면 이 두 guard 가 함께 조정되어야 함
- 본 시나리오는 `renderSearchHistory` item 에 explicit zero-count `claim_coverage_summary: {strong:0, weak:0, missing:0}` 를 시드하는 **의도된 설계** 임. 이는 CONTROL_SEQ 53/54 의 explicit zero-count dict branch 와 동일한 렌더러 경로를 exercise 하며, noisy latest-update 가족의 post-click 시나리오들이 사용하는 `undefined` 생략 경로와는 다른 branch 를 직접 잠금
- 이 시나리오는 어떤 `다시 불러오기` 클릭 / 자연어 reload / follow-up 도 수행하지 않음. Server interaction 없이 pure client-side 렌더러 분기만 잠그므로, 향후 server 측 noisy source filtering 이나 zero-count serialization 이 바뀌면 본 시나리오는 그 변경을 즉시 잡지 못함. 그 drift 는 `test_web_search_store_list_summaries_includes_claim_coverage_summary` 와 noisy latest-update service 회귀들 (`:11565`, `:11675`, `:11792`, `:19206-19437`) 이 1차 방어를 담당하며, 본 시나리오는 client-side `.meta` + noisy source exclusion 규약을 initial-render 단계에서 보완적으로 잠금
- 기존 noisy latest-update post-click 시나리오들과 본 라운드의 initial-render 시나리오는 같은 stored record 모양 (noisy community source 가 results 에 포함되지만 source_roles 에서는 제외) 을 공유하고, 파일 내에서 initial-render → post-click show-only reload → 자연어 reload + first/second follow-up → click-reload + first/second follow-up 순서로 확장되는 노이즈-필터된 noisy 가족의 user-visible no-leak 계약이 single file 안에서 end-to-end 로 보완됨
- handoff 가 "service tests untouched unless a concrete mismatch" 라고 명시했고 본 라운드는 service 측을 건드리지 않아 CONTROL_SEQ 45/46/48/51-54 및 기존 noisy latest-update 회귀들의 잠금 상태를 그대로 유지함
- CONTROL_SEQ 53 (store-seeded actual-search initial-render) → CONTROL_SEQ 54 (latest-update non-noisy initial-render × 3) → 본 CONTROL_SEQ 55 (latest-update noisy initial-render × 1) 루프는 "**explicit zero-count dict branch at pre-click render time**" user-visible contract 를 세 가족 (store-seeded actual-search, latest-update non-noisy mixed/single/news, latest-update noisy) 에 걸쳐 독립적으로 잠그는 진행 패턴으로, 렌더러의 동일 분기가 다양한 source_roles / verification_label / noisy-exclusion 조합에서 drift-free 함을 확인할 수 있음
- 시나리오를 한 개 신규 추가했으므로 기존 coverage 와 겹치지 않고 파일 내에서 noisy latest-update 가족이 initial-render → post-click show-only reload → 후속 follow-up 가족 순서로 시각적으로 인접 배치됨
