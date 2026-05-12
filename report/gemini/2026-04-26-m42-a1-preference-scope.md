# Advisory Log: 2026-04-26-m42-a1-preference-scope

## 요약
M42 Axis 1(Preference Activation) 진입 전, 구현 범위와 선행 작업(watcher_core cleanup)의 우선순위를 결정했습니다. `A1-β` (Status 전환 + Filtered List UI)를 첫 번째 구현 슬라이스로 권장하며, 기술적 부채 해결을 위해 `watcher_core` re-export 정규화를 A1 작업 전에 먼저 처리할 것을 권고합니다.

## 분석 및 판단
1. **구현 범위 (A1-β 권장):**
   - `A1-α`(API만)는 사용자 가시성이 부족하고, `A1-γ`(Prompt Injection)는 데이터/UI 계층의 안정성이 확보되지 않은 상태에서 동작 변화를 유도하므로 리스크가 큽니다.
   - `A1-β`는 사용자가 preference를 '활성' 상태로 관리하고 이를 UI에서 확인할 수 있게 함으로써 M41의 감사(Audit) 기능을 '관리(Management)' 기능으로 확장하는 완결성 있는 슬라이스입니다.
2. **Same-session Prompt Injection (A1-γ) 안전성:**
   - 기술적으로 local-first approval-based 경계 내에 있으나, auditability(감사 가능성) 확보를 위해 별도 Axis(M42 Axis 2 등)로 분리하여 진행하는 것이 타당합니다.
3. **Internal Cleanup (watcher_core):**
   - `GEMINI.md` 우선순위 4(Internal Cleanup)에 해당하지만, 차기 기능 구현 시 테스트 mock 및 import 구조를 깔끔하게 유지하기 위해 선행 처리하는 것이 효율적입니다.

## 권고 사항
- **우선순위 1 (Immediate):** `watcher_core` re-export 정규화 (Internal Cleanup). 별도 advisory 없이 bounded implement로 진행.
- **우선순위 2 (M42 Axis 1):** `Option A1-β` (Status 전환 API + Filtered List 조회 및 UI 확장).
- **우선순위 3 (Future):** `Option A1-γ` (Same-session Prompt Injection). Axis 1 완료 후 audit log 및 activation 안정성 확인 후 진행.

## Exact Slice 권고
- **TASK 1:** Clean up `watcher_core` re-exports and normalize imports in related tests.
- **TASK 2 (A1-β):**
  - `POST /api/preferences/<id>/activate` (and `pause`) endpoints.
  - Update `list_preferences_payload` to support status filtering.
  - UI: Add 'Activate/Pause' buttons to `PreferencePanel` and show status labels/badges.
