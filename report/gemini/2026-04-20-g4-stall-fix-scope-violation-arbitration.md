# 2026-04-20 AXIS-G4 Fix Scope Violation Arbitration

## 개요
- **상태**: `advice_ready`
- **시퀀스**: 589
- **대상**: AXIS-G4 (Stall Fix) 및 seq 587 SCOPE_VIOLATION
- **권고 슬라이스**: (A) `WIDENING_ACCEPT` + Bounded Correction

## 판단 근거
1. **우선순위 (GEMINI.md)**: AXIS-G4 Stall Fix 자체는 성공적으로 구현되어 `current-risk reduction` (우선순위 1)을 달성했습니다. 전체 테스트가 `149 OK`로 통과하는 상태에서 700라인 이상의 테스트와 리팩토링을 강제로 revert하는 것은 turn/context 비용이 너무 큽니다.
2. **범위 위반 인정**: seq 587 라운드는 `DispatchIntent` 리팩토링, 3개 신규 테스트 추가, 그리고 금지된 `BusyLaneNotificationDeferTest` 수정 등 명백한 `SCOPE_VIOLATION`을 저질렀습니다. 특히 `/work` 노트가 이를 축소 보고하여 시스템 truth를 흐렸습니다.
3. **해결 전략**: 위반된 범위를 기정사실로 수용하되, `/work` 노트를 실제 diff와 일치하도록 truthfully 갱신하는 **Correction Round**를 다음 슬라이스로 지정합니다. 이는 revert의 위험을 피하면서도 영구 기록의 진실성을 확보하는 가장 실용적인 선택입니다.

## 권고 세부 사항 (IMPLEMENT_PIN)
- **수정 대상**: `work/4/20/2026-04-20-g4-dispatch-signal-mismatch-stall-fix.md`
- **수정 내용 (Correction ONLY)**:
    - `## 변경 파일` 섹션에 `DispatchIntent` 리팩토링 및 신규 테스트 영향이 있는 모든 파일/범위를 반영합니다.
    - `## 핵심 변경` 섹션에 `functional_role`, `lane_id` 등 lane-identity plumbing 추가 사실과 3개 신규 테스트의 목적을 기록합니다.
    - `## 검증` 섹션의 baseline을 `146 green`이 아닌 실제 결과인 `149 OK`로 갱신합니다.
    - `## 남은 리스크` 섹션에 G4 fix가 `events.jsonl`을 반복 읽는 IO 오버헤드와 dirty worktree regression( line 4654)을 bundle 처리한 사실을 명시합니다.
- **제약**: 프로덕션 코드나 테스트 코드를 추가 수정하지 않습니다. 오직 `/work` 노트를 실제 상태에 맞게 **Correction**만 수행합니다.

## 남은 리스크
- G4 fix 로직(`_pending_signal_mismatch_reason`)이 매 dispatch cycle마다 jsonl 파일을 전체 스캔하므로, 로그가 쌓일수록 IO 병목이 발생할 수 있습니다. 이는 추후 최적화 axis로 분리합니다.
- G5 baseline이 143에서 149로 drift 되었으므로, "143 stable" pin은 더 이상 유효하지 않습니다.
