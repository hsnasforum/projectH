# history-card entity-card zero-strong-slot exact missing-only count-summary service bundle

## 변경 파일
- `tests/test_web_app.py` — 기존 zero-strong entity-card missing-only 서비스 체인 테스트 두 개에서 baseline-derived per-field count 비교를 shipped 계약 dict 에 대한 exact equality 로 교체:
  - `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_missing_only_count_summary` (`:10229`, click-reload chain)
  - `test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_missing_only_count_summary` (`:10367`, natural-reload chain)
  - 두 테스트가 동일한 baseline 파생 블록과 helper 구조를 공유하므로 `Edit replace_all=true` 로 baseline 블록 + helper 를 한 번에 교체. baseline 단계에서 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 5}` 를 직접 잠그고, helper 는 per-field strong/weak/missing 비교 3건을 exact dict 비교 한 건으로 교체.
  - downgraded `verification_label` continuity 검사 (`entry["verification_label"] == baseline_verification_label`) 는 그대로 유지 (handoff 지시).
  - 빈 progress 어서션, stage 구조 (initial → reload → first follow-up → second follow-up), `actions_taken` routing, `record_id` 조회 패턴은 전혀 변경하지 않음.
- `e2e/tests/web-smoke.spec.mjs` 는 전혀 건드리지 않음 (handoff 가 browser 쪽을 범위 밖으로 명시).

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 56-61 (noisy strong-plus-missing) → 62 (non-noisy actual-search strong-plus-missing) → 63 (dual-probe mixed-count) 이 entity-card 가족의 세 non-zero 분기를 browser / service 층에서 exact equality 로 잠갔음.
- zero-strong 분기 (`{"strong": 0, "weak": 0, "missing": 5}`, downgraded `설명형 단일 출처`) 는 browser `.meta` smoke (`e2e/tests/web-smoke.spec.mjs:6155`, `:6523`, `:7052`) 에서 이미 exact line `사실 검증 미확인 5` 를 잠가둔 상태.
- 그러나 service chain 의 두 테스트 (`:10229`, `:10367`) 는 여전히 baseline 에서 per-field count 를 파생한 뒤 stage 마다 strong/weak/0/missing 을 baseline 과만 비교하는 구조. 이 경우 baseline 자체가 drift 해 다른 shape (예: `{0,0,4}`, `{0,1,4}`) 를 내도 테스트는 통과하면서 browser `.meta` exact text 와 silently 어긋남.
- handoff 의 focused read-only verify probe 가 현재 runtime 을 직접 확인:
  - `verification_label == "설명형 단일 출처"`
  - `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 5}`
  - 빈 progress
- handoff 는 "replace baseline-derived missing-only comparisons with exact equality to the shipped zero-strong dict `{ "strong": 0, "weak": 0, "missing": 5 }`" 라고 명시하고, 두 테스트를 제자리에서 tighten 하되 `verification_label` 은 기존 continuity 검사 (baseline 과 일치) 를 유지하고 browser / 다른 가족 / docs / pipeline 은 건드리지 않도록 지시.
- 본 라운드 이후 zero-strong 체인 서비스 truth 가 browser `사실 검증 미확인 5` exact line 과 truth-synced 가 됨. entity-card 가족의 네 주요 분기 (noisy strong-plus-missing / non-noisy strong-plus-missing / dual-probe mixed-count / zero-strong missing-only) 가 모두 service 층에서 exact equality 로 정합화됨.

## 핵심 변경
1. **공통 baseline 블록 (두 테스트 공유) → exact dict 로 교체**
   - 제거: `baseline_count_summary` 파생 + `assertEqual(strong, 0)` / `assertEqual(weak, 0)` / `assertGreater(missing, 0, ...)` 세 어서션
   - 추가: baseline_entry 에 대해 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 5}` 한 줄 exact 어서션
   - 빈 progress 어서션 (`str(...) == ""`) 은 그대로 유지
   - 설명형 주석으로 exact dict 잠금이 browser `사실 검증 미확인 5` smoke 와 truth-synced 임을 명시
2. **공통 `_assert_missing_only_meta_continuity(result, stage)` 헬퍼 → exact dict 로 교체**
   - 제거: `count_summary = entry.get("claim_coverage_summary") or {}` + strong/weak/missing 필드별 3회 비교 (마지막 missing 비교는 `baseline_count_summary` 참조)
   - 추가: `entry["claim_coverage_summary"] == {"strong": 0, "weak": 0, "missing": 5}` 한 줄 exact 비교
   - `entry["verification_label"] == baseline_verification_label` continuity 검사와 빈 progress 어서션은 helper 안에서 그대로 유지
   - `actions_taken` routing / history 비어있지 않음 / `record_id` 조회 어서션도 그대로 유지
   - 두 테스트의 helper 는 독립된 클로저지만 텍스트가 동일하므로 `replace_all=true` 로 한 번에 교체 가능 — baseline 블록도 동일 텍스트라 같은 edit 안에 포함해 두 테스트 모두 한 번에 정합화
3. **범위 밖 유지**
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs:6155`, `:6523`, `:7052`) 는 이미 browser `.meta` 를 잠가둔 상태로 그대로 유지
   - dual-probe / actual-search / noisy / latest-update / store-seeded / general 테스트는 전혀 수정하지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_missing_only_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_second_follow_up_preserves_missing_only_count_summary` → 두 테스트 모두 `ok` (신규 exact equality 어서션이 실제 zero-strong runtime 의 `{strong:0, weak:0, missing:5}` dict 와 initial / click reload / natural reload / first follow-up / second follow-up 모든 stage 에서 정확히 일치함을 확인)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 두 anchor 만 재실행을 요구했고, 본 슬라이스는 같은 두 테스트의 공통 블록만 exact dict 비교로 교체함
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser `.meta` smoke 는 이미 zero-strong `사실 검증 미확인 5` 를 여러 단계에서 잠가둠
- noisy entity-card / actual-search / dual-probe / latest-update / store-seeded 테스트 — handoff 가 본 라운드 범위 밖으로 명시함

## 남은 리스크
- 신규 `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 5}` exact equality 는 zero-strong entity-card runtime 분포 (5 missing slot, 0 strong / weak) 가 고정되어 있음에 의존. 이 분포가 바뀌면 두 테스트가 동시에 깨져 drift 를 가리킴 — 이것이 본 라운드의 설계 의도 (baseline 파생 구조가 숨기던 shape drift 를 exact equality 로 노출).
- `baseline_count_summary` 지역 변수가 제거되면서 각 테스트 블록의 변수 scope 가 축소됨. 이후 해당 블록에서 이 변수를 재사용하는 다른 코드는 없음 (확인됨).
- `baseline_verification_label` 은 여전히 baseline 과의 continuity 비교에만 쓰임 (helper 안에서 `entry["verification_label"] == baseline_verification_label`). handoff 가 "keep downgraded `verification_label` continuity checks" 라고 명시했으므로 literal `"설명형 단일 출처"` 로 hard-code 하지 않고 baseline 일치만 유지. runtime 이 현재 `"설명형 단일 출처"` 이므로 두 형태는 같은 drift coverage 를 가지며, 향후 labels 이 바뀌어도 이 테스트들은 여전히 drift 를 일관되게 보고함.
- zero-strong 분기는 browser `.meta` smoke 의 `사실 검증 미확인 5` exact 문자열과 본 라운드의 `{0,0,5}` exact dict 가 같은 shipped shape 를 보증함. browser / service 층이 이제 truth-synced 상태.
- CONTROL_SEQ 56-61 (noisy family full chain) + CONTROL_SEQ 62 (non-noisy actual-search chain) + CONTROL_SEQ 63 (dual-probe mixed-count chain) + 본 CONTROL_SEQ 64 (zero-strong missing-only chain) 루프는 entity-card 가족 네 주요 분기 (noisy `{3,0,2}`, actual-search `{3,0,2}`, dual-probe `{1,4,0}`, zero-strong `{0,0,5}`) 를 browser `.meta` + service continuity 양쪽에서 정합화함. latest-update / store-seeded / general 은 별도 slice 로 남아 있음.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
