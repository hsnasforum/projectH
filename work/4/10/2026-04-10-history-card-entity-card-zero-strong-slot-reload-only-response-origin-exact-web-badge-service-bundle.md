# history-card entity-card zero-strong-slot reload-only response-origin exact-web-badge service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 zero-strong entity-card reload-only 서비스 anchor 두 개의 reload-origin 블록을 literal exact 어서션으로 교체:
  - `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields` (click reload via `load_web_search_record_id`, `session_id: "zero-strong-hcard-reload-session"`)
  - `test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` (natural reload via `"방금 검색한 결과 다시 보여줘"`, `session_id: "zero-strong-natural-reload-session"`)
  - 두 테스트 모두 기존 reload 블록 (`answer_mode == "entity_card"`, baseline-derived `verification_label` / `source_roles`, `web_search_record_path == first_record_path`) 을 네 literal exact 어서션으로 교체:
    - `reload_origin["badge"] == "WEB"` (신규)
    - `reload_origin["answer_mode"] == "entity_card"` (그대로, 기존 literal)
    - `reload_origin["verification_label"] == "설명형 단일 출처"` (baseline-derived → literal)
    - `reload_origin["source_roles"] == ["백과 기반"]` (baseline-derived → literal)
    - `second["response"]["web_search_record_path"] == first_record_path` (그대로)
  - 기존 reload 흐름, `actions_taken == ["load_web_search_record"]`, first 단계의 `first_origin["answer_mode"] == "entity_card"` + CONTROL_SEQ 66 의 `first_origin["verification_label"] == "설명형 단일 출처"` 어서션, `reload_source_paths` 어서션 (`namu.wiki/testgame`, `ko.wikipedia.org/testgame`), CONTROL_SEQ 65 의 exact history summary `{"strong": 0, "weak": 0, "missing": 5}` + 빈 progress 어서션은 전혀 건드리지 않음. `first_origin` 변수는 first 단계 `answer_mode` / `verification_label` 검사에 여전히 쓰이므로 제거하지 않음.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 64-67 이 zero-strong 가족의 follow-up / chain / initial serialization / verification-label service continuity 를 모두 잠갔지만, reload-only 두 anchor 의 `response_origin` 블록은 여전히 baseline-derived 비교 (`first_origin["verification_label"]` / `first_origin["source_roles"]`) 만 사용하고 `badge == "WEB"` 는 아예 검사하지 않는 상태였음.
- browser 쪽은 `e2e/tests/web-smoke.spec.mjs:6053` / `:6683` 에서 zero-strong reload-only UX 의 exact contract (`WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`) 를 이미 잠가둔 상태.
- CONTROL_SEQ 66 이 두 테스트의 first 단계 `first_origin["verification_label"] == "설명형 단일 출처"` 를 literal 로 이미 잠가뒀으므로 기존 reload 블록의 `first_origin["verification_label"]` continuity 어서션은 사실상 literal 과 같은 값을 보장했지만, 본 라운드는 그 chained literal 을 직접 inline literal 로 교체해 drift detection 을 reload 블록 안에서도 direct 하게 만들고 `badge == "WEB"` 를 추가로 잠금.
- handoff 는 이 두 anchor 를 제자리에서 tighten 해 zero-strong reload-only 두 entry path 모두에서 browser smoke contract 와 같은 네 필드로 literal exact 잠그도록 지시. 범위 밖은 browser / 신규 테스트 / follow-up / second follow-up / actual-search / dual-probe / noisy / latest-update / store-seeded / general 가족 / docs / pipeline.
- 본 라운드 이후 zero-strong 가족의 모든 reload stage (reload-only → first follow-up → second follow-up, click + natural 두 entry path) 에서 `response_origin` 네 필드가 literal exact 로 잠긴 상태가 됨. actual-search (CONTROL_SEQ 68-71) / dual-probe (CONTROL_SEQ 72-73) 와 동일한 완성도의 reload chain coverage 를 갖게 됨.

## 핵심 변경
1. **click-reload 테스트 (`session_id: "zero-strong-hcard-reload-session"`) in-place tightening**
   - 기존 블록 → 네 literal exact 어서션 블록으로 교체. 리로드 후의 `reload_source_paths` + `reload_entry.claim_coverage_summary == {0,0,5}` + 빈 progress 어서션은 그대로 유지.
   - `session_id` 를 discriminator 로 삼아 targeted edit 로 정확히 이 테스트만 수정 (CONTROL_SEQ 73 의 replace_all 부작용 교훈 반영).
2. **natural-reload 테스트 (`session_id: "zero-strong-natural-reload-session"`) in-place tightening**
   - 같은 구조의 블록을 같은 방식으로 교체. 기존 `first_origin["answer_mode"]` 및 CONTROL_SEQ 66 의 `first_origin["verification_label"]` 어서션은 first 단계에서 그대로 유지.
   - 이후 `reload_source_paths` + `reload_entry.claim_coverage_summary == {0,0,5}` + 빈 progress 어서션도 그대로 유지.
3. **helper 재사용 여부**
   - CONTROL_SEQ 67-73 과 동일하게 helper 를 도입하지 않고 네 줄 inline literal 어서션 유지. `first_origin` 변수는 first 단계 참조로 여전히 쓰이므로 제거하지 않음.
4. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:6053`, `:6683`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - CONTROL_SEQ 64 의 zero-strong follow-up / second follow-up chain tests 와 CONTROL_SEQ 65 의 zero-strong initial serialization / count-summary anchors 와 CONTROL_SEQ 66 의 literal label tests 와 CONTROL_SEQ 67 의 click-reload second follow-up closure 는 모두 건드리지 않음
   - dual-probe / actual-search / noisy / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` → 두 테스트 모두 `ok` (신규 네 literal 어서션이 실제 zero-strong reload-only runtime 의 `response_origin` 과 정확히 일치: `badge == "WEB"`, `answer_mode == "entity_card"`, `verification_label == "설명형 단일 출처"`, `source_roles == ["백과 기반"]`)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 reload-origin 블록을 tighten 함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 zero-strong reload-only contract 를 두 경로 모두에서 잠가둠
- 이미 닫힌 zero-strong anchor 들 (CONTROL_SEQ 64-67) 과 dual-probe / actual-search 가족 anchor 들 — 본 슬라이스는 zero-strong reload-only stage 두 경로만 targets 함

## 남은 리스크
- 신규 `source_roles == ["백과 기반"]` + `verification_label == "설명형 단일 출처"` + `badge == "WEB"` 어서션은 zero-strong runtime 이 reload-only 단계에서도 이 literal 값을 방출한다는 가정에 의존. browser smoke 와 CONTROL_SEQ 64-67 이 이미 같은 literal 에 합의하므로 drift 시 본 어서션이 먼저 깨져 browser smoke 와 silent 어긋남을 방지함.
- CONTROL_SEQ 73 에서 replace_all 부작용으로 이 두 zero-strong 블록을 잠시 잘못 수정했다가 즉시 복구한 이력이 있음. 본 라운드는 그 이력을 인지하고 `session_id` discriminator 기반 targeted edit 만 사용해 다른 가족 테스트에 영향이 없음을 보장.
- `first_origin` 변수는 본 라운드에서 제거하지 않음. first 단계의 `assertEqual(first_origin["answer_mode"], "entity_card")` + CONTROL_SEQ 66 의 `assertEqual(first_origin["verification_label"], "설명형 단일 출처")` 두 어서션이 여전히 `first_origin` 을 참조함.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64-67 (zero-strong full chain + literal label + click-reload second follow-up closure) + CONTROL_SEQ 68-71 (actual-search all reload stages + two entry paths) + CONTROL_SEQ 72-73 (dual-probe first follow-up + reload-only two entry paths) + 본 CONTROL_SEQ 74 (zero-strong reload-only two entry paths) 루프는 entity-card 가족 네 주요 분기 + 모든 reload stage (reload-only → first follow-up → second follow-up, click + natural 두 entry path) 를 browser + service 양쪽에서 완전 정합화함. 남은 가족은 latest-update / store-seeded / general 등.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
