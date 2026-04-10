# history-card entity-card actual-search first-follow-up browser meta truth-sync bundle

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 기존 actual-search entity-card first-follow-up 세 브라우저 시나리오를 실제 shipped strong-plus-missing 분기로 truth-sync:
  - `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path(namu.wiki, ko.wikipedia.org) + WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 유지됩니다` (click-reload + first follow-up)
  - `entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 source path(namu.wiki, ko.wikipedia.org)가 context box에 유지됩니다` (자연어 reload + first follow-up, source-path)
  - `entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다` (자연어 reload + first follow-up, WEB-badge)
  - 세 시나리오 모두 디스크 record 의 `claim_coverage` 를 stale 단일 strong slot + `"교차 확인 1건."` progress 또는 empty `[]` + 빈 progress 에서 3 strong + 2 missing slot + 빈 progress 로 전환 (slot 이름은 noisy 키워드 `출시일`/`2025`/`brunch` 와 충돌하지 않도록 `엔진`/`난이도` 사용), `renderSearchHistory` item 에 `claim_coverage_summary: {strong:3, weak:0, missing:2}` 와 빈 progress 를 시드, follow-up 이후 history-card `.meta === "사실 검증 교차 확인 3 · 미확인 2"` + `.meta` 한정 `설명 카드` / `최신 확인` / `일반 검색` 부정 어서션을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- `CONTROL_SEQ: 43` 은 세 서비스 회귀(`test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths`, `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths`, `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin`) 에 `{strong:3, weak:0, missing:2}` 어서션을 요구했지만, 첫 번째 테스트 (`:16977`) 는 `WebSearchStore.save(...)` 로 **사전 시드** 된 store-seeded 경로로 `claim_coverage` 파라미터를 전혀 전달하지 않아 runtime 분포가 `{0,0,0}` (empty-meta) 였음. 이로 인해 `implement_blocked` 로 환원됨
- `CONTROL_SEQ: 44` 는 store-seeded 테스트 세 개를 strong-plus-missing anchor 로 사용하지 말라고 명시적으로 지시하고, 본 라운드는 **브라우저 side 만** 실제 shipped runtime 분기로 truth-sync 하도록 scope 를 좁힘
- `storage/web_search_store.py:316-317` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 의 렌더러 경로는 investigation entity_card 에서 answer-mode label 을 skip 하고 `formatClaimCoverageCountSummary({strong:3, missing:2})` → `"교차 확인 3 · 미확인 2"` 를 내므로 `.meta` 는 `사실 검증 교차 확인 3 · 미확인 2` 한 줄이어야 함 — 이는 직전 CONTROL_SEQ 42 (actual-search reload-only) 와 CONTROL_SEQ 32 (actual-search second follow-up) 에서 이미 동일한 분기로 잠근 값과 정확히 일치함
- 기존 브라우저 시나리오 세 개(`:3596`, `:6625` → 현재 `:6635`, `:6745` → 현재 `:6755`) 는 badge / source-path / origin detail continuity 만 잠갔고, 시드된 `claim_coverage` 는 stale 단일 `{strong:1}` slot + `"교차 확인 1건."` progress 또는 empty `[]` 로 runtime 분포와 드리프트 상태였음
- `tests/test_web_app.py:9354`, `:9471` (runtime-backed `test_handle_chat_actual_entity_search_*_reload_second_follow_up_preserves_claim_coverage_count_summary`) 는 이미 same-family first-follow-up boundary 를 통과하는 runtime 기반 continuity 를 잠그고 있어, 본 라운드는 이들을 read/verification anchor 로만 사용하고 신규 service-test 이론을 확장하지 않음
- 이 슬라이스는 런타임 변경 없이 세 브라우저 시나리오의 seed 와 `.meta` 어서션만 in-place 추가해 actual-search first-follow-up 가족의 user-visible meta 계약을 잠그는 범위임. reload-only (CONTROL_SEQ 42 완료), second-follow-up (CONTROL_SEQ 32 완료), dual-probe (CONTROL_SEQ 41 완료), zero-strong, latest-update, general, docs, pipeline 은 의도적으로 범위 밖. store-seeded 서비스 테스트 (`:16977`, `:18151`, `:18219`) 는 명시적으로 건드리지 않음 — `tests/test_web_app.py` 는 이번 라운드에서 **전혀 수정되지 않음**

## 핵심 변경
1. **`e2e/tests/web-smoke.spec.mjs` 세 브라우저 시나리오 in-place tighten**
   - 세 시나리오 모두 디스크 record 의 `claim_coverage` 를 5 slot 으로 교체 또는 확장:
     - strong: `장르`, `개발사`, `플랫폼` (3개)
     - missing: `엔진`, `난이도` (2개)
   - slot 이름은 noisy 가족의 negative assertion 키워드(`출시일`/`2025`/`brunch`/`blog.example.com`) 와 충돌하지 않도록 의도적으로 선택함 (본 세 시나리오에는 noisy exclusion 어서션이 없지만, 이전 actual-search reload-only 라운드 (CONTROL_SEQ 42) 의 noisy 변형과 동일 패턴으로 맞춰 장래 공유 fixture 쪽 drift 도 방지)
   - `claim_coverage_progress_summary` 를 stale `"교차 확인 1건."` 또는 `""` → `""` 로 정렬 (runtime 과 일치)
   - `renderSearchHistory` item 에 `claim_coverage_summary: { strong: 3, weak: 0, missing: 2 }` 와 빈 `claim_coverage_progress_summary` 를 시드해 pre-click 과 post-reload/post-follow-up 양쪽에서 `.meta` 가 동일 문자열을 내도록 정렬
   - first follow-up 이후 기존 origin/context-box 어서션 다음에 아래 블록 추가:
     ```
     const historyCardMeta = historyBox.locator(".history-item").first().locator(".meta");
     await expect(historyCardMeta).toHaveCount(1);
     await expect(historyCardMeta).toHaveText("사실 검증 교차 확인 3 · 미확인 2");
     await expect(historyCardMeta).not.toContainText("설명 카드");
     await expect(historyCardMeta).not.toContainText("최신 확인");
     await expect(historyCardMeta).not.toContainText("일반 검색");
     ```
   - count line 자체가 ` · ` 구분자를 합법적으로 포함하므로 `not.toContainText("·")` blanket rule 은 사용하지 않음
   - `설명 카드` / `최신 확인` / `일반 검색` 부정 어서션은 `.meta` element 에만 한정 적용 (history card 의 `.answer-mode-badge` 에는 정상적으로 `설명 카드` 가 등장하므로 전체 카드 blanket 부정은 false negative 가 됨)
   - 기존 `WEB` badge / `설명 카드` answer-mode badge / origin detail verification-label & source-roles / `#context-box` source-path 어서션은 전부 그대로 유지
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
2. **`tests/test_web_app.py` 는 전혀 건드리지 않음**
   - handoff 지시대로 store-seeded 서비스 테스트 세 개(`:16977`, `:18151`, `:18219`) 에는 새 strong-plus-missing 어서션을 붙이지 않음
   - 대신 handoff 가 명시한 runtime-backed read/verification anchor (`tests/test_web_app.py:9354`, `:9471` — `test_handle_chat_actual_entity_search_*_reload_second_follow_up_preserves_claim_coverage_count_summary`) 가 이미 동일 런타임 분포를 잠그고 있다는 사실을 이번 검증에서 확인만 함. 서비스 테스트의 structure 는 이 라운드에서 변경하지 않음
3. reload-only / second-follow-up / dual-probe / zero-strong / latest-update / general / docs / pipeline 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_claim_coverage_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_claim_coverage_count_summary` → 두 anchor 테스트 모두 `ok` (runtime-backed actual-search first-follow-up boundary 가 `{strong:3, weak:0, missing:2}` 분기를 이미 통과 중임을 재확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path|entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 source path|entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 WEB badge" --reporter=line` → `3 passed (15.8s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 service test 를 전혀 건드리지 않았고, handoff 도 focused 두 anchor 만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 기존 세 시나리오만 in-place tighten 함
- 기존 reload-only / second-follow-up / dual-probe / zero-strong / latest-update / general 시나리오 — handoff 는 이들을 그대로 두도록 명시함
- store-seeded 서비스 테스트(`:16977`, `:18151`, `:18219`) — handoff 지시에 따라 새 strong-plus-missing 어서션을 붙이지 않음

## 남은 리스크
- 세 브라우저 시나리오의 `.meta` 정확 텍스트는 시드된 `claim_coverage` 의 3 strong + 2 missing 비율과 `formatClaimCoverageCountSummary` 의 `"교차 확인 N · 미확인 N"` 포맷에 의존함. 포맷이 바뀌면 스모크가 먼저 깨짐 — 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- slot 이름은 `엔진`/`난이도` 로 선택해 noisy 키워드(`출시일`/`2025`/`brunch`/`blog.example.com`) 와 충돌하지 않도록 함. 향후 noisy 키워드 목록이 확장되면 slot 이름도 함께 재검토해야 함
- store-seeded 서비스 테스트 (`:16977`, `:18151`, `:18219`) 는 여전히 empty-meta `{0,0,0}` 분기로 남아 있으며, 이 가족에 대한 명시적 empty-meta 어서션은 **별도 라운드**에서 다루어야 함. 본 라운드는 browser-side first-follow-up `.meta` 계약만 truth-sync 하고 서비스-side 는 handoff 지시에 따라 건드리지 않음
- `.meta` 한정 `설명 카드` / `최신 확인` / `일반 검색` 부정 어서션은 history card 의 `.answer-mode-badge` 뱃지 텍스트와 충돌하지 않음 (false positive 없음)
- CONTROL_SEQ 32 (actual-search second follow-up), CONTROL_SEQ 42 (actual-search reload-only), 본 CONTROL_SEQ 44 (actual-search first follow-up browser) 가 모두 동일한 `{strong:3, weak:0, missing:2}` 분기로 잠기며 actual-search 가족의 `.meta` 계약이 browser-side 에서 reload → first follow-up → second follow-up 전 구간 걸쳐 end-to-end 로 잠김
- CONTROL_SEQ 43 의 `implement_blocked` → CONTROL_SEQ 44 의 scope 재조정 루프는 store-seeded 와 runtime-backed 테스트 가족을 혼동하지 않도록 scope boundary 를 정정하는 정상적 pipeline 동작임. 이번 closeout 은 blocked 단계를 건너뛴 것이 아니라 수정된 scope 를 구현한 결과임
- 시나리오를 in-place tighten 했으므로 이름은 그대로 유지되었지만 실제로는 strong-plus-missing `.meta` 어서션까지 확장되었음. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
