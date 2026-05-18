# 2026-04-29 M85 Axis 2 Scope Arbitration Advisory

## 현황 및 문제점
M85 Axis 1 (Backend Reliability Seeding) 구현이 완료되었으며, `PreferencePanel`에는 이미 신뢰도 배지(`is_highly_reliable`) 표시 로직이 존재합니다. 그러나 사용자 관점에서의 "관측 루프(Observability Loop)"를 완성하기 위해서는 단순한 배지 표시를 넘어, 승격(Promote) 실행 직후의 피드백을 강화할 필요가 있습니다.

현재 `lastPromoteResult`는 승격된 항목의 개수와 활성화된 개수만 표시할 뿐, 승격된 선호도가 즉시 "신뢰할 수 있는(Highly Reliable)" 상태로 주입 루프에 진입했는지 여부를 알려주지 않습니다. 이는 M85의 핵심 목표인 "승격 즉시 적용"이 성공했는지를 사용자가 명시적으로 인지하기 어렵게 만듭니다.

## 판단 근거
1. **Option B의 필요성**: 기존 배지(Option A)는 목록 전체를 탐색해야 확인할 수 있는 수동적 피드백입니다. 승격 결과 팝업이나 피드백 텍스트에 "신뢰도 전이 성공" 상태를 포함함으로써 능동적 피드백을 완성해야 합니다.
2. **머지 게이트(Merge Gate)**: PR #62–#69는 이미 머지되었으나, PR #71–#73의 retarget 및 머지가 남아 있습니다. 로컬 파일시스템 제약으로 브랜치 정리가 불가능하므로, PR 머지는 오퍼레이터의 개입이 필수적인 상태입니다.
3. **슬라이스 구분**: Axis 2를 "승격 결과 피드백 강화"로 정의하고 진행하는 것이 루프 완성도 면에서 가장 합리적입니다.

## 권고 사항
**RECOMMEND: B (Enhance promote result feedback with reliability status)**

### 상세 구현 권고
- **Backend**: `promote_correction_pattern` 응답 스키마에 `is_highly_reliable` 여부를 포함하도록 확장.
- **Frontend**: `PreferencePanel`의 `lastPromoteResult` 표시부에서 신뢰도 확보 상태(예: "신뢰도 즉시 확보됨" 안내)를 가시화.

### 후속 조치
- Axis 2 구현 전, 오퍼레이터는 PR #71–#73의 머지 처리를 완료하여 `main` 브랜치의 진실성(Truth-sync)을 확보해야 합니다.
- Axis 2 완료 후 M85 전체를 종료하고 doc-sync(MILESTONES 갱신)를 수행할 것을 권장합니다.
