# history-card entity-card dual-probe exact count-summary service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 dual-probe entity-card mixed-count 서비스 체인 테스트 두 개에서 baseline-derived strong/weak/missing 비교를 shipped 계약 dict 에 대한 exact equality 로 교체:
  - `test_handle_chat_dual_probe_entity_card_history_card_reload_second_follow_up_preserves_mixed_count_summary` (`:9787`, click-reload chain): `baseline_strong` / `baseline_weak` / `baseline_missing` 파생 + 세 `assertGreater` / `assertEqual(0)` 블록을 제거하고, baseline_entry 에 대해 `claim_coverage_summary == {"strong": 1, "weak": 4, "missing": 0}` 를 직접 잠금. `_assert_mixed_count_summary_continuity(result, stage)` 헬퍼도 strong/weak/missing 필드별 비교 3건을 exact dict 비교 한 건으로 교체.
  - `test_handle_chat_dual_probe_natural_reload_second_follow_up_preserves_mixed_count_summary` (`:9912`, natural-reload chain): 같은 구조의 baseline 파생 + 필드별 비교를 같은 exact dict equality 로 교체. 두 테스트의 helper 는 각각 클로저 안에서 정의되어 있으므로 독립적으로 패치.
  - 두 테스트 모두 기존 stage 구조 (initial response, click/natural reload, first follow-up, second follow-up), `actions_taken` routing, `verification_label == "설명형 다중 출처 합의"`, 빈 progress, `record_id` 조회 패턴은 그대로 유지됨.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 56-61 은 noisy entity-card strong-plus-missing 분기를 browser / service 양쪽에서 exact equality 로 잠갔고, CONTROL_SEQ 62 는 non-noisy actual-search strong-plus-missing 분기를 service 층에서 exact `{3,0,2}` 로 잠갔음.
- dual-probe entity-card 의 mixed-count 분기 (`{strong:1, weak:4, missing:0}`) 는 browser `.meta` smoke 가 여러 단계에서 exact 문자열 `"사실 검증 교차 확인 1 · 단일 출처 4"` 를 이미 잠가둔 상태이고, `tests/test_web_app.py:9718-9732` 의 dual-probe reload-only exact-fields anchor 도 shipped dict 를 이미 서비스 층에서 잠가둔 상태.
- 그러나 dual-probe 체인의 두 서비스 테스트 (`:9787`, `:9912`) 는 여전히 baseline_strong / baseline_weak / baseline_missing 를 first response 에서 파생한 뒤 이후 단계를 그 baseline 과만 비교하는 구조. 이 경우 baseline 자체가 runtime drift 로 `{1,4,0}` 가 아닌 shape 로 바뀌어도 테스트는 통과하면서 browser `.meta` exact text 와 silently 어긋남.
- handoff 는 "replace baseline-derived strong/weak/missing comparisons with exact equality to the shipped dual-probe dict `{ "strong": 1, "weak": 4, "missing": 0 }`" 라고 명시하고, 두 테스트를 제자리에서 tighten 하되 noisy / actual-search / latest-update / zero-count / browser / docs / pipeline 은 범위 밖으로 둠.
- 본 라운드 이후 dual-probe 체인 서비스 truth 가 `:9718-9732` 의 reload-only 앵커와 browser `.meta` smoke 와 완전히 같은 `{1,4,0}` shape 를 강제하게 됨. entity-card 가족의 noisy strong-plus-missing / non-noisy actual-search strong-plus-missing / dual-probe mixed-count 세 주요 분기가 service 층에서 모두 exact equality 로 정합화됨.

## 핵심 변경
1. **`tests/test_web_app.py:9787` in-place tightening**
   - first response 이후 `baseline_count_summary` 파생 → `baseline_strong`/`baseline_weak`/`baseline_missing` 로컬 변수 → 세 개의 `assertGreater`/`assertEqual` 어서션 블록 전체를 제거하고, baseline_entry 에 대해 `claim_coverage_summary == {"strong": 1, "weak": 4, "missing": 0}` 한 줄 exact 어서션을 추가. 기존 `verification_label == "설명형 다중 출처 합의"` 와 빈 progress 어서션은 그대로 유지.
   - `_assert_mixed_count_summary_continuity(result, stage)` 헬퍼 안의 `count_summary` 파생 + strong/weak/missing 필드별 3회 비교 (`baseline_strong`, `baseline_weak`, `0`) 구조를 `entry["claim_coverage_summary"] == {"strong": 1, "weak": 4, "missing": 0}` 한 줄 exact 비교로 교체. `verification_label` 와 빈 progress 어서션은 helper 안에서 그대로 유지.
2. **`tests/test_web_app.py:9912` in-place tightening**
   - 같은 구조의 baseline 파생 + 간결 `assertGreater(baseline_strong, 0)` / `assertGreater(baseline_weak, 0)` / `assertEqual(baseline_missing, 0)` 블록을 같은 방식으로 exact dict 어서션으로 교체.
   - `_assert_mixed_count_summary_continuity(result, stage)` 헬퍼도 같은 방식으로 교체. 두 테스트의 helper 는 독립된 클로저지만 동일 패턴이므로 별도 Edit 로 각각 패치.
3. **범위 밖 유지**
   - `:9718-9732` 의 dual-probe reload-only exact-fields anchor (shipped dict 이미 잠긴 상태) 는 그대로 유지.
   - noisy entity-card / actual-search / latest-update / store-seeded / zero-count / general 테스트는 전혀 수정하지 않음.
   - `e2e/tests/web-smoke.spec.mjs`, docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음.

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_card_history_card_reload_second_follow_up_preserves_mixed_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_second_follow_up_preserves_mixed_count_summary` → 두 테스트 모두 `ok` (신규 exact equality 어서션이 실제 dual-probe runtime 의 `{strong:1, weak:4, missing:0}` dict 와 initial / click reload / natural reload / first follow-up / second follow-up 모든 stage 에서 정확히 일치함을 확인)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트 안에서만 baseline 파생 / 필드별 비교를 exact dict 비교로 교체함.
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser `.meta` smoke 는 이미 dual-probe `{1,4,0}` dict 를 여러 단계에서 잠가둠.
- noisy entity-card / actual-search / latest-update / store-seeded / zero-count 테스트 — handoff 가 본 라운드 범위 밖으로 명시함.

## 남은 리스크
- 신규 `claim_coverage_summary == {"strong": 1, "weak": 4, "missing": 0}` exact equality 는 dual-probe entity-card runtime 분포 (1 strong + 4 weak + 0 missing) 가 고정되어 있음에 의존. 이 분포가 바뀌면 두 테스트가 동시에 깨져 drift 를 가리킴 — 이것이 본 라운드의 설계 의도 (baseline 파생 구조가 숨기던 shape drift 를 exact equality 로 노출).
- `baseline_count_summary` / `baseline_strong` / `baseline_weak` / `baseline_missing` 지역 변수가 제거되면서 각 테스트 블록의 변수 scope 가 축소됨. 이후 해당 블록에서 이 변수들을 재사용하는 다른 코드는 없음 (확인됨).
- dual-probe mixed-count 분기는 browser `.meta` smoke 의 `"사실 검증 교차 확인 1 · 단일 출처 4"` exact 문자열과 `:9718-9732` 의 reload-only exact-fields anchor 가 이미 shipped dict 를 잠가둔 상태였음. 본 라운드는 나머지 두 체인 테스트의 continuity 계층까지 같은 shape 를 강제해 dual-probe family 전체가 browser / service 층에서 truth-synced 가 됨.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + 본 CONTROL_SEQ 63 (dual-probe mixed-count chain) 루프는 entity-card 가족 세 주요 분기 (noisy `{3,0,2}`, actual-search `{3,0,2}`, dual-probe `{1,4,0}`) 를 browser `.meta` + service continuity 양쪽에서 정합화함. latest-update / store-seeded / zero-count / general 은 별도 slice 로 남아 있음.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
