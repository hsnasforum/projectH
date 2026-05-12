# 2026-05-12 M124 Axis 3 스코프 및 다음 슬라이스 권고

## 분석
M124 "Investigation Observability & Metrics" 아크는 Axis 1을 통해 수렴 벤치마크 패턴을 확립하고, Axis 2를 통해 런타임 품질 요약 지표를 확보했습니다. 현재 지표 체계는 동작하지만, 벤치마크 fixture가 "개발", "서비스/배급" 등 2개 슬롯에만 국한되어 있어 전체 `entity-card`의 품질을 완벽히 보증하기에는 커버리지가 부족합니다.

제시된 후보 중 **3번(수렴률 smoke 지표 확장)**을 다음 슬라이스로 추천합니다. 그 이유는 다음과 같습니다:
1. **완결성 확보**: 5개 핵심 슬롯 전체에 대해 수렴 경로(UNRESOLVED→STRONG, CONFLICT→STRONG)를 고정함으로써, M123에서 도입된 고도화된 쿼리 로직이 모든 데이터 유형에서 정상 작동함을 보장합니다.
2. **지표 신뢰도 향상**: 아크의 목표인 "Metrics"가 특정 필드에만 편향되지 않고 전체 기능 영역을 대변하게 됩니다.
3. **리스크 감소**: 현재 PR 스택이 깊은 상황에서 로직을 대폭 수정하는 로그(1번)보다 테스트 커버리지를 채우는 안정적인 슬라이스가 아크 종료 전 베이스라인 확립에 더 유리합니다.

## 권고

**RECOMMEND: implement m124_axis3_convergence_benchmark_expansion**
- **대상 파일**: `tests/test_smoke.py`
- **구현 내용**:
    - "장르/성격", "상태", "이용 형태" 슬롯에 대해 UNRESOLVED 및 CONFLICT 상황에서의 수렴 fixture 테스트 케이스 추가.
    - 기존 2개 슬롯과 동일한 패턴의 `summarize_slot_coverage()` 직접 호출 검증 로직 적용.
- **RATIONALE**: M124 아크의 핵심 결과물인 벤치마크 지표를 `entity-card` 전체 슬롯으로 확장하여 품질 계측의 완결성을 확보하고, 향후 기능 변경 시의 안정적인 가드레일을 완성합니다.

## 절차
1. `tests/test_smoke.py`에 남은 3개 슬롯(장르/성격, 상태, 이용 형태)의 수렴 시나리오 fixture 추가.
2. 166+N개 전체 테스트 PASS 확인.
3. `docs/MILESTONES.md` 및 `docs/TASK_BACKLOG.md`에 M124 Axis 3 완료 및 아크 종료 준비 기록.
