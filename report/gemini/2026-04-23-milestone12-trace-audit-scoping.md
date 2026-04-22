# 2026-04-23 Milestone 12 Trace Audit Scoping

## 요약
- Milestone 11 종료 후, 차기 단계인 Milestone 12 "Personalized Local Model Layer" 진입을 위한 전제 조건 평가를 수행함.
- 현재 데이터 생성 배관은 완성되었으나 데이터의 정량적/정성적 수준을 확인하는 **Trace Collection Audit (Axis 1)**이 우선적으로 필요하다고 판단함. (Option A)

## 권고 사항 (Milestone 12 Axis 1: Trace Collection Audit & Baseline)

시스템이 수집 중인 교정, 선호도, 승인 이력을 전수 조사하여 Milestone 12 구현을 정당화할 수 있는 수치를 확보합니다.

### 핵심 변경 내용
1. **진단 유틸리티 추가**: `scripts/audit_traces.py`를 신규 생성하여 전체 세션 JSON을 스캔하고 주요 통계(교정 쌍 수, 피드백 비율 등)를 산출함.
2. **SessionStore 확장**: 다중 세션의 요약 정보를 효율적으로 집계하기 위한 `list_all_session_traces()`와 같은 읽기 전용 헬퍼 메서드를 `storage/session_store.py`에 추가함.
3. **Audit 보고서**: 스크립트 실행 결과를 바탕으로 현재 데이터가 "Personalization"을 시작하기에 충분한지(Preconditions met 여부)를 결론짓는 보고서 형식을 정의함.

### 테스트 전략
- **단위 테스트**: `tests/test_audit_utility.py`에서 모의 세션 데이터를 활용해 집계 로직의 정확성을 검증함.
- **안전성 확인**: 전수 조사 과정에서 대량의 파일 I/O가 발생해도 메인 서비스(`app.web`)의 응답성에 영향을 주지 않는지 점검함.

## 판단 근거
- **근거 중심 설계**: "Personalization"은 모델의 가변성을 높이는 위험한 작업이므로, 실제 로컬에 쌓인 데이터의 품질이 이를 뒷받침하는지 먼저 증명해야 함.
- **Gap Milestone 회피**: 새로운 마일스톤을 만들기보다, Milestone 12의 첫 번째 단계를 "Precondition Verification"으로 설정함으로써 프로젝트 흐름을 유지하면서도 기술적 정당성을 확보할 수 있음.
