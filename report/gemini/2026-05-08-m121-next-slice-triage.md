# 2026-05-08 M121 완료 및 차기 슬라이스 선정 (M122) — Advisory

## Status
- **M121 (Watcher lease reclamation)**: 완료 (PR #117 merged)
- **Document Truth**: `MILESTONES.md`, `TASK_BACKLOG.md` 내 M121 완료 기록 완료. 단, `Next 3 Implementation Priorities` 섹션은 handoff 금지 범위 문제로 인해 stale 상태 (PR #91-111 대기 중으로 표시됨).
- **Next Slice**: M122 "Improve entity-card web investigation quality" 진입 필요.

## Recommendation

### 1. RECOMMEND: implement doc-sync (Implementation Priorities reconciliation)
- **목표**: `MILESTONES.md` 및 `TASK_BACKLOG.md`의 `Next 3 Implementation Priorities` 섹션을 최신 상태로 동기화.
- **근거**: M121이 완료되고 이전 PR 백로그가 해소되었음에도 문서상에는 여전히 대기 중으로 표시되어 truth gap 발생.
- **변경 내용**:
    - PR #91-111 및 M117-M121 완료 반영.
    - 새로운 우선순위 설정:
        1. **M122 Axis 1**: Improve entity-card investigation quality (multi-source agreement)
        2. **E2E Gap**: M47/M48 A2 headers coverage
        3. **Stability**: Supervisor/Watcher lease behavior monitoring

### 2. RECOMMEND: implement M122 Axis 1 (Multi-source agreement priority)
- **목표**: 웹 조사 결과 요약 시 단일 출처의 노이즈보다 다수 출처의 합의된 정보를 우선하도록 로직 개선.
- **근거**: `TASK_BACKLOG.md`의 "Current Phase In Progress" 1, 2번 항목과 일치.

## Decision Rationale
- **Truth Gap Reduction**: `doc-sync`를 통해 현재 실행 엔진(watcher/supervisor)과 문서 기록 간의 불일치를 먼저 해소하는 것이 안전한 진행을 위해 필수적임.
- **Exact Slice**: broad한 "Investigation Quality" 개선을 M122로 정의하고, "Multi-source agreement"라는 구체적인 기술 슬라이스로 좁혀 진행함.

## Stop Rule
- `doc-sync` 중 `Next 3 Implementation Priorities` 외의 다른 섹션(Do Not Pull Forward 등)을 수정할 경우 중단.
- M122 Axis 1 구현 중 기존 document-flow 요약 품질이 저하될 경우 중단.
