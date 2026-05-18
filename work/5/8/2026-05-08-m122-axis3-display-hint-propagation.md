# 2026-05-08 M122 Axis 3 display/hint propagation

## 변경 파일

- `core/agent_loop.py`
- `tests/test_smoke.py`
- `work/5/8/2026-05-08-m122-axis3-display-hint-propagation.md`

## 사용 skill

- `investigation-quality-audit`: entity-card claim coverage의 UNRESOLVED 표시와 progress summary 전파가 불확실성을 숨기지 않고 web investigation 경계를 유지하는지 점검했다.
- `work-log-closeout`: 구현 라운드 종료 기록의 필수 섹션, 실제 검증 결과, 남은 리스크 정리에 사용했다.

## 변경 이유

- M122 Axis 2에서 `CoverageStatus.UNRESOLVED`가 추가됐지만 display/hint 함수 일부가 아직 `UNRESOLVED`를 명시적으로 처리하지 않았다.
- 이번 슬라이스는 값은 있으나 신뢰 출처가 없는 슬롯을 `미해결`로 표시하고, progress summary의 unresolved bucket에 포함되게 하는 것이다.

## 핵심 변경

- `_claim_coverage_status_rank()`에서 `CoverageStatus.UNRESOLVED`를 명시적으로 rank 0으로 처리했다.
- `_claim_coverage_status_label()`에서 `CoverageStatus.UNRESOLVED`를 `미해결`로 표시하게 했다.
- `_build_claim_coverage_progress_summary()`의 unresolved slot 집합에 `CoverageStatus.UNRESOLVED`를 포함했다.
- 기존 claim coverage status label/rank 회귀 테스트에 UNRESOLVED 기대값을 추가했다.
- progress summary가 UNRESOLVED 슬롯을 누락하지 않고 `미해결` 상태로 표면화하는 회귀 테스트를 추가했다.

## 검증

- `python3 -m py_compile core/agent_loop.py`
  - PASS.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_claim_coverage_conflict_status_label_rank_and_probe_queries tests.test_smoke.SmokeTest.test_build_claim_coverage_progress_summary_includes_unresolved_status tests.test_smoke.SmokeTest.test_build_claim_coverage_progress_summary_focus_slot_unresolved_wording_branches_by_status`
  - PASS: 3개 테스트 통과.
- `python3 -m unittest -v tests.test_smoke`
  - PASS: 156개 테스트 통과.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - PASS: 출력 없음.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py work/5/8/2026-05-08-m122-axis3-display-hint-propagation.md`
  - PASS: 출력 없음.

## 남은 리스크

- 이번 라운드는 backend display/hint 전파와 smoke regression만 수행했다. handoff 금지 범위에 따라 frontend/UI/E2E와 `docs/`는 수정하지 않았다.
- web investigation은 계속 secondary, read-only, permission-gated, locally logged 경계 안에 있으며 source ranking, fetch/search 권한 모델, 저장 schema는 바꾸지 않았다.
