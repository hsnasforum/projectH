# 2026-04-21 Watcher Turn-State Normalization Arbitration

## 개요
- AXIS-G4, G5, G11, G13, G10 시리즈가 모두 성공적으로 완료되었습니다.
- 현재 verify-lane은 G6 조사, Dispatcher Trace Backfill, G4 E2E 확인을 수행 중입니다.
- 현재 작업 브랜치가 `feat/watcher-turn-state`인 점과 `pipeline_runtime/supervisor.py`에서 이미 완료된 Turn-State 명칭 정규화를 바탕으로, 차기 구현 축을 선정합니다.

## 판단 근거
1. **Current Focus (Branch Context)**: 현재 브랜치가 `feat/watcher-turn-state`로 설정되어 있으며, 이는 Watcher의 상태 관리 로직을 최신 표준에 맞추려는 의도를 나타냅니다.
2. **Technical Integrity (Vocabulary Alignment)**: `WatcherTurnState` Enum에 남아있는 레거시 별칭(CLAUDE_ACTIVE, CODEX_VERIFY 등)은 `pipeline_runtime/turn_arbitration.py`의 정규 명칭과 불일치하며, 내부 코드와 테스트에서 혼용되고 있습니다. 이를 정리하는 것은 시스템의 일관성을 높이는 시급한 "Internal Cleanup" 작업입니다.
3. **Recursive Improvement**: 상태 명칭을 정규화함으로써 향후 Watcher FSM(상태 기구)의 로직을 더 명확하게 만들고, `turn_state.json` 및 런타임 이벤트의 진실성(Truthfulness)을 확보할 수 있습니다.

## 권고 (RECOMMEND)
- **AXIS-G14 (Watcher Turn-State Vocabulary Normalization)**
- **이유**: Watcher 내부의 상태 어휘를 정규화하여 `pipeline_runtime`과의 정합성을 맞추고, 레거시 별칭에 의존하는 기술 부채를 해소합니다.

### 세부 지시 사항
1. **Target Files**: `watcher_core.py`, `tests/test_watcher_core.py`.
2. **Action**:
   - `WatcherTurnState` Enum에서 레거시 별칭(`CLAUDE_ACTIVE`, `CODEX_VERIFY`, `CODEX_FOLLOWUP`, `GEMINI_ADVISORY`)을 제거합니다.
   - `watcher_core.py` 내의 모든 레거시 명칭 참조를 정규 명칭(`IMPLEMENT_ACTIVE`, `VERIFY_ACTIVE`, `VERIFY_FOLLOWUP`, `ADVISORY_ACTIVE`)으로 교체합니다.
   - `tests/test_watcher_core.py`에 산재한 레거시 명칭 참조를 모두 정규 명칭으로 업데이트합니다.
3. **Limit**: 새로운 상태 전이 로직이나 기능을 추가하지 않고, 순수하게 어휘 정규화와 그에 따른 테스트 수정을 목적으로 합니다. (Refactor-only)

## 결론
AXIS-G14를 통해 현재 브랜치의 목표인 Watcher Turn-State 정규화를 완결하고, 시스템 전반의 상태 명칭 정합성을 확보할 것을 권고합니다.
