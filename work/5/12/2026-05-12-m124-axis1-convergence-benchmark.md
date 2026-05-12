# 2026-05-12 M124 Axis 1 수렴 벤치마크

## 변경 파일

- `tests/test_smoke.py`
- `work/5/12/2026-05-12-m124-axis1-convergence-benchmark.md`

## 사용 skill

- `work-log-closeout`: 지정된 `/work` closeout 형식으로 변경 파일, 검증, 남은 리스크를 기록했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1600의 M124 Axis 1 지시를 실행했습니다.
- M123 Axis 1–3 개선이 UNRESOLVED·CONFLICT 슬롯을 STRONG으로 수렴시키는 경로를 fixture 기반 회귀 테스트로 고정하기 위한 변경입니다.

## 핵심 변경

- `test_m124_unresolved_slot_converges_to_strong_with_official_source`를 추가해 비신뢰 출처 only 상태의 `개발` 슬롯이 공식 출처 2개 보강 후 `CoverageStatus.STRONG`으로 전환되는지 검증했습니다.
- `test_m124_conflict_slot_converges_to_strong_when_competing_claim_loses_support`를 추가해 `서비스/배급` 슬롯의 competing trusted claim이 지지력을 잃으면 `CoverageStatus.CONFLICT`에서 `CoverageStatus.STRONG`으로 수렴하고 `competing_claim`이 사라지는지 검증했습니다.
- handoff 금지 범위에 따라 `core/web_claims.py`, `core/agent_loop.py`, docs, `.pipeline/`, frontend, E2E, commit/push/PR은 건드리지 않았습니다.

## 검증

- PASS: `python3 -m py_compile tests/test_smoke.py`
- PASS: `python3 -m unittest -v tests.test_smoke.SmokeTest.test_m124_unresolved_slot_converges_to_strong_with_official_source tests.test_smoke.SmokeTest.test_m124_conflict_slot_converges_to_strong_when_competing_claim_loses_support`
- PASS: `python3 -m unittest -v tests.test_smoke` (164 tests)
- PASS: `git diff --check -- tests/test_smoke.py`

## 남은 리스크

- 현재 작업트리에는 이전 M123 아크 종료 doc-sync의 `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `work/5/12/2026-05-12-m123-arc-closure-doc-sync.md` 변경이 남아 있으며, 이번 slice에서는 수정하지 않았습니다.
- Browser/E2E는 실행하지 않았습니다. 이번 변경은 `summarize_slot_coverage()` 직접 호출 회귀 테스트 추가이며 UI 계약 변경이 없습니다.
