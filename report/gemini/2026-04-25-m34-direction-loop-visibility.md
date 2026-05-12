# 2026-04-25 M34-direction-loop-visibility

## 결정: 후보 1 (reviewed-memory loop 가시성 개선)

### 근거
1. **사용자 가치 (North Star)**: 프로젝트의 핵심 목표 중 하나는 "가르칠 수 있는 로컬 개인 에이전트"입니다. 사용자가 자신의 선호(Preference)가 응답에 실제로 반영되었는지 시각적으로 확인(Badge/Label)할 수 있게 하는 것은 루프의 신뢰도를 높이는 가장 중요한 UX 단계입니다.
2. **기능적 완결성**: 현재 `MockModelAdapter`는 텍스트 접두어로 반영 여부를 표시하지만, 실 서비스 어댑터(Ollama)는 시스템 프롬프트에만 선호를 주입하고 사용자에게는 알리지 않습니다. 이를 UI 수준에서 표준화된 뱃지로 통합하여 일관성을 확보합니다.
3. **가이드라인 준수**: `GEMINI.md`의 "same-family user-visible improvement" (순위 2)에 해당하며, M31에서 검증된 기능적 루프를 사용자에게 시각화하여 "shipped product"로서의 완성도를 높입니다.

### 권고 Slice (M34 Axis 1)
- **목표**: 채팅 응답 카드(Message Bubble)에 적용된 선호(Applied Preferences) 목록을 표시하는 시각적 뱃지 추가 및 영속성 보장.
- **실행 항목**:
    1. **영속성 수정**: `app/serializers.py`의 `_serialize_session`에서 메시지 내 `applied_preference_ids`를 기반으로 `applied_preferences` 객체 목록을 복원하도록 수정 (세션 로드 시에도 뱃지 유지).
    2. **Frontend UI**: `app/frontend/src/components/MessageBubble.tsx`에서 `applied_preferences`가 존재할 경우 "선호 N건 반영" 뱃지와 툴팁(또는 목록) 노출.
    3. **E2E 검증 보강**: M31에서 추가된 loop smoke test를 갱신하여, 응답 텍스트의 prefix뿐만 아니라 UI 뱃지의 노출 여부와 개수(`data-testid` 활용)를 검증하도록 업데이트.
- **검증**: `make e2e-test` (147 scenarios) PASS 확인.

### 후보 검토
- **후보 2 (Preference Lifecycle UX)**: 선호 관리 기능(편집/정지)도 중요하나, "반영 여부 확인"이 되지 않는 상태에서 관리 기능만 강화하는 것은 사용자 체감 효과가 낮습니다. 가시성 확보를 우선합니다.
- **후보 3 (기타 - 구조 분리)**: 이전 권고(SEQ 168)에 따라 구조 분리 phase를 일단락하고 기능적 가치에 집중하기로 결정했으므로, 현재로서는 제외합니다.
