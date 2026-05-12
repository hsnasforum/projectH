# 2026-04-25 M35-direction-preference-management-ux

## 결정: 후보 1 (preference lifecycle 완성도 개선)

### 근거
1. **기능적 완결성 확보 (North Star)**: Milestone 34에서 "선호 반영 가시성(Badge)"을 확보했습니다. 이제 사용자가 반영된 정보를 보는 것에 그치지 않고, 잘못 반영된 선호를 즉시 관리(확인 및 정지)할 수 있게 함으로써 "사용자 피드백 루프"를 완성해야 합니다.
2. **사용자 가치 (User-Visible Improvement)**: 적용된 선호 뱃지를 클릭하여 상세 내용을 확인하고 즉시 제어할 수 있는 기능은 에이전트의 투명성과 통제권을 직접적으로 높이는 고가치 UX입니다.
3. **가이드라인 준수**: `GEMINI.md`의 "same-family user-visible improvement" 원칙을 따릅니다. M34(가시성)와 동일한 "Reviewed-Memory Loop" family의 품질을 극대화합니다.

### 권고 Slice (M35 Axis 1)
- **목표**: 채팅 응답의 "선호 반영 뱃지"를 인터랙티브하게 개선하여 상세 확인 및 즉시 제어 기능 제공.
- **실행 항목**:
    1. **Frontend UI**: `MessageBubble.tsx`의 `applied-preferences-badge`를 버튼으로 변경하고, 클릭 시 적용된 선호 목록(설명 포함)을 보여주는 Popover 노출.
    2. **Inline Action**: Popover 내의 각 선호 항목 옆에 "일시중지(Pause)" 버튼을 추가하여, `PreferencePanel`을 찾지 않고도 즉시 반영을 중단할 수 있는 빠른 접근 경로 제공.
    3. **E2E 검증**: 새 시나리오를 추가하여 뱃지 클릭 -> Popover 노출 -> 일시중지 클릭 -> 해당 선호가 `paused` 상태로 전이됨을 확인.
- **검증**: `make e2e-test` (148 scenarios 예상) 및 관련 unit tests PASS 확인.

### 후보 검토
- **후보 2 (새 기능)**: SQLite 기본 전환 등도 중요하나, 현재 사용자에게 노출된 "선호 반영" 기능의 UX를 매끄럽게 다듬는 것이 제품의 완성도 면에서 더 높은 평가를 받습니다.
- **후보 3 (유지보수)**: PR #33 머지로 큰 고비를 넘겼으므로, 소규모 내부 정리는 기능 작업 사이사이에 opportunistic하게 진행하는 것이 적절합니다.
