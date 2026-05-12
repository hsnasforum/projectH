# Advisory Log: 2026-04-26-m42-bundle-strategy-and-operator-integrity

## 요약
완료된 3개 라운드(watcher cleanup, auth boundary, shared resolver)의 커밋 전략을 확정하고, 차기 슬라이스인 M42 A1-β(Preference Activation) 진입을 승인합니다. 운영자 통제 경계가 shared resolver로 단일화됨에 따라 시스템 안정성이 확보되었으며, 이제 사용자 가시성이 있는 기능 확장으로 전환합니다.

## 분석 및 판단
1. **커밋 전략 (안 A 승인):**
   - **Commit A1 (Watcher Structural Integrity):** `watcher_core.py`와 `tests/test_watcher_core.py`의 re-export 정리 및 resolver 연결을 포함합니다. Watcher 레이어의 내부 구조 개선을 하나의 논리적 단위로 묶습니다.
   - **Commit A2 (Operator Control Integrity):** `pipeline_runtime/`, `README.md`, 그리고 관련 테스트와 M36 verify note를 포함합니다. 이는 시스템 전반의 운영자 통제 로직 강화와 문서화를 담당합니다.
   - **Draft PR #35 활용:** 동일 브랜치(`feat/watcher-turn-state`)에 push하여 PR을 확장하는 것이 audit trail 유지에 적합합니다.

2. **M42 A1-β 슬라이스 적합성:**
   - Shared resolver 아키텍처 도입으로 `needs_operator` 판정 로직이 supervisor와 watcher 간에 동기화되었습니다. 이는 preference 상태 변경(activate/pause) 시 발생할 수 있는 운영자 개입 상황을 더 정확하게 처리할 수 있는 기반이 됩니다.
   - 따라서 advisory 250의 권고인 `A1-β` (Status 전환 API + Filtered List UI)는 여전히 가장 적합한 다음 단계입니다.

3. **MILESTONES.md 업데이트:**
   - 현재 "다음 advisory에서 확정"으로 되어 있는 부분을 A1-β 슬라이스로 공식 기록하여 프로젝트의 진실의 원천(Truth)을 동기화해야 합니다.

## 권고 사항
- **RECOMMEND: bundle commit via Option A and proceed to M42 A1-β.**
- **Commit A1:** watcher_core (re-export cleanup + resolver usage integration).
- **Commit A2:** pipeline_runtime, tests, README, and M36 verify note update.
- **Next Slice:** M42 A1-β 구현 진입.
  - 첫 단계로 `docs/MILESTONES.md`에 M42 Axis 1 슬라이스를 공식 기록할 것.
  - 이후 `POST /api/preferences/<id>/activate` / `pause` 및 UI 확장을 진행.

## Exact Slice 권고
- **TASK 1:** Commit the current 3-round bundle using Option A (A1: Watcher, A2: Runtime/Tests/Docs).
- **TASK 2:** Update `docs/MILESTONES.md` to define M42 Axis 1 as A1-β.
- **TASK 3 (A1-β):** Implement preference status transition APIs and UI filtering/badges in `PreferencePanel`.
