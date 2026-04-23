# 2026-04-23 Milestone 12 Trace Export Scoping

## 요약
- Milestone 12 Axis 1(Audit) 결과, 137개의 교정 쌍이 확인되어 개인화 자산화를 시작할 수 있는 기반이 마련됨.
- 다음 슬라이스로 흩어진 세션 로그를 표준 데이터셋 형식으로 변환하는 **Trace Export Utility (Axis 2)** 구현을 권고함. (Option B)

## 권고 사항 (Milestone 12 Axis 2: Trace Export Utility)

로컬 세션에 저장된 `grounded-brief` 교정 데이터를 추출하여 학습 및 평가에 용이한 JSONL 포맷으로 내보내는 도구를 구축합니다.

### 핵심 변경 내용
1. **내보내기 유틸리티 추가**: `scripts/export_traces.py`를 신규 생성하여 전체 세션을 스캔하고, 교정 쌍(Original Draft vs Corrected Text)을 `{"prompt": "...", "completion": "..."}` 형식의 JSONL로 저장함.
2. **SessionStore 스트리밍 지원**: 메모리 효율을 위해 전체 세션을 로드하지 않고 필요한 트레이스만 필터링하여 반환하는 이터레이터 패턴을 `storage/session_store.py`에 도입할 수 있음.
3. **피드백 결합**: 피드백 신호(Helpful/Unclear 등)가 있는 경우 이를 데이터셋의 메타데이터나 가중치로 포함할 수 있는 구조를 마련함.

### 테스트 전략
- **단위 테스트**: `tests/test_export_utility.py`에서 모의 데이터를 내보낸 후, 생성된 파일의 JSON 스키마와 내용이 일치하는지 검증함.
- **회귀 테스트**: 대량의 세션 파일 처리 시에도 파일 핸들이 고갈되지 않고 안정적으로 동작하는지 확인함.

## 판단 근거
- **자산화(Promotion to Assets)**: 단순한 로그가 아닌 "Personalization Asset"이 되기 위해서는 격리된 파일에서 나와 통합된 데이터셋 형태로 존재해야 함.
- **후속 단계 가속**: 표준화된 JSONL 데이터셋은 향후 Milestone 12의 "Adaptive Model Layer" 평가나 미세 조정(Fine-tuning) 실험의 직접적인 입력값이 됨.
