# 2026-04-25 M31-direction-release-gate-bundle

## 결정: 후보 B (PR #33 Release Gate 및 통합 검증 우선)

### 근거
1. **리스크 감소 (GEMINI.md 우선순위 1)**: M28(구조 번들), M29(루프 개선), M30(Watcher 분해)에 걸친 대규모 변경사항(seq 115–146)이 아직 단일 PR(#33)에 묶여 unmerged 상태로 쌓여 있습니다. 특히 `watcher_core.py`의 구조적 변경이 브라우저 쉘(E2E)이나 컨트롤러 통합에 미치는 영향을 전체적으로 검증하는 것이 최우선입니다.
2. **Untracked 상태 해소**: 현재 `controller/monitor.py` 및 관련 테스트가 구현 완료되었으나 untracked 상태입니다. 이를 별도의 슬라이스로 분리하기보다, 현재 번들에 포함하여 함께 검증하고 커밋하는 것이 구조적 정합성에 맞습니다.
3. **진실성 유지**: PR #33의 제목과 설명이 M28 상태에 머물러 있어 현재 코드 상태와 괴리가 큽니다. 이를 M30 수준으로 동기화하여 협업 및 검토 효율을 높입니다.

### 권고 Slice
- **목표**: M28–M30 통합 번들 검증 및 Release Gate 통과.
- **실행 항목**:
    - `make e2e-test` (143개 시나리오)를 통해 Watcher core 변경 후 브라우저 회귀 여부 확인.
    - `controller/monitor.py` 및 `tests/test_controller_monitor.py`를 git에 추가 및 커밋 (현재 4 tests PASS 상태).
    - PR #33 (feat/watcher-turn-state)의 제목과 설명을 M30 완료 기준으로 갱신 (FSM single-owner, loop bridge, core decomposition 포함).
- **검증**: 전체 E2E 및 unittest(202+10+4) 통과 확인.

### 제외된 후보
- **후보 A (Monitor 우선)**: 독립 슬라이스로 처리할 수 있으나, 이미 구현된 파일을 번들 검증 단계에서 함께 커밋하는 것이 효율적입니다.
- **후보 C (M31 기능 바로 시작)**: 대규모 unmerged 번들의 리스크를 안고 새로운 기능(smoke test나 SQLite 기본 전환)을 추가하는 것은 기술 부채를 가중시킵니다. "Verification First" 원칙에 따라 검증을 먼저 수행합니다.

### 차기 Milestone (M31) 예고
Release Gate 통과 후, **C1(Reviewed-memory loop smoke test)**을 통해 기능적 완성도를 다지거나 **C2(SQLite default)**를 통해 인프라 부채를 해결하는 방향으로 Milestone 31을 시작할 것을 권고합니다.
