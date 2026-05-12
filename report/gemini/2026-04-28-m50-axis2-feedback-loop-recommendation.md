# Advisory Log: 2026-04-28 — M50 Axis 2 피드백 루프 권고

## 개요
M50 Axis 1+2(구현) 완료 후, 선호도 주입 가시성(Visibility)의 다음 단계로 사용자 피드백 루프(Feedback Loop)를 통한 신뢰도 정제(Refinement)를 권고함.

## 분석
- **현 상태**: M50 Axis 1을 통해 "이번 응답 반영" 배지가 PreferencePanel에 표시됨. 사용자는 어떤 선호가 반영됐는지 알 수 있지만, 그 적용의 적절성에 대해 직접적인 의사를 표시할 경로는 없음.
- **리스크**: 현재 `reliability_stats`의 `corrected_count`는 메시지 전체 교정이나 메시지 레벨의 부정적 피드백에 의존함. 한 메시지에 여러 선호가 적용된 경우, 특정 선호만 잘못 적용되었더라도 메시지 전체의 부정적 신호로 인해 다른 선호들의 신뢰도까지 함께 낮아질 위험(Signal Noise)이 있음.
- **기회**: 가시성이 확보된 지금, "이 선호는 이 응답에 잘 적용되었습니다/잘못 적용되었습니다"라는 세밀한(Granular) 피드백을 수집하여 `is_highly_reliable` 판정의 정확도를 높일 수 있음.

## 권고 사항
`RECOMMEND: implement M50 Axis 2(product) — 선호도 피드백 루프`

### 구현 방향
1. **백엔드**: `POST /api/preferences/record-feedback` 엔드포인트 신설. `message_id`, `preference_id`, `label` (helpful/incorrect) 수신.
2. **저장소**: 세션 메시지 내의 `applied_preferences_feedback` (가칭) 슬롯에 기록하거나, `session_store`의 `pstats` 집계 로직이 이 개별 피드백을 우선하도록 수정.
3. **프론트엔드**: `MessageBubble`의 적용 선호도 팝오버(popover) 내 각 항목에 "정확함" / "부정확함" 버튼 추가.

### 우선순위 근거
- **User-visible improvement**: 사용자가 시스템의 학습 결과에 대해 즉각적으로 개입하고 교정할 수 있는 효능감을 제공함.
- **Current-risk reduction**: 잘못된 선호가 "신뢰도 높음"으로 오판되는 것을 방지하고, 반대로 좋은 선호가 억울하게 신뢰도를 잃는 것을 막음.
- **Same-family completion**: M50의 목표인 "Visibility"를 완성하고 "Interaction"으로 연결하는 자연스러운 확장임.

## 결론
M51로 넘어가기 전, M50의 제품 가치를 완성하는 "피드백 루프" 슬라이스를 진행할 것을 강력히 권고함.
