# 2026-04-25 M35-release-gate-and-m36-direction

## 결정: 후보 A (M35 Bundle Release Gate 및 신규 PR 생성)

### 근거
1. **리스크 감소 (GEMINI.md 우선순위 1)**: M35(인터랙티브 뱃지 및 인라인 편집) 작업이 성공적으로 완료되었으며, 148개 E2E 테스트 통과가 확인되었습니다. PR #33이 이미 머지된 상태에서 새로운 기능 단위(M35)를 신속하게 `main`에 통합하여 브랜치 생명주기를 짧게 유지하는 것이 리스크 관리 측면에서 가장 유리합니다.
2. **진실성 유지**: 현재 `feat/watcher-turn-state` 브랜치는 PR #33 이후의 추가 변경사항을 포함하고 있습니다. 이를 별도의 PR로 분리하여 코드 리뷰와 머지 단위를 명확히 합니다.
3. **가이드라인 준수**: `GEMINI.md`의 "same-family current-risk reduction"을 따릅니다. unmerged 상태의 코드를 줄이고 배포 가능한 상태를 유지합니다.

### 권고 Slice (M36 Axis 1 예고)
- **M35 종료**: 이번 라운드에서 전체 `make e2e-test` 게이트를 통과한 후, M35 전용 신규 PR을 생성하여 머지 게이트에 진입합니다.
- **M36 (차기 Milestone)**: **SQLite preference store 기본 전환 (Default Rollout)**. 구조 분리와 UX 개선이 일단락되었으므로, 오랫동안 미뤄온 인프라 부채를 해결하여 시스템의 견고함을 확보할 것을 제안합니다.

### 실행 범위 (M35 Axis 3 — Release Gate)
- **목표**: M35 누적 변경사항 최종 검증 및 PR 생성 준비.
- **실행 항목**:
    1. `make e2e-test`를 통해 148개 시나리오 전수 PASS 최종 확인.
    2. `docs/MILESTONES.md`에 M34(가시성 복원) 및 M35(인터랙티브 관리) 완료 내역 동기화.
    3. M35 기능(Interactive Applied Preference Management)을 명확히 설명하는 신규 PR 생성.
- **검증**: 148 E2E + 229 unit tests PASS 및 문서 정합성 확인.

### 후보 검토
- **후보 B (추가 기능)**: 새로운 기능을 시작하기 전에 현재의 안정적인 상태를 `main`에 반영하는 "Release Gate" 절차가 "Verification First" 원칙에 더 부합합니다.
