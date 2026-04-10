# history-card entity-card actual-search exact count-summary service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 actual-search entity-card strong-plus-missing 서비스 체인 테스트 두 개에서 baseline-derived count 비교를 shipped 계약 dict 에 대한 exact equality 로 교체:
  - `test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_claim_coverage_count_summary` (`:9354`): `baseline_counts = { first_summary 에서 파생 }` + `assertGreater(total, 0)` 구조를 제거하고, first 단계에서부터 `first_history[0]` 에 대해 `claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}` / `verification_label == "설명형 다중 출처 합의"` / 빈 progress 를 직접 잠금. `_assert_same_counts(result, stage)` 헬퍼도 `baseline_counts` 비교에서 exact dict 비교로 교체하고 verification_label + 빈 progress 어서션을 함께 포함.
  - `test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_claim_coverage_count_summary` (`:9471`): `baseline_strong`/`baseline_weak`/`baseline_missing` 파생 + `assertGreater(baseline_strong, 0)` / `assertEqual(baseline_weak, 0)` / `assertGreater(baseline_missing, 0)` 구조를 제거하고, baseline_entry 에 대해 `claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}` 를 직접 잠금. `_assert_strong_plus_missing_continuity(result, stage)` 헬퍼도 strong/weak/missing 필드별 비교 3건을 exact dict 비교 한 건으로 교체.
  - 두 테스트 모두 기존 stage 구조 (initial response, natural / click reload, first follow-up, second follow-up) 와 `actions_taken` / `record_id` 조회 / `verification_label == "설명형 다중 출처 합의"` / 빈 progress 어서션은 그대로 유지됨.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 56-61 이 noisy entity-card strong-plus-missing 분기를 browser initial-render / browser reload-only / service initial response / service direct reload / service follow-up 네 축에서 exact equality 로 잠갔음.
- non-noisy actual-search 체인은 browser `.meta` smoke 가 이미 exact `{strong:3, weak:0, missing:2}` dict 를 여러 단계에서 인코딩하고 있었음. 또한 `tests/test_web_app.py:9338-9352` 의 actual-search reload-only exact-fields anchor 가 동일한 shipped dict 를 이미 서비스 층에서 잠가둔 상태.
- 그러나 actual-search 체인의 두 서비스 테스트 (`:9354`, `:9471`) 는 여전히 `baseline_counts` / `baseline_strong` / `baseline_missing` 를 first response 에서 파생한 뒤 이후 단계를 그 baseline 과만 비교하는 구조. 이 경우 baseline 자체가 runtime drift 로 `{3,0,2}` 가 아니게 되면 테스트는 여전히 통과하면서 browser `.meta` exact text 와 silently 어긋남.
- handoff 는 "replace baseline-derived count comparisons with exact equality to the shipped actual-search dict `{ "strong": 3, "weak": 0, "missing": 2 }`" 라고 명시하고, 두 테스트를 제자리에서 tighten 하되 noisy family / dual-probe / latest-update / zero-count / browser / docs / pipeline 은 범위 밖으로 둠.
- 본 라운드 이후 actual-search 체인 서비스 truth 가 `:9338-9352` 의 reload-only 앵커와 browser `.meta` smoke 와 완전히 같은 `{3,0,2}` shape 를 강제하게 됨. 그래서 noisy family 와 nonnoisy actual-search family 양쪽이 service 층에서 동일 payload shape 를 공유하는 상태로 정합화.

## 핵심 변경
1. **`tests/test_web_app.py:9354` in-place tightening**
   - first response 이후 `baseline_counts` 파생 / 총합 `assertGreater` 검사를 제거하고, first_history[0] 에 대해 세 계약을 직접 잠금:
     - `claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}`
     - `verification_label == "설명형 다중 출처 합의"`
     - `claim_coverage_progress_summary == ""`
   - `_assert_same_counts(result, stage)` 헬퍼 본문에서 `entry["claim_coverage_summary"] == baseline_counts` 비교를 `{"strong": 3, "weak": 0, "missing": 2}` exact dict 비교로 교체하고, 이어서 `verification_label == "설명형 다중 출처 합의"` 와 빈 progress 어서션을 같은 helper 안에서 매 stage 마다 수행. 기존 `actions_taken` / `record_id` 조회 / `history` 비어있지 않음 어서션은 그대로 유지.
2. **`tests/test_web_app.py:9471` in-place tightening**
   - `baseline_count_summary` 에서 `baseline_strong` / `baseline_weak` / `baseline_missing` 을 파생하는 세 줄과 각각에 대한 `assertGreater` / `assertEqual(0)` 세 줄 전체를 제거하고, baseline_entry 자체에 `claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}` exact 어서션을 추가. 기존 `verification_label == "설명형 다중 출처 합의"` 와 빈 progress 어서션은 그대로 유지.
   - `_assert_strong_plus_missing_continuity(result, stage)` 헬퍼 안에서 `count_summary` dict 파생 + strong/weak/missing 필드별 3회 비교 구조를 `entry["claim_coverage_summary"] == {"strong": 3, "weak": 0, "missing": 2}` 한 줄 exact 비교로 교체. `verification_label` 와 빈 progress 어서션은 같은 helper 안에서 그대로 유지.
3. **기존 stage 구조와 다른 테스트는 전혀 건드리지 않음**
   - `:9338-9352` 의 actual-search reload-only natural reload exact-fields anchor (shipped dict 이미 잠긴 상태) 는 그대로 유지.
   - noisy family (CONTROL_SEQ 61 에서 exact dict 로 잠김) 는 건드리지 않음.
   - dual-probe, latest-update, store-seeded, zero-count, general 테스트는 전혀 수정하지 않음.
4. **범위 밖 유지**
   - `e2e/tests/web-smoke.spec.mjs`, docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음 (handoff 지시).

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_claim_coverage_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_claim_coverage_count_summary` → 두 테스트 모두 `ok` (새 exact equality 어서션이 실제 actual-search runtime 의 `{strong:3, weak:0, missing:2}` dict 와 initial / natural reload / click reload / first follow-up / second follow-up 모든 stage 에서 정확히 일치함을 확인)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 baseline 파생 / 필드별 비교를 exact dict 비교로 교체함.
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser `.meta` smoke 는 이미 actual-search `{3,0,2}` dict 를 여러 단계에서 잠가둠.
- noisy entity-card / dual-probe / latest-update / store-seeded / zero-count 테스트 — handoff 가 본 라운드 범위 밖으로 명시함.

## 남은 리스크
- 신규 `claim_coverage_summary == {"strong": 3, "weak": 0, "missing": 2}` exact equality 는 actual-search entity-card runtime 분포 (5-slot strong 3 + missing 2) 가 고정되어 있음에 의존. 이 분포가 바뀌면 두 테스트가 동시에 깨져 drift 를 가리킴 — 이것이 본 라운드의 설계 의도 (baseline 파생 구조가 숨기던 shape drift 를 exact equality 로 노출).
- `baseline_counts` / `baseline_strong` / `baseline_weak` / `baseline_missing` 지역 변수가 제거되면서 각 테스트 블록의 변수 scope 가 축소됨. 이후 해당 블록에서 이 변수들을 재사용하는 다른 코드는 없음 (확인됨).
- actual-search entity-card strong-plus-missing 분기는 browser `.meta` smoke 와 `:9338-9352` 의 reload-only exact-fields anchor 가 이미 shipped dict 를 잠가둔 상태였음. 본 라운드는 나머지 두 체인 테스트의 continuity 계층까지 같은 shape 를 강제해 nonnoisy actual-search family 전체가 browser / service 층에서 truth-synced 가 됨.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) 루프는 entity-card 가족 전체의 strong-plus-missing 분기를 browser `.meta` + service continuity 양쪽에서 정합화함. dual-probe / latest-update / store-seeded 는 별도 slice 로 남아 있음.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
