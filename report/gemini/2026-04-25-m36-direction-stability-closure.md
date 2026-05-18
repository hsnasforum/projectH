# 2026-04-25 M36-direction-stability-closure

## 결정: 후보 A (M36 종결 및 PR #34 머지 준비)

### 근거
1. **검증 충분성 확보 (GEMINI.md 우선순위 1)**: M36 Axis 1-2를 통해 "일시중지(Pause)"가 즉각적으로 반영(Injection 중단)되고, 새로고침 후에도 유지(Persistence)됨을 148개 E2E 시나리오로 입증했습니다. 이는 "사용자 통제에 따른 루프 반응성"이라는 핵심 기능적 계약을 증명한 것입니다.
2. **환경 리스크 회피**: 현재 테스트 환경의 데이터베이스 누적 상태(6+ preferences)로 인해 Resume/Reject의 개별 상태 전이를 E2E 수준에서 엄격하게 assertion하는 것은 불필요하게 복잡하며, M35 Axis 1에서 경험한 대량 실패(4회)를 재발시킬 리스크가 큽니다. 해당 전이 로직은 이미 229개 unit tests에서 충분히 보호되고 있습니다.
3. **진실성 및 진도 유지**: M34(가시성)부터 M36(Pause 안정화)까지의 고가치 기능 번들을 조속히 `main`에 통합하여 PR #34를 닫는 것이 프로젝트의 리스크 관리 및 다음 단계(SQLite 전환 등) 진입을 위해 유리합니다.

### 권고 Slice (M36 Axis 3 — Release Gate & PR Update)
- **목표**: M34–M36 통합 번들 최종 확정 및 머지 승인 요청.
- **실행 항목**:
    1. **PR 갱신**: PR #34 (Interactive Applied Preference Management)의 설명을 M36의 안정성 검증 성과(Pause functional effect & persistence)까지 포함하도록 최종 업데이트.
    2. **최종 게이트**: `make e2e-test`를 통해 148개 시나리오 전수 PASS 상태에서 더 이상의 기능 추가 없이 "Release Gate"를 통과시킨다.
    3. **머지 요청**: Operator에게 PR #34의 머지 승인을 요청한다.
- **검증**: 148 E2E + 229 unit tests PASS 유지.

### 후보 검토
- **후보 B (Axis 3 강행)**: 직접 API 호출을 통한 검증도 가능하나, 이미 "Pause"로 루프의 통제력이 입증된 시점에서 테스트 코드를 더 복잡하게 만드는 것은 기술 부채를 늘릴 우려가 있습니다. 인프라 격리(DB isolation)가 해결된 이후에 보강하는 것이 정석입니다.
- **차기 방향 (M37)**: Milestone 37에서는 **SQLite preference store 기본 전환**을 통해 인프라 부채를 해결하거나, **E2E 실행 환경 격리(Test isolation)**를 통해 향후 검증 효율을 높이는 작업을 제안합니다.
