# Advisory Log: 2026-04-28 — M63 완료 및 M64 방향 권고

## 개요
M63 Axis 1+2 완료를 통해 `PreferencePanel`에서 상위 반복 교정 패턴(Top Recurring Patterns)의 실제 내용(Snippet)을 확인할 수 있게 됨. "가시성(Visibility)" 단계가 완성되었으므로, M64에서는 이를 운영자가 승인하거나 거절할 수 있는 "검증(Validation)" 단계로 진입할 것을 권고함.

## 분석
- **성과**: 이제 운영자는 어떤 텍스트가 반복적으로 교정되고 있는지 UI에서 직접 확인할 수 있음. 이는 단순한 수치를 넘어 시스템의 학습 방향을 질적으로 판단할 수 있는 근거가 됨.
- **현 상태**: 가시화된 패턴에 대해 운영자가 조치를 취할 수 있는 UI적 수단이 없음. 현재 모든 교정 기록은 `recorded` 상태에 머물러 있음.
- **리스크**: 반복되는 패턴이 노이즈임이 판명되더라도 이를 걸러낼 방법이 없으면 `reliability_stats`에 왜곡이 발생할 수 있음. 반대로 유효한 패턴을 조기에 승인(Confirm)하여 선호도(Preference)로 승격시키는 프로세스가 지연됨.

## 권고 사항
`RECOMMEND: implement M64 Axis 1 — Pattern-level validation (confirmation)`

### 권고 이유
1. **From Visibility to Action**: M61-M63에서 구축한 분석 도구를 실제 데이터 정제에 활용하는 첫 단계임.
2. **Backlog Alignment**: `TASK_BACKLOG`의 "physical correction analytics/validation" 중 "Validation" 영역의 핵심 기능을 구현함.
3. **Lifecycle Management**: 교정 기록의 상태(Status)를 `RECORDED`에서 `CONFIRMED`로 전환함으로써, 향후 `PreferenceRecord`로의 자동/수동 승격(Promotion)을 위한 필터를 마련함.

### 구현 슬라이스
- **백엔드**: `AggregateHandlerMixin`에 `confirm_correction_pattern(payload)` 추가. 특정 `delta_fingerprint`를 가진 모든 교정 기록의 상태를 `CONFIRMED`로 일괄 업데이트.
- **프론트엔드**: `PreferencePanel.tsx`의 반복 패턴 목록 각 항목에 "승인(Confirm)" 버튼 추가.

## 결론
가시화된 교정 패턴을 운영자가 직접 검증하고 승인할 수 있는 M64 Axis 1 진행을 강력히 권고함.
