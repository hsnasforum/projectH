# 2026-04-25 M31-axis2-loop-smoke-test

## 결정: 후보 A (reviewed-memory loop end-to-end smoke test)

### 근거
1. **기능적 완결성 검증**: M29에서 구현된 sync bridge와 기존의 preference injection 로직이 결합되어 전체 루프가 실제로 동작하는지 확인할 시점입니다.
2. **리스크 감소**: 구조적 변경(M30) 이후 기능적 핵심 경로인 "교정 반영" 흐름에 회귀가 없는지 보장합니다.
3. **가이드라인 준수**: `GEMINI.md`의 "same-family current-risk reduction" 및 "user-visible improvement" 원칙에 부합합니다.

### 권고 Slice
- **목표**: `e2e/tests/web-smoke.spec.mjs`에 전체 reviewed-memory loop를 검증하는 시나리오 추가.
- **테스트 시나리오**:
    - `/api/preferences/audit`를 모킹하여 "활성 교정"이 있는 상태를 시뮬레이션.
    - `PreferencePanel`에서 "후보 동기화" 버튼 노출 및 클릭 확인.
    - 동기화로 생성된 `candidate` 선호를 "수락/활성화"하여 `active` 상태로 전환.
    - 새로운 메시지 전송 시, `MockModelAdapter`가 반환하는 응답에 `[모의 응답, 선호 1건 반영]` 접두어가 포함되는지 확인하여 prompt injection 검증.
- **검증**: `make e2e-test`를 실행하여 147개(기존 146 + 신규 1) 시나리오 통과 확인.

### 후보 검토
- **후보 B (다른 방향)**: 현재로서는 흩어져 있던 기능(correction, preference, injection)을 하나의 검증된 루프로 묶는 것이 가장 시급한 과제입니다. 인프라 개선(SQLite default 등)은 이미 상당 부분 진행되었으므로 기능 검증을 우선합니다.
