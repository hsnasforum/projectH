# history-card entity-card actual-search natural-reload first-follow-up response-origin service closure

## 변경 파일
- `tests/test_web_app.py` — 기존 `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin` (`:18535`) 의 first follow-up 블록에서 loose response-origin 검사 세 줄을 literal exact 어서션 네 줄로 교체:
  - 제거: `assertIsNotNone(followup_origin)` + `assertIn(followup_origin.get("answer_mode", ""), ("entity_card", first_origin["answer_mode"]))` + `assertEqual(followup_origin["verification_label"], first_origin["verification_label"])` + `assertEqual(followup_origin["source_roles"], first_origin["source_roles"])`
  - 추가: `followup_origin = third["response"]["response_origin"]` + 네 literal exact 어서션:
    - `assertEqual(followup_origin["badge"], "WEB")`
    - `assertEqual(followup_origin["answer_mode"], "entity_card")`
    - `assertEqual(followup_origin["verification_label"], "설명형 다중 출처 합의")`
    - `assertEqual(followup_origin["source_roles"], ["백과 기반"])`
  - `first_origin = first["response"]["response_origin"]` 변수 파생은 이후 사용처가 없어져 제거. `record_id` 파생과 natural reload → first follow-up stage 흐름 (`first` / `second` / `third` handle_chat 호출) 은 그대로 유지.
  - 설명형 주석으로 이 어서션이 browser smoke (`e2e/tests/web-smoke.spec.mjs:8189`, contract `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `백과 기반`) 및 CONTROL_SEQ 69 의 click-reload first follow-up closure (`:9486`) 의 minimal inline 패턴과 truth-synced 임을 명시.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 68 (click-reload second follow-up response-origin closure) + CONTROL_SEQ 69 (click-reload first follow-up response-origin closure) + CONTROL_SEQ 70 (reload-only two entry paths response-origin exactness + `badge == "WEB"`) 까지 진행돼 actual-search 가족의 click-reload chain 과 reload-only 두 경로가 service 층에서 literal exact `WEB` / `entity_card` / `설명형 다중 출처 합의` / `["백과 기반"]` 에 합의하는 상태가 되었음.
- 그러나 actual-search 가족의 **natural-reload first follow-up** 단계 (`tests/test_web_app.py:18535`) 는 여전히 loose 상태:
  - `badge` 필드 검사 없음
  - `answer_mode` 를 `assertIn(..., ("entity_card", first_origin["answer_mode"]))` 로 inclusion 비교 → literal `"entity_card"` 가 아닌 값으로도 통과 가능
  - `verification_label` / `source_roles` 를 `first_origin` baseline 과 일치 비교 → initial 자체가 drift 하면 silently 통과
- browser 쪽은 `e2e/tests/web-smoke.spec.mjs:8189` 에서 natural-reload first follow-up UX 의 exact contract 를 이미 잠가둔 상태.
- natural-reload second follow-up (`:18606`) 은 이미 exact 상태 — handoff 는 "Do not touch the already-closed natural-reload second-follow-up exactness test at `:18606`" 라고 명시.
- handoff 는 이 한 anchor 를 제자리에서 tighten 해 first follow-up `third["response"]["response_origin"]` 네 필드를 literal exact 로 잠그되, natural reload → first follow-up 흐름은 그대로 두고 범위 밖 (browser / 신규 테스트 / reload-only / second follow-up / click-reload / 다른 가족 / docs / pipeline) 은 건드리지 않도록 지시.
- 본 라운드 이후 actual-search 가족의 모든 reload stage (reload-only click + natural → first follow-up click + natural → second follow-up click + natural) 에서 `response_origin` 네 필드가 literal exact 로 잠긴 상태가 됨. 가족 level 에서 browser + service 양쪽의 모든 reload 경로가 truth-synced.

## 핵심 변경
1. **`tests/test_web_app.py:18535` first follow-up 블록 in-place tightening**
   - `first["ok"]` 검사 직후의 `first_origin = first["response"]["response_origin"]` 변수 파생을 제거 (이후 사용처가 없어짐). `record_id = first["session"]["web_search_history"][0]["record_id"]` 는 그대로 유지 (second/third handle_chat 호출의 `load_web_search_record_id` 에 필요).
   - `third = service.handle_chat(...)` + `assertTrue(third["ok"])` 뒤의 followup_origin 블록을 교체:
     - 제거: `assertIsNotNone(followup_origin)` + `assertIn(followup_origin.get("answer_mode", ""), ("entity_card", first_origin["answer_mode"]))` + 두 baseline-derived 어서션
     - 추가: `followup_origin = third["response"]["response_origin"]` + 네 literal 어서션 (`badge`, `answer_mode`, `verification_label`, `source_roles`)
   - 설명형 주석으로 browser smoke (`:8189`) contract 와 CONTROL_SEQ 69 의 click-reload first follow-up closure 의 minimal inline 패턴과의 정합성 의도 명시
   - natural reload (`second`) stage 는 전혀 건드리지 않음. reload-only natural-reload test 는 CONTROL_SEQ 70 이 이미 literal exact 로 잠가둠.
2. **helper 재사용 여부**
   - handoff 가 "remove `first_origin` only if it becomes unused after the tightening" 와 "keep the diff small" 을 명시. CONTROL_SEQ 67-70 과 동일하게 helper 를 도입하지 않고 네 줄 inline 어서션으로 minimal-diff 유지.
3. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:8189`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 68 의 `:17409` click-reload second follow-up closure, CONTROL_SEQ 69 의 `:9486` click-reload chain first follow-up closure, CONTROL_SEQ 70 의 `:8906` + `:9275` reload-only anchors, `:18606` natural-reload second follow-up anchor 는 모두 건드리지 않음
   - zero-strong / dual-probe / noisy / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin` → `ok` (신규 네 literal 어서션이 실제 actual-search natural-reload first follow-up runtime 의 `response_origin` 과 정확히 일치: `badge == "WEB"`, `answer_mode == "entity_card"`, `verification_label == "설명형 다중 출처 합의"`, `source_roles == ["백과 기반"]`)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 한 anchor 만 재실행을 요구했고, 본 슬라이스는 그 테스트 안에 네 줄짜리 어서션을 교체함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 actual-search natural-reload first follow-up contract 를 잠가둠
- 이미 닫힌 anchor 들 (CONTROL_SEQ 68/69/70 + `:18606`) — 본 슬라이스는 natural-reload first follow-up stage 하나만 targets 함

## 남은 리스크
- 신규 네 exact 어서션은 actual-search runtime 이 natural-reload first follow-up 단계에서도 `badge="WEB"` / `answer_mode="entity_card"` / `verification_label="설명형 다중 출처 합의"` / `source_roles=["백과 기반"]` 를 방출한다는 가정에 의존. drift 시 본 어서션이 먼저 깨져 browser smoke 와 silent 어긋남을 방지함.
- `first_origin` 변수 제거로 first response 의 `response_origin` 값 자체를 직접 검사하지 않게 됨. 첫 응답의 drift 는 다른 initial-response anchor (`:9354` 등 CONTROL_SEQ 62 에서 잠근 chain 테스트의 first_history 어서션) 가 1차로 방어함. 본 라운드는 first follow-up 단계만 targets 함.
- `assertIsNotNone(followup_origin)` 을 제거했지만, `followup_origin` 이 `None` 이면 literal exact equality 가 즉시 `TypeError` / `AssertionError` 로 실패하므로 guard 가 불필요. 기존 테스트가 `third["ok"]` 를 이미 검사하므로 response_origin 이 누락된 상태로 통과하지 않음.
- `second` (natural reload) stage 는 본 라운드에서 직접 잠기지 않음. natural-reload reload-only 는 CONTROL_SEQ 70 의 `:9275` 가 literal exact 로 잠가둔 상태이며, 본 라운드는 first follow-up (`third`) stage 한 곳만 targets 함.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64-67 (zero-strong full chain) + CONTROL_SEQ 68 (actual-search click-reload second follow-up) + CONTROL_SEQ 69 (actual-search click-reload first follow-up) + CONTROL_SEQ 70 (actual-search reload-only two entry paths) + 본 CONTROL_SEQ 71 (actual-search natural-reload first follow-up) 루프는 entity-card 가족 네 주요 분기 + actual-search 모든 reload stage (reload-only → first follow-up → second follow-up, click + natural 두 entry path) 까지 browser + service 양쪽에서 완전 정합화함. 남은 가족은 latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
