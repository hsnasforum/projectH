# 2026-04-23 Milestone 22 Scope Definition

## Summary

Milestone 21에서 완료된 SQLite 기반 교정 라이프사이클 및 전역 거절(Global Reject) 기능의 무결성을 최종 확보하기 위해 **Option A (Correction Lifecycle Integrity)**를 마일스톤 22의 범위로 선택합니다.

## Milestone 22 Axes

### Axis 1: Lifecycle State Guard
- `SQLiteCorrectionStore._transition()` 내부에 상태 전이 규칙 검증 로직을 구현합니다.
- `CANDIDATE -> CONFIRMED -> PROMOTED -> ACTIVE` 등 정의된 순서를 벗어난 전이 시도를 차단하여 데이터 일관성을 보장합니다.

### Axis 2: Global Reject Smoke Test
- 전역 후보 거절 후 세션을 재시작하거나 다른 세션에 진입했을 때 해당 지문(fingerprint)의 후보가 다시 노출되지 않는지 확인하는 Playwright 테스트를 추가합니다.
- M21 Axis 2의 브라우저 가시성 및 영구성 누락분을 보완합니다.

### Axis 3: Release Gate
- 모든 기능 구현 및 테스트 추가 후 전체 스모크 테스트(`make e2e-test`)를 통해 회귀 여부를 확인합니다.

## Decision Rationale
- M21에서 급격히 진행된 SQLite 라이프사이클 전환의 내부 로직을 공고히 하고, 사용자에게 직접적인 영향을 미치는 전역 거절 기능의 "영구성"을 실질적으로 검증하는 것이 가장 시급한 과제입니다.
- 테스트 격리(Option B)는 장기적인 안정성에 기여하나, 현재는 기능의 정확성과 무결성(Integrity)을 우선순위에 둡니다.
