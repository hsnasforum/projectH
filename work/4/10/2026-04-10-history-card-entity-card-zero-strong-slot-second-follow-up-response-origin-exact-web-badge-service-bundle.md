# history-card entity-card zero-strong-slot second-follow-up response-origin exact-web-badge service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 zero-strong entity-card second-follow-up 서비스 anchor 두 개를 제자리에서 tighten:
  - `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths` (`:17927`, click-reload second follow-up): CONTROL_SEQ 67 이 이미 추가한 세 어서션 (`answer_mode`, `verification_label`, `source_roles`) 앞에 `fourth_origin["badge"] == "WEB"` 어서션 한 줄을 추가.
  - `test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` (`:18094`, natural-reload second follow-up): `_assert_origin_and_sources(fourth, "second follow-up")` 호출 뒤에 inline literal 어서션 블록 네 건을 추가. 공유 helper `_assert_origin_and_sources` 는 수정하지 않음 — 그 helper 가 같은 테스트의 natural reload / first follow-up stage 도 덮고 있고 handoff 가 "do not broaden the helper for already-closed natural reload or first-follow-up stages" 라고 명시했기 때문.
  - 두 테스트 모두 네 literal 어서션 세트:
    - `fourth_origin["badge"] == "WEB"`
    - `fourth_origin["answer_mode"] == "entity_card"`
    - `fourth_origin["verification_label"] == "설명형 단일 출처"`
    - `fourth_origin["source_roles"] == ["백과 기반"]`
  - 기존 second-follow-up flow, `source_paths` 어서션, first stage 어서션, `_assert_origin_and_sources` helper 본문, `record_id` / stage 순서 등은 전혀 건드리지 않음.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 64-67 + CONTROL_SEQ 74-75 까지 진행돼 zero-strong 가족의 reload-only / first follow-up 경로와 count-summary / literal label / click-reload second follow-up 세 필드 closure 는 이미 literal exact 로 잠긴 상태였음.
- 그러나 zero-strong second-follow-up 두 anchor 에서 여전히 `badge` 필드가 검사되지 않는 상태였음:
  - `:17927` 의 click-reload second-follow-up 은 CONTROL_SEQ 67 에서 `answer_mode` / `verification_label` / `source_roles` 세 어서션만 추가했고 `badge` 는 누락됨.
  - `:18094` 의 natural-reload second-follow-up 은 공유 helper `_assert_origin_and_sources` 에 전적으로 의존하는데, 그 helper 가 `assertIn(answer_mode, ...)` inclusion + baseline-derived 비교만 수행하고 `badge` 는 검사하지 않음.
- browser 쪽은 `e2e/tests/web-smoke.spec.mjs:6410` / `:6913` 에서 second-follow-up UX 의 네 필드 exact contract 를 이미 잠가둔 상태.
- handoff 는 이 두 anchor 를 제자리에서 tighten 해 click-reload 경로는 `badge == "WEB"` 을 한 줄 추가하고, natural-reload 경로는 helper 를 건드리지 않고 second follow-up 단계에서만 inline literal 블록을 추가하도록 지시. 범위 밖은 browser / 신규 테스트 / reload-only / first follow-up / 다른 가족 / docs / pipeline.
- 본 라운드 이후 zero-strong 가족의 모든 reload stage (reload-only → first follow-up → second follow-up, click + natural 두 entry path) 에서 `response_origin` 네 필드가 literal exact 로 잠긴 상태가 완성됨.

## 핵심 변경
1. **`tests/test_web_app.py:17927` click-reload second follow-up in-place tightening**
   - CONTROL_SEQ 67 의 기존 3-line 어서션 블록 (`answer_mode` / `verification_label` / `source_roles`) 바로 앞에 `self.assertEqual(fourth_origin["badge"], "WEB")` 한 줄을 추가.
   - `fourth_origin = fourth["response"]["response_origin"]` 변수 획득, 기존 `source_paths` 어서션, stage flow, CONTROL_SEQ 67 의 주석은 모두 유지.
2. **`tests/test_web_app.py:18094` natural-reload second follow-up in-place tightening**
   - `_assert_origin_and_sources(fourth, "second follow-up")` 호출 직후에 네 literal exact 어서션 블록을 추가:
     - `fourth_origin = fourth["response"]["response_origin"]`
     - `assertEqual(fourth_origin["badge"], "WEB")`
     - `assertEqual(fourth_origin["answer_mode"], "entity_card")`
     - `assertEqual(fourth_origin["verification_label"], "설명형 단일 출처")`
     - `assertEqual(fourth_origin["source_roles"], ["백과 기반"])`
   - 설명형 주석으로 이 어서션이 browser smoke contract 와 truth-synced 임과, helper `_assert_origin_and_sources` 를 건드리지 않는 이유 (같은 helper 가 natural reload 와 first follow-up 등 이미 닫힌 stage 도 덮고 있어 helper 확장 시 scope 가 넓어짐) 를 명시.
   - 공유 helper 본문은 전혀 수정하지 않음. natural reload / first follow-up stage 의 기존 어서션은 그대로 유지.
3. **helper 재사용 여부**
   - natural-reload 경로에서 helper 확장 대신 inline literal 블록을 선택한 이유는 handoff 가 "do not broaden the helper for already-closed natural reload or first-follow-up stages" + "prefer adding a direct literal assertion block for `fourth["response"]["response_origin"]` after `_assert_origin_and_sources(fourth, "second follow-up")`" 라고 명시했기 때문. 이 접근은 CONTROL_SEQ 67-75 의 minimal inline 패턴과 일관됨.
4. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:6410`, `:6913`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 64 의 zero-strong follow-up / second follow-up chain tests, CONTROL_SEQ 65 의 initial serialization / count-summary anchors, CONTROL_SEQ 66 의 literal label tests, CONTROL_SEQ 67 의 click-reload second follow-up closure (본 라운드는 그 closure 에 `badge` 만 한 줄 추가), CONTROL_SEQ 74 의 reload-only two entry paths, CONTROL_SEQ 75 의 first-follow-up two entry paths 는 모두 건드리지 않음
   - dual-probe / actual-search / noisy / latest-update / store-seeded / general 테스트와 `_assert_origin_and_sources` helper 본문은 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` → 두 테스트 모두 `ok` (신규 `badge == "WEB"` 어서션과 natural-reload inline literal 블록이 실제 runtime 의 second follow-up `response_origin` 과 정확히 일치)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 second follow-up stage 의 literal 어서션을 좁게 추가함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 zero-strong second-follow-up contract 를 두 경로 모두에서 잠가둠
- 이미 닫힌 zero-strong anchor 들 (CONTROL_SEQ 64-67, CONTROL_SEQ 74-75) 과 dual-probe / actual-search 가족 anchor 들, 공유 helper `_assert_origin_and_sources` 의 다른 호출 지점 — 본 슬라이스는 zero-strong second follow-up stage 두 경로만 targets 함

## 남은 리스크
- 신규 `fourth_origin["badge"] == "WEB"` 어서션은 zero-strong runtime 이 second follow-up 단계에서도 `badge` 필드를 `"WEB"` 로 방출한다는 가정에 의존. drift 시 본 어서션이 먼저 깨져 browser smoke 와 silent 어긋남을 방지함.
- natural-reload 테스트의 `_assert_origin_and_sources(fourth, "second follow-up")` 호출은 여전히 helper 를 통해 baseline-derived 비교를 수행하지만, 본 라운드의 inline literal 블록이 그 뒤에 뒤따르며 second follow-up 단계만 네 필드 literal 로 잠금. 따라서 second follow-up stage 에서는 helper 와 inline 블록 모두 동시에 통과해야 함 — helper 쪽의 baseline-derived 검사는 CONTROL_SEQ 66 이 baseline literal (`"설명형 단일 출처"`) 을 이미 잠가뒀기 때문에 실질적으로 literal 비교와 같은 drift coverage 를 가짐.
- 공유 helper 를 확장하지 않은 결정은 의도적 — helper 확장 시 natural reload / first follow-up stage 까지 영향이 퍼져 범위를 넘어섬. 향후 natural reload 나 first follow-up 의 다른 필드도 literal 로 tighten 이 필요해지면 helper 승격 검토.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64-67 (zero-strong full chain + literal label + click-reload second follow-up three-field closure) + CONTROL_SEQ 68-71 (actual-search all reload stages + two entry paths) + CONTROL_SEQ 72-73 (dual-probe first follow-up + reload-only two entry paths) + CONTROL_SEQ 74-75 (zero-strong reload-only + first-follow-up two entry paths) + 본 CONTROL_SEQ 76 (zero-strong second follow-up `badge` closure) 루프는 entity-card 가족 네 주요 분기의 모든 reload stage 에서 네 필드 literal exact 를 browser + service 양쪽에서 완전 정합화함. 남은 가족은 noisy entity-card / latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
