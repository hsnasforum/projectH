# 2026-05-12 M124 Axis 3 수렴 벤치마크 확장

## 변경 파일

- `tests/test_smoke.py`
- `work/5/12/2026-05-12-m124-axis3-convergence-benchmark-expansion.md`

## 사용 skill

- `investigation-quality-audit`: core entity 슬롯 수렴 회귀 테스트가 기존 claim coverage 불확실성 규칙을 유지하는지 범위를 점검했습니다.
- `work-log-closeout`: 지정된 `/work` closeout 형식으로 변경 파일, 검증, 남은 리스크를 기록했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1610의 M124 Axis 3 지시를 실행했습니다.
- M124 Axis 1 벤치마크가 다루지 않았던 `장르/성격`, `상태`, `이용 형태` 슬롯까지 UNRESOLVED→STRONG 수렴 경로를 회귀 테스트로 고정하기 위한 변경입니다.

## 핵심 변경

- `test_m124_genre_slot_converges_to_strong_with_official_source`를 추가해 `장르/성격` 슬롯의 UNRESOLVED→STRONG 전환을 검증했습니다.
- `test_m124_status_slot_converges_to_strong_with_official_source`를 추가해 `상태` 슬롯의 UNRESOLVED→STRONG 전환을 검증했습니다.
- `test_m124_platform_slot_converges_to_strong_with_official_source`를 추가해 `이용 형태` 슬롯의 UNRESOLVED→STRONG 전환을 검증했습니다.
- handoff 금지 범위에 따라 `core/web_claims.py`, `core/agent_loop.py`, docs, `.pipeline/`, frontend, E2E, commit/push/PR은 건드리지 않았습니다.

## 검증

- PASS: `python3 -m py_compile tests/test_smoke.py`
- PASS: `python3 -m unittest -v tests.test_smoke.SmokeTest.test_m124_genre_slot_converges_to_strong_with_official_source tests.test_smoke.SmokeTest.test_m124_status_slot_converges_to_strong_with_official_source tests.test_smoke.SmokeTest.test_m124_platform_slot_converges_to_strong_with_official_source`
- PASS: `python3 -m unittest -v tests.test_smoke` (169 tests)
- PASS: `git diff --check -- tests/test_smoke.py`

## 남은 리스크

- Browser/E2E는 실행하지 않았습니다. 이번 변경은 `summarize_slot_coverage()` 직접 호출 회귀 테스트 추가이며 UI 계약 변경이 없습니다.
- M124 Axis 3 doc-sync와 publish bundle은 아직 미수행 상태이며 후속 control 대상입니다.
