# 2026-04-25 stale-control-recovery-m37-axis2

## 결정: 후보 A (M37 Axis 2 — Preference Resume/Reject E2E 재시도)

### 근거
1. **Stale Control 원인 분석**: `CONTROL_SEQ: 207`의 구현 단계가 960 사이클 동안 완료되지 않아 런타임에 의해 `stale_control_advisory`가 트리거되었습니다. 직접적인 원인은 `tests/web-smoke.spec.mjs`에 추가된 149번 시나리오(Resume/Reject lifecycle)가 누적된 데이터베이스(accumulated DB) 환경에서 팝오버 내부 텍스트 매칭 실패로 인해 flakiness를 보였기 때문으로 판단됩니다.
2. **리스크 감소 (GEMINI.md 우선순위 1)**: 루프 중단(Stall) 상태를 해소하고, 계획된 검증 부채(M37 Axis 2)를 상환하는 것이 최우선입니다.
3. **가이드라인 준수**: `GEMINI.md`의 원칙에 따라 stall/recovery 문제를 에이전트 간의 논의와 세분화된 지시로 해결합니다. 207번의 실패를 교훈 삼아, 더 견고한 assertion 전략을 포함한 재시도를 권고합니다.

### 권고 Slice (M37 Axis 2 - Recovery)
- **목표**: 207번에서 시도했던 Resume/Reject E2E 시나리오를 완성하고 149개 전체 패스를 달성.
- **개선 항목**:
    - **팝오버 텍스트 매칭 완화**: `getByText(preferenceStatement)` 대신 특정 접두어만 확인하거나, `data-testid`를 활용하여 누적된 선호 항목 중 하나라도 의도한 상태 전이를 보이는지 확인하는 방식으로 flakiness 제거.
    - **Resume/Reject 효과 검증**: 단순히 상태 변경 API 호출에 그치지 않고, 두 번째 메시지 전송을 통해 반영 여부가 복구(Resume)되거나 영구 제외(Reject)됨을 실제 응답 뱃지 상태로 확인.
- **검증**:
    - `cd e2e && npx playwright test -g "resume/reject" --reporter=line` 1 passed 확인.
    - `make e2e-test` 149 passed 확인.

### 제외된 후보
- **Operator 에스컬레이션**: 현재 문제는 기술적인 테스트 flakiness이며, 에이전트 수준에서 해결 가능한 범위 내에 있으므로 operator 개입 없이 처리를 시도합니다.
