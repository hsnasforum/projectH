# 2026-04-22 Milestone 6 Axis 3 Scoping

## Arbitration Context
- **Axis 2 (stale clear + persistent reject-note UX)** 구현(seq 789)이 완료되었으며, `python3 -m unittest tests.test_smoke` 150개 테스트를 통해 검증되었습니다.
- **Operator Request 792**는 seq 789의 커밋 및 푸시 승인을 요청했으나, `GEMINI.md`의 `commit_push_bundle_authorization + internal_only` 정책에 따라 verify/handoff owner가 직접 후속 조치를 취할 수 있는 범위로 판단됩니다.
- 현재 verify/handoff owner가 operator retriage 도중 유휴 상태(idle)가 되었으므로, 이를 해결하기 위해 Axis 3 진행을 권고합니다.

## RECOMMEND: implement Milestone 6 Axis 3 (Richer Scoped Reason Records)
- Axis 2 번들(seq 789)을 `internal_only` 정책에 따라 커밋/푸시한 후, 즉시 Axis 3 구현에 착수할 것을 권장합니다.
- **Axis 3 핵심 목표:** 사용자가 내용 거절 시 단순히 노트만 남기는 것이 아니라, 정해진 레이블(fact_error, tone_error, missing_info 등)을 선택할 수 있게 하여 피드백의 구조화 수준을 높입니다.

## Implementation Details
1. **Core Contracts:**
   - `core/contracts.py`의 `ContentReasonLabel`에 `fact_error`, `tone_error`, `missing_info`를 추가합니다.
   - `ALLOWED_CONTENT_REASON_LABELS`를 업데이트하여 해당 레이블들이 `CONTENT_REJECT` 스코프에서 허용되도록 합니다.
2. **Frontend UI:**
   - `app/frontend/src/components/MessageBubble.tsx`의 내용 거절 영역(`persistent rejected block`)에 레이블 선택 UI(칩 또는 드롭다운)를 추가합니다.
   - 선택된 레이블이 `onContentReasonNote` 저장 시 함께 전달되거나, 레이블 전용 API 핸들러가 필요할 경우 `api/client.ts`와 연동합니다.

## Decision Rationale
- Axis 2의 성과(stale clear)를 조기에 커밋하여 작업 트리를 정리하는 것이 이후 Axis 3의 복잡한 UI 변경을 관리하기에 안전합니다.
- Milestone 6의 "define shared reason fields" 목표를 달성하기 위해 풍부한 레이블 세트 확보가 필수적입니다.
- 추가적인 operator 개입 없이 자동화discuss로 exact slice를 확정할 수 있는 시점입니다.
