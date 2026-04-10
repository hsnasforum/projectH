# history-card entity-card actual-search reload-only response-origin exact-web-badge service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 actual-search entity-card reload-only 서비스 테스트 두 개의 `response_origin` 어서션을 shipped literal 계약에 맞춰 tighten:
  - `test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths` (`:8906`, click reload via `load_web_search_record_id`): 기존 `answer_mode` / `verification_label` / `source_roles` 세 어서션은 그대로 두고, `reload_origin["badge"] == "WEB"` 어서션을 `answer_mode` 직전에 한 줄 추가.
  - `test_handle_chat_actual_entity_search_natural_reload_exact_fields` (`:9275`, natural reload via `"방금 검색한 결과 다시 보여줘"`): `first_origin` 파생 제거, baseline-derived `verification_label` / `source_roles` 비교를 literal direct 비교로 교체하고 `badge == "WEB"` 어서션 한 줄 추가. 결과적으로 네 필드 모두 literal exact 비교:
    - `reload_origin["badge"] == "WEB"`
    - `reload_origin["answer_mode"] == "entity_card"`
    - `reload_origin["verification_label"] == "설명형 다중 출처 합의"`
    - `reload_origin["source_roles"] == ["백과 기반"]`
  - 두 테스트 모두 기존 reload flow, `active_context.source_paths` 어서션, `web_search_record_path` 일치 어서션, exact history summary (`{strong:3, weak:0, missing:2}`, 빈 progress, `설명형 다중 출처 합의`) 는 전혀 건드리지 않음.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 68 (click-reload second follow-up response-origin closure) + CONTROL_SEQ 69 (click-reload first follow-up response-origin closure) 이 actual-search 가족의 click-reload chain 중 first / second follow-up 두 stage 를 browser smoke contract (`WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`) 와 같은 네 필드로 잠갔음.
- 그러나 actual-search 가족의 **reload-only** 단계 (click-reload 와 natural-reload 두 경로 모두) 에서는 service-side `response_origin.badge == "WEB"` 를 직접 잠그는 어서션이 아직 없었음:
  - `:8906` 은 `answer_mode` / `verification_label` / `source_roles` + exact history summary 는 이미 잠가둔 상태지만 `badge` 필드는 검사하지 않음.
  - `:9275` 은 `verification_label` / `source_roles` 를 baseline-derived (`first_origin` 과의 일치) 로만 비교해서 initial 자체가 drift 하면 silently 통과할 수 있고, `badge` 필드는 역시 검사하지 않음.
- browser 쪽은 `e2e/tests/web-smoke.spec.mjs:2977` 에서 reload-only actual-search UX 의 exact contract 를 이미 잠가둔 상태.
- handoff 는 이 두 anchor 를 제자리에서 tighten 해 두 reload entry path (click / natural) 가 모두 literal `WEB` + `entity_card` + `설명형 다중 출처 합의` + `["백과 기반"]` 에 합의하도록 지시. 범위 밖은 browser / 신규 테스트 / follow-up / second follow-up / 다른 가족 / docs / pipeline.
- 본 라운드 이후 actual-search 가족의 모든 reload stage (reload-only → first follow-up → second follow-up, 두 entry path 모두) 에서 `response_origin` 네 필드가 literal exact 로 잠긴 상태가 됨. click-reload chain 은 CONTROL_SEQ 68/69/본 라운드로, natural-reload chain 은 기존 `:18525` + 본 라운드로 완성.

## 핵심 변경
1. **`tests/test_web_app.py:8906` in-place tightening**
   - 기존 `reload_origin = second["response"]["response_origin"]` 뒤에 `self.assertEqual(reload_origin["badge"], "WEB")` 어서션을 `answer_mode` 어서션 바로 앞 한 줄에 삽입.
   - 기존 `answer_mode` / `verification_label` / `source_roles` 어서션 + `reload_entry` history summary 어서션 (count-summary exact, 빈 progress, verification_label literal) 은 모두 그대로 유지.
   - 기존 `active_context.source_paths` 어서션, reload flow (`first` → `second = service.handle_chat(..., load_web_search_record_id=record_id)`), `actions_taken == ["load_web_search_record"]` 검사는 전혀 수정하지 않음.
2. **`tests/test_web_app.py:9275` in-place tightening**
   - `first_origin = first["response"]["response_origin"]` 변수 파생을 제거 (이후 사용처가 없어짐). `first_record_path = first["response"]["web_search_record_path"]` 는 그대로 유지 (`web_search_record_path` 일치 어서션에서 사용).
   - `reload_origin` 비교 블록을 네 줄 literal exact 비교로 교체:
     - `assertEqual(reload_origin["badge"], "WEB")` (신규)
     - `assertEqual(reload_origin["answer_mode"], "entity_card")` (그대로)
     - `assertEqual(reload_origin["verification_label"], "설명형 다중 출처 합의")` (`first_origin["verification_label"]` 비교에서 literal 로 교체)
     - `assertEqual(reload_origin["source_roles"], ["백과 기반"])` (`first_origin["source_roles"]` 비교에서 literal 로 교체)
   - 기존 `second["response"]["web_search_record_path"] == first_record_path` 어서션 (natural reload 가 stored record 경로를 재사용하는지 확인) 은 그대로 유지.
   - 기존 reload_entry history summary 어서션 (count-summary exact, 빈 progress, verification_label literal) 은 전혀 건드리지 않음.
3. **helper 재사용 여부**
   - handoff 가 "keep the diff small" + minimal inline 패턴 유지를 명시. CONTROL_SEQ 67/68/69 와 동일하게 helper 를 도입하지 않음.
4. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:2977`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 68 의 `:17409` second follow-up closure 와 CONTROL_SEQ 69 의 `:9486` click-reload chain first follow-up closure 는 건드리지 않음
   - natural-reload actual-search follow-up anchor (`:18525`) 는 이미 강한 상태 — 건드리지 않음
   - zero-strong / dual-probe / noisy / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_exact_fields` → 두 테스트 모두 `ok` (신규 `badge == "WEB"` 어서션이 click-reload runtime 에서 통과, 네 필드 literal exact 비교가 natural-reload runtime 의 `reload_origin` 과 정확히 일치)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 reload_origin 비교를 tighten 함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 actual-search reload-only contract 를 잠가둠
- 이미 닫힌 follow-up / second follow-up anchor들 — 본 슬라이스는 reload-only stage 두 경로만 targets 함

## 남은 리스크
- 신규 `reload_origin["badge"] == "WEB"` 어서션은 actual-search runtime 이 reload-only 단계에서도 `badge` 필드를 `"WEB"` 로 방출한다는 가정에 의존. browser smoke 와 CONTROL_SEQ 68/69 가 이미 동일 literal 에 합의하고 있으므로 drift 시 본 어서션이 먼저 깨져 silent 어긋남을 방지함.
- natural-reload 테스트에서 `first_origin` 변수 파생을 제거하면서 first response 의 `response_origin` 값 자체를 직접 검사하지 않게 됨. 첫 응답의 drift 는 다른 initial-response anchor (`tests/test_web_app.py:9354` 등 CONTROL_SEQ 62 에서 잠근 chain 테스트의 first_history 어서션) 가 1차로 방어함. 본 라운드는 reload 단계만 targets 함.
- `web_search_record_path == first_record_path` 어서션은 그대로 유지되므로 natural-reload 가 새 record 를 저장하지 않고 기존 record 를 재사용한다는 계약은 여전히 잠겨 있음.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64-67 (zero-strong full chain) + CONTROL_SEQ 68 (actual-search click-reload second follow-up) + CONTROL_SEQ 69 (actual-search click-reload first follow-up) + 본 CONTROL_SEQ 70 (actual-search reload-only two entry paths) 루프는 entity-card 가족 네 주요 분기의 모든 reload stage (reload-only → first follow-up → second follow-up, click-reload + natural-reload 두 entry path) 까지 browser + service 양쪽에서 완전 정합화함. 남은 가족은 latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
