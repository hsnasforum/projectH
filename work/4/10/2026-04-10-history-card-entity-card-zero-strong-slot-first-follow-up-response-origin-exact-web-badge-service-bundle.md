# history-card entity-card zero-strong-slot first-follow-up response-origin exact-web-badge service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 zero-strong entity-card first-follow-up 서비스 anchor 두 개의 loose response-origin 블록을 literal exact 어서션으로 교체:
  - `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_follow_up_preserves_stored_response_origin` (`:17859`, click-reload first follow-up): `reload_origin = second["response"]["response_origin"]` 이후 loose 블록 (`assertIsNotNone` + inclusion `answer_mode` + baseline-derived `verification_label` / `source_roles`) 을 네 literal exact 어서션으로 교체.
  - `test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin` (`:18014`, natural-reload first follow-up): 같은 구조의 `followup_origin = third["response"]["response_origin"]` 블록을 같은 방식으로 네 literal exact 어서션으로 교체.
  - 두 테스트 모두 네 literal 어서션:
    - `badge == "WEB"` (신규)
    - `answer_mode == "entity_card"` (inclusion → literal)
    - `verification_label == "설명형 단일 출처"` (baseline-derived → literal)
    - `source_roles == ["백과 기반"]` (baseline-derived → literal)
  - 기존 follow-up 흐름, `load_web_search_record_id` 라우팅, `followup_source_paths` 어서션 (`namu.wiki/testgame` / `ko.wikipedia.org/testgame`) 은 전혀 건드리지 않음. CONTROL_SEQ 66 의 first 단계 `first_origin["verification_label"] == "설명형 단일 출처"` 어서션은 그대로 유지.
  - `first_origin` 변수는 두 테스트 모두 first 단계의 literal 검사에 여전히 쓰이므로 제거하지 않음.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 64-67 이 zero-strong 가족의 follow-up chain / count-summary / literal label / click-reload second follow-up closure 를 잠갔고, CONTROL_SEQ 74 가 zero-strong reload-only 두 anchor 를 네 literal exact 로 잠갔음.
- 그러나 zero-strong first-follow-up 두 anchor (`:17859`, `:18014`) 는 여전히 loose:
  - `assertIn(reload_origin.get("answer_mode", ""), ("entity_card", first_origin["answer_mode"]))` inclusion 비교 → literal `"entity_card"` 가 아닌 값으로도 통과 가능
  - `verification_label` / `source_roles` 가 `first_origin` baseline 과 일치 비교 → baseline literal 이 CONTROL_SEQ 66 으로 이미 잠기긴 했지만 reload 블록에서 직접 literal 을 검사하지 않음
  - `badge` 필드 검사 없음
- browser 쪽은 `e2e/tests/web-smoke.spec.mjs:6293` / `:6791` 에서 zero-strong first-follow-up UX 의 exact contract (`WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`) 를 이미 잠가둔 상태.
- zero-strong second-follow-up 은 이미 `:18009` / `:18094` 에서 exact — handoff 가 "Do not touch the already-closed zero-strong reload-only or second-follow-up anchors" 명시.
- handoff 는 이 두 anchor 를 제자리에서 tighten 해 zero-strong first-follow-up 두 entry path 모두에서 browser smoke contract 와 같은 네 필드로 literal exact 잠그도록 지시. 범위 밖은 browser / 신규 테스트 / reload-only / second follow-up / 다른 가족 / docs / pipeline.
- 본 라운드 이후 zero-strong 가족의 모든 reload stage (reload-only → first follow-up → second follow-up, click + natural 두 entry path) 에서 `response_origin` 네 필드가 literal exact 로 잠긴 상태가 됨. actual-search (CONTROL_SEQ 68-71) / dual-probe (CONTROL_SEQ 72-73) / zero-strong (CONTROL_SEQ 74 + 본 라운드) 세 가족 모두 동일 완성도의 reload chain coverage 를 갖게 됨.

## 핵심 변경
1. **`tests/test_web_app.py:17859` click-reload first-follow-up in-place tightening**
   - 제거: `reload_origin` 획득 뒤 `assertIsNotNone(reload_origin)` + `assertIn(reload_origin.get("answer_mode", ""), ("entity_card", first_origin["answer_mode"]))` + 두 baseline-derived 어서션
   - 유지 + 추가: `reload_origin = second["response"]["response_origin"]` + `assertEqual(reload_origin["badge"], "WEB")` + `assertEqual(reload_origin["answer_mode"], "entity_card")` + `assertEqual(reload_origin["verification_label"], "설명형 단일 출처")` + `assertEqual(reload_origin["source_roles"], ["백과 기반"])`
   - 이후 `followup_source_paths` 어서션 두 줄은 그대로 유지
2. **`tests/test_web_app.py:18014` natural-reload first-follow-up in-place tightening**
   - 같은 구조의 `followup_origin = third["response"]["response_origin"]` 블록을 같은 방식으로 교체 (`reload_origin` 대신 `followup_origin` 변수명, `second` 대신 `third` result)
   - 이후 `followup_source_paths` 어서션 두 줄은 그대로 유지
   - 두 테스트의 블록은 변수명이 달라서 `replace_all` 을 쓸 수 없고 targeted edit 두 번으로 정확히 분리 패치. CONTROL_SEQ 73 의 replace_all 부작용 교훈 반영.
3. **helper 재사용 여부**
   - CONTROL_SEQ 67-74 와 동일하게 helper 를 도입하지 않고 네 줄 inline literal 어서션 유지. `first_origin` 변수는 두 테스트 모두 first 단계 `assertEqual(first_origin["verification_label"], "설명형 단일 출처")` (CONTROL_SEQ 66) 에 여전히 쓰이므로 제거하지 않음.
4. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:6293`, `:6791`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 64 의 zero-strong follow-up / second follow-up chain tests, CONTROL_SEQ 65 의 initial serialization / count-summary anchors, CONTROL_SEQ 66 의 literal label tests, CONTROL_SEQ 67 의 click-reload second follow-up closure, CONTROL_SEQ 74 의 reload-only two entry paths 는 모두 건드리지 않음
   - dual-probe / actual-search / noisy / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin` → 두 테스트 모두 `ok` (신규 네 literal 어서션이 실제 zero-strong first-follow-up runtime 의 `response_origin` 과 정확히 일치)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 first-follow-up response-origin 블록을 tighten 함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 zero-strong first-follow-up contract 를 두 경로 모두에서 잠가둠
- 이미 닫힌 zero-strong anchor 들 (CONTROL_SEQ 64-67, CONTROL_SEQ 74) 과 dual-probe / actual-search 가족 anchor 들 — 본 슬라이스는 zero-strong first-follow-up stage 두 경로만 targets 함

## 남은 리스크
- 신규 네 literal 어서션은 zero-strong runtime 이 first-follow-up 단계에서도 `badge="WEB"` / `answer_mode="entity_card"` / `verification_label="설명형 단일 출처"` / `source_roles=["백과 기반"]` 를 방출한다는 가정에 의존. drift 시 본 어서션이 먼저 깨져 browser smoke 와 silent 어긋남을 방지함.
- `assertIsNotNone(reload_origin)` / `assertIsNotNone(followup_origin)` 을 제거했지만, `None` 이면 literal exact equality 가 즉시 실패하므로 guard 가 불필요. 기존 테스트가 `second["ok"]` / `third["ok"]` 를 이미 검사함.
- `first_origin` 은 두 테스트 모두 first 단계 literal 검사로 여전히 쓰임. 본 라운드는 first_origin 을 제거하지 않고 유지.
- CONTROL_SEQ 73 의 replace_all 부작용 교훈을 따라 두 테스트의 블록 (변수명 `reload_origin` vs `followup_origin`) 을 targeted edit 두 번으로 정확히 분리 패치. 다른 가족 테스트에 영향 없음.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64-67 (zero-strong full chain + literal label + click-reload second follow-up closure) + CONTROL_SEQ 68-71 (actual-search all reload stages + two entry paths) + CONTROL_SEQ 72-73 (dual-probe first follow-up + reload-only two entry paths) + CONTROL_SEQ 74 (zero-strong reload-only two entry paths) + 본 CONTROL_SEQ 75 (zero-strong first-follow-up two entry paths) 루프는 entity-card 가족 네 주요 분기 (actual-search / dual-probe / zero-strong / noisy) 의 모든 reload stage 를 browser + service 양쪽에서 완전 정합화함. 남은 가족은 latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
