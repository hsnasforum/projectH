# history-card entity-card dual-probe reload-only response-origin exact-web-badge service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 dual-probe entity-card reload-only 서비스 anchor 두 개의 reload-origin 블록을 literal exact 어서션으로 교체:
  - `test_handle_chat_dual_probe_entity_search_natural_reload_exact_fields` (`:9627`, natural reload via `"방금 검색한 결과 다시 보여줘"`)
  - `test_handle_chat_dual_probe_entity_search_history_card_reload_exact_fields` (`:10012`, click reload via `load_web_search_record_id`)
  - 두 테스트 모두 기존 reload 블록 (`answer_mode == "entity_card"`, baseline-derived `verification_label` / `source_roles`, `web_search_record_path == first_record_path`) 을 네 literal exact 어서션으로 교체:
    - `reload_origin["badge"] == "WEB"` (신규)
    - `reload_origin["answer_mode"] == "entity_card"` (그대로, 기존 literal)
    - `reload_origin["verification_label"] == "설명형 다중 출처 합의"` (baseline-derived → literal)
    - `reload_origin["source_roles"] == ["공식 기반", "백과 기반"]` (baseline-derived → literal)
    - `second["response"]["web_search_record_path"] == first_record_path` (그대로)
  - 기존 reload 흐름, `actions_taken == ["load_web_search_record"]` 어서션, first 단계의 `first_origin["answer_mode"] == "entity_card"` 어서션, exact history summary `{"strong": 1, "weak": 4, "missing": 0}` + 빈 progress + `"설명형 다중 출처 합의"` history-entry 어서션은 전혀 건드리지 않음. `first_origin` 변수는 first 단계 `answer_mode` 검사에서 여전히 쓰이므로 제거하지 않음.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 72 (dual-probe first follow-up response-origin) 이후 dual-probe 가족의 first follow-up (`:9797`, `:18311`) 과 second follow-up (`:17346`, `:18406`) anchor 들이 모두 literal exact 로 잠긴 상태였음.
- 그러나 dual-probe reload-only 두 anchor (`:9627`, `:10012`) 는 여전히 loose:
  - `badge` 필드 검사 없음
  - `verification_label` / `source_roles` 가 `first_origin` baseline 과 일치 비교 → initial 자체가 drift 하면 silently 통과
- browser 쪽은 `e2e/tests/web-smoke.spec.mjs:3096` / `:7537` 에서 dual-probe reload-only UX 의 exact contract (`WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반 · 백과 기반`) 를 이미 잠가둔 상태.
- handoff 는 이 두 anchor 를 제자리에서 tighten 해 dual-probe reload-only 두 entry path 모두에서 browser smoke contract 와 같은 네 필드로 literal exact 잠그도록 지시. 범위 밖은 browser / 신규 테스트 / first follow-up / second follow-up / actual-search / zero-strong / 다른 가족 / docs / pipeline.
- 본 라운드 이후 dual-probe 가족의 모든 reload stage (reload-only → first follow-up → second follow-up, click + natural 두 entry path) 에서 `response_origin` 네 필드가 literal exact 로 잠긴 상태가 됨. actual-search 가족 (CONTROL_SEQ 68-71) 과 동일한 완성도의 reload chain coverage 를 갖게 됨.

## 핵심 변경
1. **`tests/test_web_app.py:9627` natural-reload exact-fields in-place tightening**
   - 기존 블록:
     ```python
     reload_origin = second["response"]["response_origin"]
     self.assertEqual(reload_origin["answer_mode"], "entity_card")
     self.assertEqual(reload_origin["verification_label"], first_origin["verification_label"])
     self.assertEqual(reload_origin["source_roles"], first_origin["source_roles"])
     self.assertEqual(second["response"]["web_search_record_path"], first_record_path)
     ```
   - 교체 후:
     ```python
     reload_origin = second["response"]["response_origin"]
     self.assertEqual(reload_origin["badge"], "WEB")
     self.assertEqual(reload_origin["answer_mode"], "entity_card")
     self.assertEqual(reload_origin["verification_label"], "설명형 다중 출처 합의")
     self.assertEqual(reload_origin["source_roles"], ["공식 기반", "백과 기반"])
     self.assertEqual(second["response"]["web_search_record_path"], first_record_path)
     ```
   - `first_origin` 변수는 여전히 first 단계 `self.assertEqual(first_origin["answer_mode"], "entity_card")` 에 쓰이므로 제거하지 않음.
2. **`tests/test_web_app.py:10012` click-reload exact-fields in-place tightening**
   - 같은 블록 패턴을 같은 방식으로 교체. 동일한 네 literal exact 어서션.
3. **replace_all 부작용 복구**
   - `Edit replace_all=true` 로 두 dual-probe 블록을 한 번에 교체 시도했으나, 같은 패턴이 zero-strong reload-only 두 테스트 (`zero-strong-hcard-reload-session` / `zero-strong-natural-reload-session`) 에도 존재해 그 두 블록까지 dual-probe literal 값으로 교체되어 두 테스트가 실패했음 (`verification_label == "설명형 다중 출처 합의"` 로 잘못 설정되었는데 zero-strong runtime 은 `"설명형 단일 출처"` 를 방출).
   - 복구 절차:
     1. 두 zero-strong reload 블록을 `session_id` discriminator 기반 targeted edit 로 원래의 baseline-derived 형태 (`reload_origin["verification_label"] == first_origin["verification_label"]` + `reload_origin["source_roles"] == first_origin["source_roles"]`) 로 되돌림 (`badge == "WEB"` 추가도 제거).
     2. zero-strong reload-only 는 본 라운드 범위 밖이므로 CONTROL_SEQ 66 의 `first_origin["verification_label"] == "설명형 단일 출처"` literal 어서션이 baseline 을 이미 잠가두고 있어 continuity 경로는 그대로 literal 에 바인딩된 상태로 유지됨.
   - 복구 후 dual-probe 네 필드는 그대로 literal exact 로 잠기고, zero-strong 두 테스트도 이전 상태 그대로 유지됨.
4. **helper 재사용 여부**
   - handoff 가 "remove `first_origin` only if it becomes unused after the tightening" + "keep the diff small" 을 명시. 본 라운드에서는 `first_origin` 이 `first_origin["answer_mode"]` 참조로 여전히 쓰이므로 제거하지 않음. CONTROL_SEQ 67-72 와 동일하게 helper 를 도입하지 않고 네 줄 inline 어서션 유지.
5. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:3096`, `:7537`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 63 의 dual-probe mixed-count history summary 어서션은 건드리지 않음
   - `:9797` / `:18311` dual-probe first follow-up tests 와 `:17346` / `:18406` dual-probe second follow-up tests 는 모두 건드리지 않음 (handoff 명시)
   - zero-strong reload-only tests (`zero-strong-hcard-reload-session`, `zero-strong-natural-reload-session`) 는 replace_all 부작용 복구를 통해 이전 상태로 되돌려 범위 밖 상태 유지
   - actual-search / noisy / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_search_natural_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_search_history_card_reload_exact_fields` → 두 테스트 모두 `ok`
- 부작용 확인: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` → 복구 후 두 테스트 모두 `ok`
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 reload-origin 블록을 tighten 함. 부작용 확인으로 zero-strong reload-only 두 테스트를 추가로 재실행했지만 전체 슈트는 아님.
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 dual-probe reload-only contract 를 두 경로 모두에서 잠가둠.
- 이미 닫힌 dual-probe anchor 들 (`:9797`, `:18311`, `:17346`, `:18406`) 과 actual-search / zero-strong 가족 anchor 들 — 본 슬라이스는 dual-probe reload-only stage 두 경로만 targets 함.

## 남은 리스크
- 신규 `source_roles == ["공식 기반", "백과 기반"]` 어서션은 dual-probe runtime 이 두 role 을 이 순서로 방출한다는 가정에 의존. browser smoke 의 `공식 기반 · 백과 기반` 배지 ordering 과 CONTROL_SEQ 63 / 72 / 기존 second follow-up anchor 들의 ordering 이 같은 순서를 이미 잠가두고 있음. ordering 이 바뀌면 본 어서션이 먼저 깨져 drift 를 가리킴.
- `first_origin["answer_mode"]` 어서션은 여전히 first 단계 check 로 유지됨. first_origin 의 다른 필드 (`verification_label` / `source_roles`) 는 이제 reload 블록에서 직접 검사되지 않지만, CONTROL_SEQ 63 의 `:9787` / `:9912` 에서 잠근 dual-probe chain 테스트의 baseline_entry 어서션이 1차 방어함.
- replace_all 부작용으로 zero-strong reload-only 테스트가 일시적으로 잘못된 literal 값으로 바뀌었지만, 즉각 `session_id` discriminator 기반 targeted edit 로 baseline-derived 형태로 되돌렸고 검증으로 확인함. 이 교훈: 같은 리팩터 블록 패턴이 여러 가족에서 공유되는 경우 `replace_all=true` 는 discriminator 없이는 위험하므로 가족별 targeted edit 가 더 안전함.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64-67 (zero-strong full chain) + CONTROL_SEQ 68-71 (actual-search all reload stages + two entry paths) + CONTROL_SEQ 72 (dual-probe first follow-up two entry paths) + 본 CONTROL_SEQ 73 (dual-probe reload-only two entry paths) 루프는 entity-card 가족 네 주요 분기 + actual-search 모든 reload stage + dual-probe 모든 reload stage 를 browser + service 양쪽에서 완전 정합화함. 남은 가족은 latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
