# Advisory Log: 2026-04-28 — M62 완료 및 M63 방향 권고

## 개요
M62 Axis 1+2 완료를 통해 `PreferencePanel`에 교정 요약 통계(전체/활성 수)가 시각화됨. 다음 마일스톤 M63에서는 단순히 수치를 보여주는 것을 넘어, 시스템이 무엇을 반복적으로 교정하고 있는지 "내용(Content)"에 기반한 가시성을 확보할 것을 권고함.

## 분석
- **현 상태**: `/api/corrections/summary` 응답에 `top_recurring_fingerprints`가 포함되어 있지만, UI에서는 아직 활용되지 않음. 또한 현재 백엔드 응답은 fingerprint와 count만 제공하여, UI에서 실제 어떤 텍스트가 교정되었는지 알 수 없는 상태임.
- **리스크**: 숫자(Count)만으로는 교정 루프가 "유효한 학습"을 하고 있는지, 아니면 "노이즈"만 쌓고 있는지 판정하기 어려움. `TASK_BACKLOG`의 "physical correction analytics/validation" 목표를 달성하려면 패턴의 실체를 확인할 수 있어야 함.
- **기회**: 상위 반복 패턴의 스니펫(Snippet)을 함께 제공함으로써, 운영자가 별도의 DB 조회 없이도 주요 교정 경향을 즉시 파악하고 검증(Validation)할 수 있는 토대를 마련할 수 있음.

## 권고 사항
`RECOMMEND: implement M63 Axis 1 — top recurring patterns content visibility`

### 권고 이유
1. **Semantic Analytics**: 숫자 중심에서 내용 중심의 분석으로 진화하여 "Reviewed-Memory"의 질적 분석이 가능해짐.
2. **Same-family Completion**: `PreferencePanel`에서 개별 선호의 스니펫을 보여주듯이, 교정 통계에서도 주요 패턴의 스니펫을 보여주는 것이 일관된 사용자 경험을 제공함.
3. **Bridge to Validation**: 패턴의 내용을 직접 보는 것은 향후 "교정 패턴 승인/거부" 기능을 위한 필수 전제 조건임.

### 구현 슬라이스
- **백엔드**: `AggregateHandlerMixin.get_correction_summary()`를 수정하여 `top_recurring_fingerprints` 항목에 `original_snippet`과 `corrected_snippet`을 추가.
- **프론트엔드**: `PreferencePanel.tsx`에서 상위 1-2개 패턴의 스니펫을 툴팁이나 확장 영역에 표시.

## 결론
단순 통계를 넘어 "무엇이 반복되는가"를 보여주는 M63 Axis 1 진행을 강력히 권고함.
