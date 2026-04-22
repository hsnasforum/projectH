# 2026-04-22 milestone4-closed-milestone5-scope

## 개요
CONTROL_SEQ 771(Source Role Tooltip)을 통해 Milestone 4 "Secondary-Mode Investigation Hardening"이 최종 완료되었습니다. 이에 따라 (1) 오늘 수행된 대규모 로직/UI 작업의 커밋 타이밍과 (2) 차기 단계인 Milestone 5 "Grounded Brief Contract"의 첫 구현 슬라이스를 중재합니다.

## 중재 결과

### Q1 — Commit/push timing and scope
**RECOMMEND: commit_push_now_bundle**
오늘 완료된 Seqs 756~771(내부 필드, 유닛 테스트, 재조사 정렬, AgentLoop 동기화, UI 툴팁)을 하나의 큰 "Investigation Quality Final Bundle"로 묶어 커밋 및 푸시할 것을 권고합니다. 이 번들은 Milestone 4의 모든 목표를 달성한 상태이며, 로직과 UI가 상호 검증된 안정적인 상태이므로 `feat/watcher-turn-state` 브랜치에 더 이상의 미커밋 작업을 누적하지 않고 닫는 것이 적절합니다.

### Q2 — First Milestone 5 non-implemented sub-item
**NEXT SLICE: Optional Reject-Note Surface (React UI Port)**
Milestone 5의 백엔드 기반과 "Recently Landed Memory Foundation"(#1-9)은 이미 확보되었으나, 레거시 앱(`index.html`)에 존재하는 "내용 거절(Content Verdict)" 및 "거절 메모(Reject Note)" 기능이 React 프론트엔드에는 아직 구현되지 않았습니다. 이는 Milestone 5의 "still later" 항목이자 Milestone 6의 "fix truthful contract"를 위한 필수 전제 조건입니다.

- **Exact Sub-bullet:** `docs/MILESTONES.md` Milestone 5 "keep the first optional reject-note surface narrow..." 및 `docs/TASK_BACKLOG.md` NextToAdd #2 ("More optional reject-note records...").
- **Entry Points:**
    - `app/frontend/src/api/client.ts` (line 70 부근): `postContentVerdict`, `postContentReasonNote` API 호출 추가
    - `app/frontend/src/types.ts` (line 25 부근): `Message` 인터페이스에 `content_reason_record` 필드 추가
    - `app/frontend/src/components/MessageBubble.tsx` (line 220 부근): "내용 거절" 버튼 및 거절 사유 입력을 위한 textarea UI 구현
- **Constraint:** Milestone 6의 "Richer reason labels" 확장을 시도하기 전에, 먼저 이 "진실된 사용자 입력 인터페이스(truthful user-input surface)"가 React 앱에 안착되어야 합니다 (`TASK_BACKLOG.md` #35 제약).

## 권고 요약
1. Seqs 756~771 전체 작업을 하나의 번들로 커밋 및 푸시하여 Milestone 4를 종료합니다.
2. 다음 슬라이스로 React 앱에 "내용 거절" 버튼과 "거절 메모" 입력 UI를 구현하여 Milestone 5의 UI 공백을 메웁니다.
3. 이후 확보된 UI를 바탕으로 Milestone 6의 풍부한 사유 라벨(Richer Labels) 시스템으로 확장합니다.
