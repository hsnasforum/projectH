# Advisory Log: 2026-04-23 M14 Milestone 정의 및 우선순위 중재

## 개요
M13 (Applied Preference Effectiveness Tracking)의 주요 축(Axes 1–6)이 Shipped 상태로 전환됨에 따라, 다음 Milestone인 M14의 정의와 첫 번째 구현 슬라이스(implement slice)에 대한 중재 요청입니다. 특히 SQLite backend의 기능 격차(gap) 처리와 deferred된 frontend 기능의 우선순위 결정이 핵심입니다.

## 분석 및 판단

### 1. M14 정의: 개인화 무결성 및 트레이스 품질 통합 (Personalization Integrity and Trace Quality Integration)
M13에서 구축한 선호도 적용 및 효과 측정 인프라를 바탕으로, M14는 이를 사용자에게 가시화하고 데이터 품질(Trace Quality)을 검토 프로세스에 직접 연동하는 단계로 정의합니다.
- **핵심 목표**: 백엔드 무결성 확보, 선호도 신뢰도 가시화, 품질 기반 검토 루프 강화.

### 2. SQLitePreferenceStore auto-activation 우선순위 (Q2)
- **판단**: **M14의 첫 번째 슬라이스**로 처리할 것을 권고합니다.
- **이유**: `projectH`의 핵심 원칙인 "honestly synchronized" 상태와 백엔드 간 일관성 유지를 위해, M13 Axis 6의 미완된 부분을 먼저 닫는 것이 "same-family current-risk reduction" 관점에서 가장 우선순위가 높습니다. 이를 별도 backlog로 미루는 것은 기술 부채를 방치하는 결과가 될 수 있습니다.

### 3. M13 Axis 5 Frontend 및 중복성 확인 (Q3)
- **판단**: **M14의 두 번째 슬라이스**로 권고하며, 기존 `PreferencePanel`과 통합합니다.
- **분석**: `app/frontend/src/components/PreferencePanel.tsx` 확인 결과, 이미 `reliability_stats`를 표시하는 코드가 일부 포함되어 있습니다. 이는 "Axis 5b (seq 16)"에서 시도된 UI 작업과 현재의 데이터 모델이 결합된 결과로 보입니다. 따라서 별도의 surface를 만들기보다는, 현재 `deferred` 상태인 이 기능을 실제 데이터와 연결하여 "Shipped" 상태로 만드는 것이 효율적입니다.

### 4. M12 Axis 3 (Trace Quality Scoring)의 처리
- **판단**: M14의 세 번째 슬라이스로 배치합니다.
- **이유**: 인프라와 가시성이 확보된 후, 보류되었던 품질 점수(scoring)를 검토 큐(Review Queue) 등에 연동하여 사용자에게 "고품질 트레이스"를 우선 보여주는 등의 UX 개선으로 이어갑니다.

## 권고 사항 (RECOMMENDATION)

1. **M14 명명**: `Personalization Integrity and Trace Quality Integration`
2. **첫 번째 슬라이스**: `SQLitePreferenceStore auto-activation parity` (M13 Axis 6의 백엔드 격차 해소)
3. **후속 슬라이스**:
   - `M13 Axis 5 frontend verification & shipping` (선호도 신뢰도 UI 검증 및 Shipped 전환)
   - `M12 Axis 3 trace quality scoring integration` (품질 점수 UI/UX 연동)

이 방향은 "same-family risk reduction" -> "user-visible improvement" -> "new quality axis"의 우선순위 원칙에 부합합니다.
