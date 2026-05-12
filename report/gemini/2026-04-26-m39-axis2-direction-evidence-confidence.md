# 2026-04-26 M39 Axis 2 — Review Evidence Enrichment — Confidence & Metadata

## 상황 개요
- **M39 Axis 1 (Multi-turn Context) 완료**: 리뷰 큐(Review Queue) 후보의 직전 대화 문맥(context_turns)을 API와 UI에 성공적으로 반영했습니다.
- **M39 전략적 목표**: "Review Context & Reasoning"의 일환으로, 운영자가 후보의 신뢰도를 판단할 수 있는 정량적 지표를 보강해야 합니다.
- **현상**: 현재 운영자는 고품질(is_high_quality) 배지만으로는 해당 후보가 얼마나 자주 발생한 패턴인지, 혹은 얼마나 많은 증거(evidence)에 기반한 것인지 알기 어렵습니다.

## 판단 근거
1. **정량적 신뢰도 필요**: 단순히 '무엇(What)'과 '맥락(Context)'을 아는 것을 넘어, '얼마나(How many)'를 보여줌으로써 운영자의 의사결정 속도를 높일 수 있습니다.
2. **증거 기반 리뷰**: 후보를 지지하는 아티팩트(supporting_artifact_ids)와 확인 신호(supporting_signal_refs)의 개수를 노출하면, 반복적으로 학습된 선호와 일회성 교정을 쉽게 구분할 수 있습니다.
3. **M39의 완결성**: Axis 1에서 맥락(Context)을 해결했으므로, Axis 2에서 정량적 근거(Reasoning)를 해결하여 Milestone 39를 마무리하는 것이 적절합니다.

## 권고 사항 (RECOMMENDATION)
- **결정**: Milestone 39 Axis 2를 시작하여 리뷰 증거의 정량적 지표를 보강합니다.
- **RECOMMEND: implement Milestone 39 Axis 2: Review Evidence Enrichment — Evidence Confidence & Metadata**
    - `serializers.py`: `ReviewQueueItem`에 증거 카운트(지원 아티팩트 수, 확인 신호 수, 누적 세션 수 등)를 포함하도록 확장합니다.
    - `ReviewQueuePanel.tsx`: "신뢰도" 또는 "증거" 섹션을 추가하여 해당 카운트들을 운영자에게 표시합니다.
    - 필요 시, 증거가 일정 수준 이상일 때 "신뢰도 높음" 등의 추가적인 시각적 힌트를 제공합니다.

### 예상 결과
- 운영자가 선호(Preference) 수락 시 정량적 데이터를 근거로 더 빠르고 정확하게 판단 가능.
- 시스템이 학습한 규칙의 강도를 직관적으로 파악하여 Milestone 39의 목표 달성.
