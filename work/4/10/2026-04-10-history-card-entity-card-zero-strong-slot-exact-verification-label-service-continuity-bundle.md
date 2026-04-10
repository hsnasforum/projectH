# history-card entity-card zero-strong-slot exact verification-label service continuity bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 zero-strong entity-card 서비스 테스트 일곱 개에서 loose / baseline-only `verification_label` 검사를 literal `"설명형 단일 출처"` exact equality 로 교체:
  - `test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization` (`:10107`): `assertNotEqual(..., "설명형 다중 출처 합의")` + `assertTrue(...)` 두 줄을 `assertEqual(history[0]["verification_label"], "설명형 단일 출처")` 한 줄로 교체.
  - `test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization_includes_missing_only_count_summary` (`:10159`): 같은 two-line loose 검사 블록을 `assertEqual(entry["verification_label"], "설명형 단일 출처")` 한 줄로 교체.
  - `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields` (`:10484`) + `test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` (`:10553`): 두 테스트의 공통 초기 블록 `first_origin["answer_mode"] == "entity_card"` + `assertNotEqual(first_origin["verification_label"], "설명형 다중 출처 합의")` 를 `Edit replace_all=true` 로 `assertEqual(first_origin["verification_label"], "설명형 단일 출처")` 로 교체. reload_origin continuity (`reload_origin["verification_label"] == first_origin["verification_label"]`) 는 자동으로 exact literal 에 바인딩됨.
  - `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_follow_up_preserves_stored_response_origin` (`:17827`): `first_origin = first["response"]["response_origin"]` 직후에 `assertEqual(first_origin["verification_label"], "설명형 단일 출처")` 한 줄을 추가. 기존 `reload_origin["verification_label"] == first_origin["verification_label"]` continuity 가 자동으로 literal 에 바인딩됨.
  - `test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin` (`:17974`): 같은 방식으로 `first_origin` 취득 직후 exact literal 어서션 한 줄 추가.
  - `test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` (`:18053`): `first_origin = first["response"]["response_origin"]` + `assertIsNotNone(first_origin)` 직후에 exact literal 어서션을 추가. `_assert_origin_and_sources(result, stage)` 헬퍼의 `origin["verification_label"] == first_origin["verification_label"]` continuity 가 자동으로 literal 에 바인딩됨.
- 기존 exact count-summary (`{"strong": 0, "weak": 0, "missing": 5}`), 빈 progress, `source_roles`, `answer_mode`, `source_paths` 어서션은 모두 그대로 유지.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 64 (zero-strong follow-up chain exact `{0,0,5}`) + CONTROL_SEQ 65 (zero-strong initial + reload exact `{0,0,5}`) 이 zero-strong 가족 count-summary 전체를 서비스 층에서 exact dict 로 잠갔음.
- browser 쪽 UX 는 이미 literal `설명형 단일 출처` 를 `e2e/tests/web-smoke.spec.mjs:6053`, `:6155`, `:6683` 에서 exact 로 잠가둔 상태.
- handoff 의 focused 런타임 probe 가 service 가 실제로 initial response origin 및 stored history entry 모두에서 동일 literal `"설명형 단일 출처"` 를 방출함을 확인.
- 그러나 zero-strong 가족의 서비스 테스트 일곱 개는 여전히 downgraded label 에 대해 loose 검사 (`assertNotEqual(..., "설명형 다중 출처 합의")` + `assertTrue(...)`) 또는 baseline-only continuity (`first_origin["verification_label"]` 과의 일치) 만 수행하고 있었음. 이 경우 label 이 다른 downgraded 문자열로 drift 해도 (예: `"설명형 단일 근거"`) 테스트는 통과하면서 browser literal 과 silently 어긋남.
- handoff 는 "replace the current downgraded/non-strong checks or baseline-only label continuity with exact `verification_label == "설명형 단일 출처"` where the runtime already emits that literal" 라고 명시하고, 기존 count-summary / source_roles / answer_mode / source_paths / progress 어서션은 그대로 두도록 지시. 범위 밖은 browser / 신규 테스트 / 다른 가족 / docs / pipeline.
- 본 라운드 이후 zero-strong 가족 전체가 service 층에서 literal `"설명형 단일 출처"` 를 exact 로 잠그고, 기존 `reload_origin` / `followup_origin` / `origin` continuity 검사는 자동으로 literal 에 바인딩되어 모든 stage (initial serialization, click reload exact fields, natural reload exact fields, click reload follow-up, natural reload follow-up, natural reload second follow-up) 가 browser literal 과 truth-synced 가 됨.

## 핵심 변경
1. **`tests/test_web_app.py:10107` (`..._history_badge_serialization`) — initial serialization anchor**
   - 제거: `assertNotEqual(history[0]["verification_label"], "설명형 다중 출처 합의")` + `assertTrue(history[0]["verification_label"])` 두 줄
   - 추가: `assertEqual(history[0]["verification_label"], "설명형 단일 출처")` 한 줄
2. **`tests/test_web_app.py:10159` (`..._history_badge_serialization_includes_missing_only_count_summary`) — count-summary anchor**
   - 제거: `assertNotEqual(entry["verification_label"], "설명형 다중 출처 합의")` + `assertTrue(entry["verification_label"])` 두 줄 (CONTROL_SEQ 65 의 exact count-summary 어서션은 그대로 유지)
   - 추가: `assertEqual(entry["verification_label"], "설명형 단일 출처")` 한 줄
3. **`tests/test_web_app.py:10484` + `:10553` (`..._history_card_reload_exact_fields` + `..._natural_reload_exact_fields`) — reload-only exact anchors**
   - 두 테스트의 공통 초기 블록에서 `assertNotEqual(first_origin["verification_label"], "설명형 다중 출처 합의")` 를 `assertEqual(first_origin["verification_label"], "설명형 단일 출처")` 로 `replace_all=true` 로 한 번에 교체. 두 매치 모두 zero-strong 가족의 reload exact-fields 테스트 안에 있음 (grep 으로 확인).
   - 기존 `reload_origin["verification_label"] == first_origin["verification_label"]` continuity 어서션은 자동으로 literal 에 바인딩됨.
4. **`tests/test_web_app.py:17827` / `:17974` / `:18053` — follow-up anchors**
   - 세 테스트 모두 `first_origin = first["response"]["response_origin"]` 직후에 `assertEqual(first_origin["verification_label"], "설명형 단일 출처")` 한 줄을 추가. 각각 서로 다른 surrounding context (`record_id` 호출, 빈 줄, `assertIsNotNone(first_origin)`) 를 discriminator 로 사용해 세 개의 독립 Edit 로 정확히 매치.
   - 기존 `reload_origin` / `followup_origin` / `origin` 의 continuity 어서션 (`first_origin` 과 일치) 은 그대로 두고, 이 continuity 검사가 exact literal 에 자동으로 바인딩되도록 함.
5. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:6053`, `:6155`, `:6683`) 는 이미 literal 을 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 64 / 65 에서 잠근 count-summary `{0,0,5}` / 빈 progress / source_roles / answer_mode / source_paths 어서션은 전혀 건드리지 않음
   - noisy / actual-search / dual-probe / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization_includes_missing_only_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` → 일곱 테스트 모두 `ok` (신규 literal 어서션이 실제 zero-strong runtime 의 `"설명형 단일 출처"` 값과 initial serialization / click reload exact fields / natural reload exact fields / click reload follow-up / natural reload follow-up / natural reload second follow-up 모든 경로에서 정확히 일치함을 확인)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 일곱 anchor 만 재실행을 요구했고, 본 슬라이스는 그 일곱 테스트 안에서만 label 검사 라인을 정확히 교체/추가함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 literal 을 잠가둠
- CONTROL_SEQ 64 / 65 가 잠근 count-summary 체인 테스트 / follow-up 체인 테스트 — 본 슬라이스는 label 계약만 좁게 tighten 함

## 남은 리스크
- literal `"설명형 단일 출처"` exact equality 는 zero-strong entity-card runtime 이 이 문자열을 계속 방출한다는 가정에 의존. 향후 downgraded label 이 변경되면 일곱 테스트가 동시에 깨져 drift 를 가리킴 — 이것이 본 라운드의 설계 의도 (loose / baseline-only 검사가 숨기던 label drift 를 exact literal 로 노출).
- follow-up 테스트 세 개 (`:17827`, `:17974`, `:18053`) 는 `first_origin["verification_label"]` 과의 continuity 어서션을 그대로 두고 `first_origin` 자체를 literal 에 고정하는 구조. 이 방식은 기존 baseline-continuity 패턴을 보존하면서 literal 보증을 추가하는 minimal-diff 접근이며, 향후 follow-up 에서 label 이 drift 하면 continuity 어서션이 먼저 깨지면서 literal 어서션은 first_origin 이 여전히 유효한지만 체크함. 만약 first_origin 자체가 drift 하면 literal 어서션이 먼저 깨짐.
- `_assert_origin_and_sources` 헬퍼 (`:18104`) 는 여전히 `first_origin["verification_label"]` 을 참조하므로, 본 라운드의 literal 어서션이 각 호출마다 literal 값을 간접적으로 보장함. 헬퍼 자체를 수정하지 않은 이유는 handoff 가 "keep the existing ... assertions intact" 라고 했고 continuity 구조 자체는 유지되어야 하기 때문.
- CONTROL_SEQ 64 / 65 가 잠근 count-summary `{0,0,5}` / 빈 progress / source_roles / answer_mode / source_paths 어서션은 본 라운드에서 전혀 건드리지 않음. zero-strong 가족 전체가 browser literal + service literal + service count-summary + service progress 네 축에서 truth-synced 상태로 정합화됨.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64 (zero-strong missing-only chain) + CONTROL_SEQ 65 (zero-strong initial+reload anchors) + 본 CONTROL_SEQ 66 (zero-strong verification-label service continuity) 루프는 entity-card 가족 네 주요 분기를 count-summary + verification_label + progress + source_roles + answer_mode + source_paths 여섯 축에서 browser / service 층 truth-synced 로 완성함. latest-update / store-seeded / general 은 별도 slice 로 남아 있음.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
