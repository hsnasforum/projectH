# history-card entity-card dual-probe first-follow-up response-origin service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 dual-probe entity-card first-follow-up 서비스 anchor 두 개를 제자리에서 tighten:
  - `test_handle_chat_dual_probe_entity_card_history_card_reload_second_follow_up_preserves_mixed_count_summary` (`:9797`, click-reload chain): first follow-up stage (`third = service.handle_chat(...)` + `_assert_mixed_count_summary_continuity(third, "first follow-up")` 직후) 에 exact `third_origin` 어서션 네 건을 추가:
    - `third_origin["badge"] == "WEB"`
    - `third_origin["answer_mode"] == "entity_card"`
    - `third_origin["verification_label"] == "설명형 다중 출처 합의"`
    - `third_origin["source_roles"] == ["공식 기반", "백과 기반"]`
  - `test_handle_chat_dual_probe_natural_reload_follow_up_preserves_response_origin` (`:18311`, natural-reload first follow-up): 기존 loose response-origin 블록 (`assertIsNotNone` + inclusion `answer_mode` + baseline-derived `verification_label` / `source_roles`) 을 네 literal exact 어서션으로 교체. `first_origin = first["response"]["response_origin"]` 변수 파생은 사용처가 없어져 제거. `record_id` 파생과 natural reload → first follow-up 흐름은 유지.
  - 두 테스트 모두 기존 mixed-count `{strong:1, weak:4, missing:0}` + 빈 progress + `verification_label == "설명형 다중 출처 합의"` history summary / second follow-up stage / `actions_taken` routing / `active_context.source_paths` 어서션은 전혀 건드리지 않음.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 63 (dual-probe mixed-count chain exact `{1,4,0}`) 이후 dual-probe 가족의 reload-only (`:9627` / `:10003`) 및 second follow-up (`:17346` / `:18406`) anchor 들은 이미 exact response-origin 으로 잠긴 상태였음.
- 그러나 first follow-up stage 의 두 anchor 는 여전히 loose:
  - `:9797` 는 click-reload mixed-count chain 을 이미 stage-level history summary exact 로 잠갔지만 `third["response"]["response_origin"]` 은 직접 검사하지 않음.
  - `:18302` 은 natural-reload follow-up response-origin 을 `assertIn(answer_mode, ("entity_card", first_origin["answer_mode"]))` inclusion 비교 + `verification_label` / `source_roles` 를 baseline-derived 로만 비교 + `badge` 필드 검사 없음.
- browser 쪽은 `e2e/tests/web-smoke.spec.mjs:5489` / `:7924` 에서 dual-probe first follow-up UX (`WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반 · 백과 기반`) 를 이미 잠가둔 상태. dual-probe 가 actual-search 와 다른 점은 `source_roles == ["공식 기반", "백과 기반"]` 두 entry list 로 다중 role 을 가진다는 점.
- handoff 는 이 두 anchor 를 제자리에서 tighten 해 dual-probe first follow-up 을 두 reload entry path (click + natural) 모두에서 browser smoke contract 와 같은 네 필드로 literal exact 잠그도록 지시. 범위 밖은 browser / 신규 테스트 / reload-only / second follow-up / actual-search 가족 / docs / pipeline.
- 본 라운드 이후 dual-probe 가족의 모든 reload stage (reload-only → first follow-up → second follow-up, click + natural 두 entry path) 에서 `response_origin` 네 필드가 literal exact 로 잠긴 상태가 됨. actual-search 가족 CONTROL_SEQ 68-71 과 같은 진행 패턴으로 dual-probe 가족의 reload chain 이 완성됨.

## 핵심 변경
1. **`tests/test_web_app.py:9797` click-reload chain first follow-up in-place tightening**
   - `third = service.handle_chat(...)` + `_assert_mixed_count_summary_continuity(third, "first follow-up")` 뒤, `fourth = service.handle_chat(...)` 호출 이전 지점에 네 exact 어서션을 삽입:
     - `third_origin = third["response"]["response_origin"]`
     - `assertEqual(third_origin["badge"], "WEB")`
     - `assertEqual(third_origin["answer_mode"], "entity_card")`
     - `assertEqual(third_origin["verification_label"], "설명형 다중 출처 합의")`
     - `assertEqual(third_origin["source_roles"], ["공식 기반", "백과 기반"])`
   - 설명형 주석으로 browser smoke (`:5489`, `:7924`) contract 와 CONTROL_SEQ 69 의 actual-search click-reload first follow-up closure (`:9486`) 의 minimal inline 패턴과의 정합성 의도 명시
   - show-only reload (`second`) / second follow-up (`fourth`) stage 의 helper 호출 및 기존 어서션은 전혀 수정하지 않음
2. **`tests/test_web_app.py:18311` natural-reload first follow-up in-place tightening**
   - `first_origin = first["response"]["response_origin"]` 변수 파생 제거 (이후 사용처가 없어짐)
   - `third = service.handle_chat(...)` + `assertTrue(third["ok"])` 뒤의 followup_origin 블록을 교체:
     - 제거: `followup_origin = third["response"]["response_origin"]` + `assertIsNotNone(followup_origin)` + `assertIn(followup_origin.get("answer_mode", ""), ("entity_card", first_origin["answer_mode"]))` + 두 baseline-derived 어서션
     - 추가: `followup_origin = third["response"]["response_origin"]` + 네 literal 어서션 (`badge`, `answer_mode`, `verification_label`, `source_roles`)
   - 설명형 주석으로 browser smoke + CONTROL_SEQ 71 의 actual-search natural-reload first follow-up closure (`:18535`) 패턴과의 정합성 의도 명시
   - `second` (natural reload) stage 와 `record_id` 파생은 전혀 건드리지 않음. natural-reload reload-only 단계는 별도 anchor 가 담당.
3. **helper 재사용 여부**
   - handoff 가 "remove `first_origin` only if it becomes unused after the tightening" + "keep the diff small" 을 명시. CONTROL_SEQ 67-71 과 동일하게 helper 를 도입하지 않고 네 줄 inline 어서션으로 minimal-diff 유지.
4. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:5489`, `:7924`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 63 의 dual-probe mixed-count chain history summary 어서션은 건드리지 않음
   - `:9627` / `:10003` dual-probe reload-only exact-fields tests 와 `:17346` / `:18406` dual-probe second follow-up exactness tests 는 모두 건드리지 않음 (handoff 명시)
   - actual-search / zero-strong / noisy / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_card_history_card_reload_second_follow_up_preserves_mixed_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_follow_up_preserves_response_origin` → 두 테스트 모두 `ok` (신규 네 exact 어서션이 실제 dual-probe first follow-up runtime 의 `response_origin` 과 정확히 일치: `badge == "WEB"`, `answer_mode == "entity_card"`, `verification_label == "설명형 다중 출처 합의"`, `source_roles == ["공식 기반", "백과 기반"]`)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 first follow-up stage 의 response_origin 블록을 tighten 함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 dual-probe first follow-up contract 를 두 경로 모두에서 잠가둠
- 이미 닫힌 dual-probe anchor 들 (`:9627`, `:10003`, `:17346`, `:18406`) 과 actual-search 가족 anchor 들 — 본 슬라이스는 dual-probe first follow-up stage 두 경로만 targets 함

## 남은 리스크
- 신규 `source_roles == ["공식 기반", "백과 기반"]` 어서션은 dual-probe runtime 이 두 role 을 이 순서로 방출한다는 가정에 의존. browser smoke 의 `공식 기반 · 백과 기반` 배지 ordering 과 CONTROL_SEQ 63 / 기존 reload-only / second follow-up anchor 들의 ordering 이 같은 순서를 이미 잠가두고 있음. ordering 이 바뀌면 본 어서션이 먼저 깨져 drift 를 가리킴.
- `first_origin` 변수 제거로 first response 의 `response_origin` 값 자체를 직접 검사하지 않게 됨. 첫 응답의 drift 는 다른 initial-response anchor (CONTROL_SEQ 63 의 `:9787` / `:9912` 에서 잠근 dual-probe chain 테스트의 baseline_entry 어서션) 가 1차로 방어함. 본 라운드는 first follow-up stage 만 targets 함.
- `assertIsNotNone(followup_origin)` 을 제거했지만, `None` 이면 literal exact equality 가 즉시 실패하므로 guard 가 불필요. 기존 테스트가 `third["ok"]` 를 이미 검사함.
- click-reload chain 의 second follow-up 단계 (`:9797` 안의 `fourth`) 는 본 라운드에서 `response_origin` 을 직접 잠그지 않음. 기존 `_assert_mixed_count_summary_continuity` 헬퍼가 stage-level history summary 만 검사하므로 second follow-up response_origin 의 drift 는 `:17346` / `:18406` 의 별도 anchor 가 담당함.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64-67 (zero-strong full chain) + CONTROL_SEQ 68-71 (actual-search all reload stages + two entry paths) + 본 CONTROL_SEQ 72 (dual-probe first follow-up two entry paths) 루프는 entity-card 가족 네 주요 분기 + actual-search 모든 reload stage + dual-probe first follow-up 을 browser + service 양쪽에서 정합화함. 남은 dual-probe 가족의 stage 는 이미 reload-only / second follow-up 이 별도 anchor 로 잠겨 있음. 다른 가족은 latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
