# 2026-05-12 M123 Axis 3 conflict resolution queries

## 변경 파일

- `core/web_claims.py`
- `core/agent_loop.py`
- `tests/test_smoke.py`
- `work/5/12/2026-05-12-m123-axis3-conflict-resolution-queries.md`

## 사용 skill

- `investigation-quality-audit`: entity-card CONFLICT 슬롯의 claim coverage와 second-pass probe 쿼리 변경이 신뢰/불확실성 표시 계약을 해치지 않는지 확인했습니다.
- `work-log-closeout`: 지정된 `/work` closeout 형식으로 변경 파일, 검증, 남은 리스크를 기록했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1592의 M123 Axis 3 지시를 실행했습니다.
- CONFLICT 슬롯에서 primary claim 값만 재확인하던 second-pass probe를 competing claim 값까지 포함하는 크로스-검증 쿼리로 강화하기 위한 변경입니다.

## 핵심 변경

- `SlotCoverage`에 `competing_claim` 필드를 추가하고, `summarize_slot_coverage()`의 CONFLICT 판정 시 신뢰 가능한 경쟁 claim을 보존하도록 했습니다.
- `_build_entity_slot_probe_queries()`에 `competing_claim` 인자를 추가하고, CONFLICT + primary/competing 값이 모두 있을 때 두 값과 정확성 질의를 포함한 슬롯별 probe 쿼리를 반환하도록 했습니다.
- `_build_entity_second_pass_queries()` 호출부가 `slot_coverage.competing_claim`을 probe query helper로 전달하도록 연결했습니다.
- `tests/test_smoke.py`에 CONFLICT cross-verification 쿼리와 competing 값이 없을 때 기존 fallback 유지 테스트를 추가하고, 기존 conflict coverage 테스트에 `competing_claim` 보존 assertion을 보강했습니다.

## 검증

- PASS: `python3 -m py_compile core/web_claims.py core/agent_loop.py`
- PASS: `python3 -m unittest -v tests.test_smoke.SmokeTest.test_conflict_slot_with_competing_value_produces_cross_verification_queries tests.test_smoke.SmokeTest.test_conflict_slot_without_competing_value_falls_through_to_existing_branch tests.test_smoke.SmokeTest.test_claims_summarize_slot_coverage_conflicting_trusted_alternative_returns_conflict`
- PASS: `python3 -m unittest -v tests.test_smoke` (162 tests)
- PASS: `git diff --check -- core/web_claims.py core/agent_loop.py tests/test_smoke.py`

## 남은 리스크

- 실제 live 웹 검색은 실행하지 않았고 fixture/unit smoke로 검증했습니다.
- UI, frontend, E2E, `.pipeline/`, commit/push/PR은 handoff 금지 범위에 따라 건드리지 않았습니다.
