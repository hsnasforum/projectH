# Advisory Log: 2026-04-26-m43-a2-preference-transition-visibility-recommendation

## 요약
M43 Axis 1(Transition Reason Recording)이 코드 및 문서 수준에서 성공적으로 완료되었음을 확인했습니다. 차기 구현 슬라이스로 **후보 A (transition_reason 표시)**를 선정합니다. 이는 이전에 기록하기 시작한 감사 데이터를 사용자에게 직접 노출함으로써 "Reviewed-Memory" 계층의 투명성을 완성하는 자연스러운 후속 단계입니다.

## 분석 및 판단
1. **M43 Axis 1 완료**:
   - `activate`/`pause`/`reject` 시 `transition_reason`을 수집하고 `task_log`에 기록하는 백엔드 로직(`eff9bdb`)과 관련 문서(`092c19e`) 동기화가 완료되었습니다.
   - 현재 진실의 원천(Truth)은 동기화되어 있으며, 다음 기능 확장 준비가 되었습니다.

2. **후보 비교 및 선정**:
   - **후보 A (Visibility) — 선정**: `GEMINI.md`의 "same-family user-visible improvement" 원칙에 따라, 백엔드에 기록된 `transition_reason`을 UI(`PreferencePanel`)에 다시 노출합니다. 이는 이미 구현된 `review_reason_note` 노출 패턴과 일관성을 유지하며, 투자 대비 높은 UX 가치를 제공합니다.
   - **후보 B (Warning)**: UI 경고는 정합성 면에서 유용하나, 이미 기록된 데이터를 보여주는 것보다 우선순위가 낮습니다.
   - **후보 C (M44)**: M43의 목적이 "상태 전환의 감사 가능성"인 만큼, 기록된 데이터를 보여주는 것까지 포함하여 M43의 완성도를 높이는 것이 옳습니다.

3. **구현 전략**:
   - `list_preferences_payload`에서 `task_log`를 조회하여 각 선호도 항목의 마지막 상태 전환 사유를 추출합니다.
   - 프론트엔드 `PreferencePanel`에서 이를 "전환 사유" 등의 레이블로 표시합니다.

## 권고 사항
- **RECOMMEND: implement Candidate A (M43 Axis 2: Preference Transition Visibility in UI)**
- **Task**: `list_preferences_payload()`에서 최신 `transition_reason` 추출 및 `PreferencePanel` 노출.
- **Files**:
    - `app/handlers/preferences.py`: `task_log` 조회를 통한 `last_transition_reason` 필드 추가.
    - `app/frontend/src/api/client.ts`: `PreferenceRecord` 타입에 필드 추가.
    - `app/frontend/src/components/PreferencePanel.tsx`: UI 노출 및 스타일링.

## Next 3 Implementation Priorities (Updated)
1. **M43 Axis 2: 선호 상태 전환 사유 UI 노출**: Task Log에서 사유를 추출하여 표시 (Candidate A).
2. **M43 Axis 3: 전환 이유 미입력 시 시각적 표시**: "이유 없음" 상태의 가시성 강화.
3. **M44 준비**: 다음 마일스톤(Preference 기반 응답 필터링 등) 설계.
