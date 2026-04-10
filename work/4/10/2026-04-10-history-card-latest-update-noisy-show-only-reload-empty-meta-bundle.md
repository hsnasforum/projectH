# history-card latest-update noisy show-only reload empty-meta bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 latest-update noisy show-only reload 세 서비스 회귀에 history-entry empty-meta continuity 어서션을 in-place 추가 (기존 noisy-source exclusion / verification-label parity / source-role contract 어서션은 그대로 유지):
  - `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload`
  - `test_handle_chat_latest_update_single_source_verification_label_retained_after_history_card_reload`
  - `test_handle_chat_latest_update_dual_news_noisy_community_badge_contract`
  - 세 회귀 모두 `second` (`load_web_search_record_id` show-only reload) 응답 단계에서 `session.web_search_history` 의 해당 `record_id` 항목이 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 0}`, 빈 `claim_coverage_progress_summary` 를 유지하는지 확인
- `e2e/tests/web-smoke.spec.mjs` — 기존 latest-update noisy show-only reload 브라우저 시나리오 `history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다` 에 history-card empty-meta no-leak 어서션을 in-place 추가. 기존 본문/origin/context 부정 어서션과 `#context-box` 긍정 어서션은 그대로 유지

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-latest-update-show-only-reload-empty-meta-bundle.md`) 와 그 `/verify` 는 latest-update **non-noisy** show-only reload 가족의 empty-meta no-leak 계약을 잠갔고, 같은 라운드의 검증 단계에서 다음 현재 위험으로 latest-update **noisy** show-only reload 분기에 동일한 empty-meta no-leak 계약이 여전히 잠기지 않았음을 관찰함
- `storage/web_search_store.py:316-317` + `app/serializers.py:280-287` + `app/static/app.js:2954-2969` 에 의해 latest-update noisy show-only reload 런타임도 동일하게:
  - history entry 가 zero-count `claim_coverage_summary` 를 serialize 함
  - `claim_coverage_progress_summary` 가 빈 문자열로 유지됨
  - investigation 카드는 detailLines 에서 answer-mode label 을 skip 함
  - 결과적으로 history card 는 `.meta` detail node 를 생성하지 않아야 함
- 기존 서비스 회귀 세 개(`:11359`, `:11451`, `:11544`) 는 noisy-source exclusion / verification-label parity / source-role contract 만 잠갔고, 기존 브라우저 시나리오 한 개(`:2250`) 는 본문/origin/context negative assertions 만 잠가 empty-meta no-leak 계약을 직접 exercise 하지 않음
- 이 슬라이스는 런타임 변경 없이 세 서비스 회귀와 한 browser 시나리오에 empty-meta assertion block 을 in-place 추가해 "noisy show-only reload 후에도 history card 에 `.meta` detail node 가 없고 `사실 검증` content leak 이 없다" 는 current shipped contract 를 명시적으로 잠그는 범위임. 이 라운드로 latest-update 가족(noisy + non-noisy) × (show-only + click-reload + 자연어 reload) × (shallow + second-follow-up) 전 분기가 empty-meta no-leak 으로 잠기며 latest-update 가족의 empty-meta 계약이 truthfully end-to-end 로 닫힘
- noisy latest-update follow-up 가족(직전 noisy follow-up 라운드들 완료), non-noisy latest-update 가족(직전 라운드들 완료), entity-card, actual-search, dual-probe, zero-strong, general, docs, pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` 세 서비스 회귀 in-place tighten**
   - 세 테스트 모두 `second = service.handle_chat({..., "load_web_search_record_id": record_id})` show-only reload 이후 기존 noisy exclusion / verification-label parity 어서션 뒤에 assertion block 을 삽입
   - 공통 assertion pattern (직전 show-only reload empty-meta 라운드와 동일):
     - `reload_history = second["session"]["web_search_history"]`
     - `self.assertTrue(reload_history)`
     - `reload_entry = next((item for item in reload_history if item.get("record_id") == record_id), None)`
     - `self.assertIsNotNone(reload_entry)`
     - `self.assertEqual(reload_entry.get("claim_coverage_summary") or {}, {"strong": 0, "weak": 0, "missing": 0})`
     - `self.assertEqual(str(reload_entry.get("claim_coverage_progress_summary") or ""), "")`
   - 기존 `actions_taken == ["load_web_search_record"]`, `response_origin.answer_mode == "latest_update"`, `verification_label` / `source_roles`, noisy-community 및 `brunch` 부정 어서션은 전부 그대로 유지
   - `_FakeWebSearchTool` / `AppSettings` / `WebAppService` fixture 는 재사용, 신규 helper/import/fixture 파일 없음
2. **`e2e/tests/web-smoke.spec.mjs` noisy show-only 시나리오 in-place tighten**
   - show-only reload 클릭 이후 기존 origin/response/context-box 부정/긍정 어서션 다음에 다음 두 줄을 추가:
     ```
     const historyCard = historyBox.locator(".history-item").first();
     await expect(historyCard.locator(".meta")).toHaveCount(0);
     await expect(historyCard).not.toContainText("사실 검증");
     ```
   - `toHaveCount(0)` 은 investigation empty branch 에서 detail `.meta` 가 전혀 생성되지 않음을 잠금. `app/static/app.js:2939-2943` 의 header timestamp `<span>` 은 className 이 없는 raw span 이므로 `.meta` CSS selector 에 매칭되지 않아 false positive 없음 (직전 non-noisy / follow-up 라운드들에서 이미 검증됨)
   - `not.toContainText("사실 검증")` 은 accidental `.meta` creation 으로 count line 이 leak 되면 `사실 검증 ...` 접두어가 전체 카드 텍스트에 등장할 텐데 그 leak 자체를 막는 double-guard. 카드의 header/badge/summary 영역에는 `사실 검증` 문자열이 등장하지 않으므로 false positive 없음
   - handoff 지시에 따라 `not.toContainText("최신 확인")` / `not.toContainText("기사 교차 확인")` blanket rule 은 **사용하지 않음** — 이 두 문자열은 각각 `.answer-mode-badge` 와 `.verification-badge` DOM 에 정상적으로 등장하므로 전체 카드에 대한 blanket 부정이 false negative 가 됨. `.meta toHaveCount(0)` 이 accidental `.meta` 생성 자체를 원천 차단함
   - 기존 `originBadge`/`answerModeBadge`/`originDetail` 긍정 어서션, `originDetailText` / `responseText` / `contextBoxText` 의 `보조 커뮤니티`·`brunch`·`로그인 회원가입 구독 광고` 부정 어서션, `#context-box` 의 `hankyung.com`/`mk.co.kr` 긍정 어서션은 전부 그대로 유지
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음
   - noisy latest-update follow-up 시나리오, non-noisy latest-update 시나리오, entity-card / actual-search / dual-probe / zero-strong / general 시나리오는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_verification_label_retained_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_dual_news_noisy_community_badge_contract` → 세 테스트 모두 `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출" --reporter=line` → `1 passed (6.5s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 세 latest-update noisy show-only reload 회귀에 순수 추가 어서션만 붙였고 기존 로직 변경이 없음. handoff 도 focused 세 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 기존 한 시나리오만 in-place tighten 함
- 기존 noisy latest-update follow-up / non-noisy latest-update / entity-card / actual-search / dual-probe / zero-strong / general 시나리오 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 브라우저 시나리오의 `toHaveCount(0)` guard 는 `app/static/app.js:2939-2943` 의 header timestamp `<span>` 이 className 을 가지지 않는다는 전제에 의존함. 향후 header span 에 `.meta` class 가 붙으면 이 guard 가 false-fail 됨. 같은 가정이 이전 non-noisy show-only / follow-up / noisy follow-up / entity-card / noisy 라운드들에서도 이미 사용되고 있어 drift 범위는 기존 시나리오 전반과 동일
- `not.toContainText("사실 검증")` guard 는 history card 의 다른 영역이 `사실 검증` 접두어를 절대 사용하지 않는다는 전제에 의존함. 향후 UI 가 해당 접두어를 다른 곳에서 재사용하면 이 guard 가 false-fail 하므로 함께 조정해야 함
- 세 서비스 회귀는 정확 dict equality (`{"strong": 0, "weak": 0, "missing": 0}`) 로 count-summary 를 잠금. `_summarize_claim_coverage` 가 추가 key 를 내거나 zero-count 표현이 None 로 바뀌면 equality 가 먼저 실패해 원인을 빠르게 가리킴 — failure-first 설계이며, 직전 latest-update show-only / follow-up 라운드들의 동일 패턴과 상호 일관적
- handoff 지시에 따라 `최신 확인` / `기사 교차 확인` 에 대한 직접 blanket `not.toContainText` 는 의도적으로 피함 (false negative 방지). 대신 `.meta toHaveCount(0)` 으로 accidental `.meta` 생성 자체를 원천 차단
- 이번 라운드로 latest-update (noisy + non-noisy) × (show-only + click-reload + 자연어 reload) × (shallow + second-follow-up) 전 분기가 empty-meta no-leak 으로 잠기며 latest-update 가족의 empty-meta 계약이 truthfully end-to-end 로 닫힘. 다음 현재 위험은 entity-card / actual-search / dual-probe / zero-strong / general 가족의 아직 열린 메타 경로에 있을 수 있지만 본 슬라이스 범위 밖이며 별도 라운드로 남겨둠
- 시나리오/회귀를 in-place tighten 했으므로 이름은 그대로 유지되었지만 실제로는 empty-meta no-leak 어서션까지 확장되었음. 향후 이름 리팩터링은 별도 docs-sync 라운드에서 다룰 수 있음
