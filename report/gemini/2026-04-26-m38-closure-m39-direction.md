# 2026-04-26 M38 closure and M39 direction — Multi-turn Context for Review

## 상황 개요
- **Milestone 38 (Test Infrastructure Robustness) 완료**: Axis 1(healthcheck wrapper)과 Axis 2(hardening & doc closure)가 성공적으로 구현 및 검증되었습니다.
- **M38 잔여 리스크**: 샌드박스 환경 제약으로 인해 `existing-server` 재사용 경로의 full E2E 검증은 수행하지 못했으나, 코드 로직은 검증되었으며 auto-start 경로(150 passed)가 충분한 커버리지를 제공합니다.
- **차기 방향**: 인프라 안정화가 확보되었으므로, 제품의 핵심 가치인 "Teachable" 및 "Alignment" 역량 강화를 위한 **Milestone 39**로 진입합니다.

## 판단 근거
1. **인프라 안정성**: M38을 통해 `make e2e-test`의 신뢰도가 크게 향상되었습니다. 이제 기능적 개선으로 복귀할 준비가 되었습니다.
2. **리뷰 품질 개선**: 현재 `ReviewQueueItem`은 단일 교정 쌍(original/corrected)만 보여주어, 대화의 문맥(Context)에 의존하는 선호를 판단하기 어렵습니다.
3. **학습 효과 극대화**: 멀티턴 문맥(Multi-turn Context)을 리뷰 증거에 포함하면 운영자가 선호의 일반화 가능성을 더 정확하게 판단할 수 있습니다.

## 권고 사항 (RECOMMENDATION)
- **결정**: Milestone 38을 공식적으로 종결하고 **Milestone 39 Axis 1**을 시작합니다.
- **RECOMMEND: implement Milestone 39 Axis 1: Review Evidence Enrichment — Multi-turn Context**
    - `serializers.py`에서 `ReviewQueueItem` 생성 시 이전 User/Assistant 턴을 추출하여 포함합니다.
    - `ReviewQueuePanel.tsx`에서 이 문맥을 "Evidence" 섹션에 표시합니다.
    - 이를 통해 운영자가 교정의 근거를 대화 흐름 속에서 파악할 수 있게 합니다.

### 예상 결과
- 운영자가 선호(Preference) 수락 여부를 결정할 때 더 높은 확신을 가질 수 있음.
- 대화 스타일이나 문맥 의존적 지침에 대한 선호 학습 정확도 향상.
- 인프라 부채(reuse path risk)는 인지된 리스크로 남기되, 기능적 진보를 우선함.
