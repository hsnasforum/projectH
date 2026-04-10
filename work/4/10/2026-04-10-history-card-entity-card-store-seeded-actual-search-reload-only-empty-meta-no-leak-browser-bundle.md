# history-card entity-card store-seeded actual-search reload-only empty-meta no-leak browser bundle

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 신규 브라우저 시나리오 `history-card entity-card store-seeded actual-search 다시 불러오기 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다` 를 기존 store-seeded click-reload first/second follow-up 시나리오 직전에 삽입. store-seeded 가족이 **reload-only → first follow-up → second follow-up → 자연어 reload 체인** 네 단계의 시나리오로 파일 내에서 인접 배치되도록 함. 이 신규 시나리오는 click reload 단계에서 바로 정지하고, 후속 follow-up / 자연어 reload 로 진입하지 않음으로써 "**reload 직후 empty-meta no-leak**" 만 단독으로 잠그는 bounded browser 회귀임
- `tests/test_web_app.py` 는 전혀 건드리지 않음 (handoff 지시에 따라 `tests/test_web_app.py:17179` 의 `_assert_empty_meta_continuity(first, "click reload")` 가 이미 같은 click-reload 단계의 zero-count summary + 빈 progress + stored verification label 을 service 측에서 잠그고 있음 — 이를 semantic anchor 로만 활용)

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-entity-card-store-seeded-actual-search-natural-reload-empty-meta-continuity-bundle.md`, CONTROL_SEQ 49) 는 store-seeded actual-search 가족의 natural-reload 체인 (click → natural reload → first follow-up → second follow-up) empty-meta no-leak 계약을 persistent truth 로 기록했고, 그 이전 CONTROL_SEQ 45 / 46 라운드는 click-reload first-follow-up / second-follow-up 체인을 잠갔음
- 그러나 기존 store-seeded 브라우저 시나리오 세 개 (`:3596` reload + first follow-up, `:3721` → 현재 `:3830` reload + second follow-up, `:3856` 자연어 reload 체인) 는 모두 reload **이후 후속 step 을 지나간 뒤** 에 `.meta toHaveCount(0)` 를 검증함. 즉 "다시 불러오기 직후의 `.meta` 부재" 는 후속 단계로 인해 간접적으로만 잠겨 있었고, user-visible 에서 reload 만 수행하고 화면을 그대로 두는 경로가 browser 측에 직접 잠겨 있지 않았음
- `storage/web_search_store.py:316-317` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 경로에 의해 store-seeded record 는 reload 직후 `claim_coverage_summary == {"strong":0, "weak":0, "missing":0}` 과 빈 progress 로 직렬화되고, investigation entity_card 렌더러는 answer-mode label 을 skip + `formatClaimCoverageCountSummary({0,0,0})` = 빈 문자열이므로 detail `.meta` 자체가 생성되지 않아야 함
- `tests/test_web_app.py:17179` 의 `_assert_empty_meta_continuity(first, "click reload")` 는 same-click-reload-stage 에서 service 측 `claim_coverage_summary` / `claim_coverage_progress_summary` / `verification_label` 을 잠그고 있지만, **browser 측의 DOM 에서 `.meta` detail node 가 생성되지 않음을 직접 검증** 하는 회귀는 없었음
- 이 슬라이스는 service refactor 없이 기존 store-seeded seed 규약을 재사용하는 browser 시나리오 한 개를 신규 추가해 reload-only user-visible 계약을 독립적으로 잠그는 범위임. 후속 체인을 타지 않으므로 첫 click 시점의 behavior 가 예기치 못한 drift 를 일으키면 본 시나리오가 가장 먼저 실패함
- runtime-backed strong-plus-missing / natural-reload / dual-probe / zero-strong / latest-update / noisy / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오**
   - 신규 테스트 이름: `history-card entity-card store-seeded actual-search 다시 불러오기 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다`
   - 기존 store-seeded click-reload first-follow-up 시나리오 (`:3596` → 현재 `:3705`) 직전에 삽입해 store-seeded 가족이 reload-only → first follow-up → second follow-up → 자연어 reload chain 네 시나리오로 파일 내에서 인접 배치되도록 함
   - 구조:
     - 디스크 record 에 `claim_coverage: []` + 빈 `claim_coverage_progress_summary` 시드 (store-seeded 분기)
     - `renderSearchHistory` item 에는 `claim_coverage_summary` / `claim_coverage_progress_summary` 를 **전혀 seed 하지 않음** (의도된 설계 — client seed 가 붙으면 pre-click `.meta` 가 생성될 수 있어 no-leak 잠금이 false-fail 할 수 있음)
     - `다시 불러오기` 클릭 (show-only reload) **한 번만** 실행하고, 후속 follow-up 또는 자연어 reload 로 **진입하지 않음**
     - reload 직후 어서션:
       - `#response-origin-badge === "WEB"` + `web` class
       - `#response-answer-mode-badge` visible + `"설명 카드"`
       - `#response-origin-detail` 이 `설명형 다중 출처 합의` + `백과 기반` 포함
       - `#context-box` 가 `namu.wiki` + `ko.wikipedia.org` 포함 (source-path 연속성)
     - 신규 empty-meta no-leak 어서션:
       - `historyCard.locator(".meta") toHaveCount(0)` — 다시 불러오기 직후에 detail `.meta` 가 전혀 생성되지 않음
       - `historyCard not.toContainText("사실 검증")` — accidental `.meta` creation 으로 count line 이 leak 되는 경우 방어 double-guard
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - 기존 store-seeded first-follow-up / second-follow-up / 자연어 reload chain 시나리오와 runtime-backed actual-search 시나리오는 **전혀 건드리지 않음** (handoff 지시)
2. **`tests/test_web_app.py` 는 전혀 건드리지 않음**
   - handoff 가 "keep existing service tests untouched unless you discover a concrete mismatch" 라고 명시했고, 기존 `tests/test_web_app.py:17179` 의 `_assert_empty_meta_continuity(first, "click reload")` 가 이미 click-reload 단계의 `session.web_search_history` zero-count summary + 빈 progress + stored verification label 을 잠그고 있어 service 측 mismatch 가 없음
   - 본 라운드는 그 service 회귀를 semantic anchor 로만 활용해 browser 측 신규 시나리오가 동일한 zero-count 분기를 user-visible DOM 레벨에서 직접 검증하는 구조를 취함
3. runtime-backed strong-plus-missing / natural-reload 가족 / dual-probe / zero-strong / latest-update / noisy / general / docs / pipeline 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_store_seeded_actual_search_post_reload_natural_reload_follow_up_chain_preserves_empty_meta_no_leak` → `ok` (click-reload 단계의 `_assert_empty_meta_continuity(first, "click reload")` 가 여전히 zero-count summary + 빈 progress + stored verification label 을 service 측에서 잠그고 있음을 재확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "store-seeded actual-search.*reload-only|store-seeded actual-search.*다시 불러오기.*empty-meta" --reporter=line` → `3 passed (17.2s)`
  - `:3596` 신규 reload-only 시나리오 (이번 라운드)
  - `:3705` 기존 store-seeded click-reload first-follow-up 시나리오 (CONTROL_SEQ 45)
  - `:3830` 기존 store-seeded click-reload second-follow-up 시나리오 (CONTROL_SEQ 46)
  - 세 시나리오 모두 `다시 불러오기.*empty-meta` 정규식에 매칭되어 함께 실행; 셋 다 `ok`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 `tests/test_web_app.py` 를 전혀 건드리지 않았고, handoff 도 focused service anchor 한 개만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 store-seeded reload-only 시나리오 한 개만 추가함
- 기존 runtime-backed actual-search / 자연어 reload chain / dual-probe / zero-strong / latest-update / noisy / general 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 false-fail 됨. 같은 가정이 이전 latest-update / store-seeded click-reload first/second-follow-up / 자연어 reload chain empty-meta 라운드들에서도 이미 사용 중이라 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 badge/summary 영역에서 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- store-seeded 경로에서 `renderSearchHistory` item 에 `claim_coverage_summary` 를 seed 하지 않는 것이 의도된 설계임. seed 하면 client-side 에서 `.meta` 가 생성될 수 있어 `toHaveCount(0)` 어서션이 false-fail 할 수 있음 — 이 의도는 코드 주석으로 명시해 두었음
- reload-only 시나리오는 click reload **한 번만** 실행하고 후속 단계로 진입하지 않음. 향후 reload 직후의 DOM state 가 비동기 로딩으로 잠시 불안정해지는 경우에도 Playwright 의 auto-waiting 이 `originBadge` 등 다른 assertion 에서 먼저 실패해 원인을 빠르게 가리킴. `.meta toHaveCount(0)` 이 reload 완료 전에 평가되는 false-positive 는 `expect(originBadge).toHaveText("WEB")` 이 먼저 통과해야 후속 어서션이 실행되므로 발생하지 않음
- 기존 store-seeded first-follow-up / second-follow-up / 자연어 reload chain 시나리오 세 개와 본 라운드의 reload-only 시나리오는 같은 seed 규약 (`claim_coverage: []`, `renderSearchHistory` 에 `claim_coverage_summary` 미시드) 을 공유하고, 파일 내에서 reload → first follow-up → second follow-up → natural reload chain 네 가지 길이의 체인이 인접 배치되어 각 체인 길이별 no-leak 계약이 서로 보완함
- handoff 가 "service tests untouched unless a concrete mismatch" 라고 명시했고 본 라운드는 service 측을 건드리지 않아 CONTROL_SEQ 45/46/48 의 잠금 상태를 그대로 유지함. 향후 service 측에서 `_assert_empty_meta_continuity` 가 다른 stage 로 확장되거나 reload-only 별도 회귀로 분리될 필요가 생기면 별도 라운드에서 다룰 수 있음
- CONTROL_SEQ 49 truth-sync → CONTROL_SEQ 51 reload-only bounded-browser 루프는 `truth-sync → user-visible coverage tightening` 진행 패턴으로, 동일 가족의 persistent-truth 가 기록된 상태에서 user-visible DOM 계약을 점진적으로 잠그는 정상 순서임. 본 라운드는 browser 측에서 "click reload 직후" 의 user-visible `.meta` 부재를 독립적으로 잠가 store-seeded actual-search 가족의 reload-only edge 를 명시적으로 닫음
- 시나리오를 신규 추가했으므로 기존 coverage 와 겹치지 않고 파일 내에서 store-seeded 가족이 네 시나리오로 인접 배치되어 향후 reader 가 reload-only → first follow-up → second follow-up → natural reload chain 의 점진적 구조를 시각적으로 구분할 수 있음
