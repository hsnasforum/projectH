# history-card entity-card zero-strong-slot initial-plus-reload exact missing-only count-summary service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 zero-strong entity-card 서비스 테스트 세 개에서 남아 있던 loose missing-only 어서션을 shipped 계약 dict 에 대한 exact equality 로 교체:
  - `test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization_includes_missing_only_count_summary` (`:10159`): `count_summary` 파생 + `assertEqual(strong, 0)` + `assertEqual(weak, 0)` + `assertGreater(missing, 0)` 블록을 `entry.get("claim_coverage_summary") == {"strong": 0, "weak": 0, "missing": 5}` 한 줄 exact 어서션으로 교체. downgraded verification_label (`assertNotEqual(..., "설명형 다중 출처 합의")`) 와 빈 progress 어서션은 그대로 유지.
  - `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields` (`:10484`): 기존 `response_origin` / `source_paths` exact-field 어서션 뒤에 reload-stage history summary 잠금 블록을 추가. `second["session"]["web_search_history"][0]` 에 대해 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 5}` + 빈 progress 어서션. verification_label continuity 는 기존 `reload_origin["verification_label"] == first_origin["verification_label"]` 비교로 유지됨.
  - `test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` (`:10553`): 같은 방식으로 exact 어서션 두 건 추가. 두 reload 테스트의 3-line ending (`reload_source_paths` 블록) 이 동일하므로 `Edit replace_all=true` 로 한 번에 추가.
  - 세 테스트 모두 기존 `response_origin` / `source_paths` / `web_search_record_path` / `answer_mode` / downgraded verification_label 어서션은 전혀 건드리지 않음.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 64 (`2026-04-10-history-card-entity-card-zero-strong-slot-exact-missing-only-count-summary-service-bundle.md`) 가 zero-strong 가족의 follow-up 체인 테스트 두 개 (`:10229`, `:10367`) 를 exact `{"strong": 0, "weak": 0, "missing": 5}` 로 잠갔음.
- browser `.meta` smoke (`e2e/tests/web-smoke.spec.mjs:6155`, `:6523`, `:7052`) 는 이미 exact line `사실 검증 미확인 5` 를 잠가둔 상태.
- 그러나 zero-strong 가족에 남아 있던 세 개의 느슨한 서비스 anchor 가 여전히 drift 가능한 구조였음:
  - `:10159` 초기 serialization anchor 는 `missing > 0` 만 검사 → `{0,0,4}` / `{0,0,6}` / `{0,1,5}` 등으로 drift 해도 통과
  - `:10484` / `:10553` reload-only exact-fields anchor 는 `response_origin` / `source_paths` 만 검사하고 `claim_coverage_summary` / progress 는 전혀 검사하지 않음 → reload 시점에 history summary 가 drift 해도 통과
- handoff 는 이 세 anchor 를 제자리에서 tighten 해 initial serialization / reload-only 두 경로 / chain continuity / browser `.meta` 네 축이 모두 `{0,0,5}` 계약에 합의하도록 지시함. 범위 밖은 browser / 신규 테스트 / docs / pipeline / 다른 history-card 가족.
- 본 라운드 이후 zero-strong 가족 전체 (initial serialization → click reload exact-fields → natural reload exact-fields → click reload follow-up chain → natural reload follow-up chain) 가 service 층에서 exact `{0,0,5}` 로 정합화됨. browser `사실 검증 미확인 5` smoke 와도 truth-synced 상태.

## 핵심 변경
1. **`tests/test_web_app.py:10159` in-place tightening**
   - 제거: `count_summary = entry.get("claim_coverage_summary") or {}` + `assertEqual(int(count_summary.get("strong") or 0), 0)` + `assertEqual(int(count_summary.get("weak") or 0), 0)` + `assertGreater(int(count_summary.get("missing") or 0), 0, "...")`
   - 추가: `self.assertEqual(entry.get("claim_coverage_summary"), {"strong": 0, "weak": 0, "missing": 5})` 한 줄 + 설명형 주석 (browser smoke + chain tests 와의 정합성 의도)
   - 기존 빈 progress 어서션 (`str(entry.get("claim_coverage_progress_summary") or "") == ""`) 과 downgraded verification_label 어서션 (`assertNotEqual(..., "설명형 다중 출처 합의")` + `assertTrue(...)`) 은 그대로 유지
2. **`tests/test_web_app.py:10484` + `:10553` in-place tightening (`replace_all=true`)**
   - 두 테스트의 공통 ending 패턴 (`reload_source_paths = ...` + `assertIn namu.wiki/testgame` + `assertIn ko.wikipedia.org/testgame`) 뒤에 다음 블록을 추가:
     - `reload_entry = second["session"]["web_search_history"][0]`
     - `assertEqual(reload_entry.get("claim_coverage_summary"), {"strong": 0, "weak": 0, "missing": 5})`
     - `assertEqual(str(reload_entry.get("claim_coverage_progress_summary") or ""), "")`
   - 설명형 주석으로 이 어서션이 browser `사실 검증 미확인 5` smoke + chain tests `:10229` / `:10367` 과 truth-synced 임을 명시. verification_label continuity 는 기존 `reload_origin["verification_label"] == first_origin["verification_label"]` 이미 잠겨 있음.
   - `record_id` 기반 lookup 이 아니라 `second["session"]["web_search_history"][0]` index 조회로 단순화한 것은 두 테스트의 기존 fixture 가 session 내 단일 history entry 만 생성하는 구조이기 때문. follow-up 체인 테스트와 달리 이들은 첫 호출 후 reload 한 번만 수행하므로 첫 entry 가 target record 와 동일함이 보장됨.
3. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:6155`, `:6523`, `:7052`) 는 이미 browser `.meta` 를 잠가둔 상태로 그대로 유지
   - chain tests `:10229` / `:10367` 는 CONTROL_SEQ 64 에서 exact dict 로 이미 잠김 — 건드리지 않음
   - noisy / actual-search / dual-probe / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization_includes_missing_only_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` → 세 테스트 모두 `ok` (신규 exact equality 어서션이 실제 zero-strong runtime 의 `{strong:0, weak:0, missing:5}` dict 와 initial serialization / click reload / natural reload 세 경로 모두에서 정확히 일치함을 확인)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 세 anchor 만 재실행을 요구했고, 본 슬라이스는 세 테스트에 한 줄씩 exact 어서션을 좁게 추가/교체함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser `.meta` smoke 는 이미 zero-strong `사실 검증 미확인 5` 를 여러 단계에서 잠가둠
- CONTROL_SEQ 64 가 잠근 chain tests `:10229` / `:10367` — 본 슬라이스는 그 두 테스트 범위 밖

## 남은 리스크
- 신규 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 5}` exact equality 는 zero-strong entity-card runtime 분포 (5 missing slot, 0 strong / weak) 가 고정되어 있음에 의존. 이 분포가 바뀌면 세 테스트가 동시에 깨져 drift 를 가리킴 — 이것이 본 라운드의 설계 의도 (loose missing-only pattern 이 숨기던 shape drift 를 exact equality 로 노출).
- `:10484` / `:10553` 의 reload 후 history entry 조회는 `second["session"]["web_search_history"][0]` 첫 entry 를 사용. 두 테스트의 fixture 가 session 당 단일 record 만 생성하므로 index 0 이 안전하고, reload action 은 기존 record 를 재사용해 entry 개수를 늘리지 않음. 향후 이 테스트들의 호출 흐름이 바뀌어 여러 entry 가 추가되면 조회 방식을 재검토해야 함.
- `:10159` 는 초기 serialization 단계만 exercise 하므로 reload / follow-up drift 는 다른 anchor 들이 1차로 잡도록 역할 분담이 유지됨. browser `.meta` smoke + chain tests + reload-only exact-fields + 본 라운드의 initial serialization anchor 가 서로 다른 stage 에 대한 drift detection 계층을 형성함.
- downgraded verification_label (`"설명형 단일 출처"`) 은 literal hard-code 하지 않고 기존 continuity 비교 (chain tests 는 baseline 일치, reload tests 는 `first_origin` 일치, initial serialization 은 `assertNotEqual("설명형 다중 출처 합의")`) 를 그대로 유지. handoff 가 "keep downgraded verification-label expectations / continuity" 라고 명시한 바에 부합.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + CONTROL_SEQ 64 (zero-strong missing-only chain) + 본 CONTROL_SEQ 65 (zero-strong initial+reload anchors) 루프는 entity-card 가족 네 주요 분기를 browser `.meta` + service continuity + service initial/reload anchor 세 계층에서 완전히 정합화함. latest-update / store-seeded / general 은 별도 slice 로 남아 있음.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
