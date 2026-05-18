# 2026-05-12 M124 Axis 1 스코프 및 첫 번째 슬라이스 권고

## 분석
M123 아크를 통해 웹 조사 파이프라인의 핵심 로직(UNRESOLVED 억제, 공식 출처 탐색, CONFLICT 크로스-검증)이 개선되었습니다. M124 "Investigation Observability & Metrics" 아크의 목적은 이러한 개선 사항이 실제로 조사 품질(수렴률)을 얼마나 향상시켰는지 정량적으로 측정하고 지속적으로 검증하는 것입니다.

제시된 세 가지 후보 중 **1번(수렴률 smoke fixture)**이 가장 우선순위가 높습니다. 그 이유는 다음과 같습니다:
1. **검증 우선 원칙**: 로직 개선 후에는 그 효과를 증명할 수 있는 벤치마크가 필요합니다.
2. **회귀 방지**: 향후 조사 로직 수정 시 수렴률이 떨어지지 않는지 자동으로 감시할 수 있는 안전장치가 됩니다.
3. **지표의 기초**: 2번(로그)이나 3번(필드)은 운영 중 데이터를 수집하지만, 1번은 통제된 환경에서 알고리즘의 "이론적 최대 성능"을 계측할 수 있게 해줍니다.

## 권고

**RECOMMEND: implement m124_axis1_convergence_benchmark**
- **대상 파일**: `tests/test_smoke.py`
- **구현 내용**:
    - `_build_entity_second_pass_queries`의 입출력을 테스트하는 고정 fixture 시나리오 구축.
    - 1차 조사 결과(UNRESOLVED/CONFLICT 상태)를 주입하고, 생성된 2차 쿼리에 대해 신뢰 출처가 포함된 가상의 검색 결과를 응답했을 때 최종 `summarize_slot_coverage`가 `STRONG`으로 전환되는지 확인하는 통합 테스트 케이스 추가.
    - 주요 수렴 시나리오(예: "공식 사이트 탐색을 통한 UNRESOLVED 해소", "교차 검증을 통한 CONFLICT 해소")를 명시적으로 검증.
- **RATIONALE**: M123에서 개선된 조사 로직이 실제로 슬롯 상태를 UNRESOLVED/CONFLICT에서 STRONG으로 전환시키는지 정량적으로 검증하고, 향후 품질 저하를 막기 위한 벤치마크 기반을 마련합니다.

## 절차
1. `tests/test_smoke.py`에 웹 조사 수렴 테스트 전용 클래스 또는 메서드 그룹 추가.
2. 각 슬롯 상태별(UNRESOLVED, CONFLICT, WEAK) 1차/2차 조사 시뮬레이션 데이터 준비.
3. M123에서 추가된 로직(공식 probe, 크로스-검증 쿼리)이 정상 작동하여 최종 상태가 개선되는지 검증.
4. `docs/MILESTONES.md` 및 `docs/TASK_BACKLOG.md`에 M124 Axis 1 정의 및 시작 기록.
