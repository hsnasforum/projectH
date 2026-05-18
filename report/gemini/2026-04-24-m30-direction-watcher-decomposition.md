# 2026-04-24 m30-direction-watcher-decomposition

## 결정: 후보 3 (watcher_core.py 구조 분리)

### 근거
1. **구조적 정렬**: M29 루프(Axis 1-3)가 144개 e2e 패스와 함께 기능적으로 완료되었습니다. 현재 시점은 "기능 충분, 구조 미흡" 단계로 판단되며, `watcher_core.py`의 비대한 책임을 분산하는 것이 최우선입니다.
2. **이전 권고(SEQ 126) 계승**: 이전 Advisory SEQ 126에서 제안된 "opportunistic small structural slices"와 일치하며, 이는 향후 "4축 owner bundle" 작업을 위한 필수적인 선행 단계입니다.
3. **유지보수 리스크 감소**: `GEMINI.md`의 원칙에 따라 단일 파일에 책임을 몰아넣는 구조를 개선하여 owning boundary를 명확히 합니다.

### 권고 Slice
- `watcher_core.py`를 책임 단위(parsing, labeling, control-writing, lane-surface)로 분리하는 opportunistic bounded slice 구현.

### 제외된 후보
- **후보 1 (smoke test)**: 기능 검증 보강도 중요하나, 현재 구조적 결합도가 높아지는 리스크가 더 크다고 판단했습니다.
- **후보 2 (SQLite store 전환)**: `TASK_BACKLOG`에서 명시적으로 deferred로 분류되었으므로 현 시점에서는 제외합니다.
