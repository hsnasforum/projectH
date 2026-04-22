# 2026-04-22 content reject parent wire-up

## 변경 파일
- `app/frontend/src/components/ChatArea.tsx`
- `app/frontend/src/App.tsx`
- `work/4/22/2026-04-22-content-reject-parent-wire-up.md`

## 사용 skill
- `security-gate`: content verdict와 reason note 호출이 기존 backend 기록 경로를 호출하는 frontend 연결이며 승인/write/storage 경계를 새로 넓히지 않는지 확인했습니다.
- `doc-sync`: UI behavior 변경에 따른 문서 동기화 필요성을 점검했으며, 이번 handoff 제약상 docs는 수정하지 않았습니다.
- `finalize-lite`: 구현 종료 전 실행한 검증과 남은 리스크를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 775의 exact slice에 따라 seq 774에서 추가된 `MessageBubble`의 `onContentVerdict` / `onContentReasonNote` props를 parent call chain에 연결했습니다.
- `내용 거절` 버튼이 실제 backend route를 호출할 수 있도록 `App handler → ChatArea passthrough → MessageBubble` 경로를 닫았습니다.

## 핵심 변경
- `ChatArea.tsx` props에 `onContentVerdict`, `onContentReasonNote`를 추가하고 일반 메시지 `MessageBubble`에 전달했습니다.
- streaming bubble에는 handoff 제약대로 content verdict/reason-note props를 전달하지 않았습니다.
- `App.tsx`에서 `postContentVerdict`, `postContentReasonNote`를 import하고 `handleContentVerdict`, `handleContentReasonNote` callback을 추가했습니다.
- content verdict 성공 시 현재 session을 reload하고, 실패 시 한국어 error toast를 표시하도록 했습니다.
- content reason note 실패 시 별도 한국어 error toast를 표시하도록 했습니다.

## 검증
- `python3 -m unittest tests.test_smoke` 통과 (`150 tests`)
- `git diff --check -- app/frontend/src/components/ChatArea.tsx app/frontend/src/App.tsx` 통과

## 남은 리스크
- 이번 라운드는 commit/push/PR을 수행하지 않았습니다.
- handoff 제약에 따라 `MessageBubble.tsx`, `api/client.ts`, `types.ts`, backend, docs, pipeline control 파일은 수정하지 않았습니다.
- TypeScript/frontend build는 handoff 필수 검증에 포함되지 않아 실행하지 않았습니다.
- 작업 시작 전부터 선행 라운드의 dirty tree가 남아 있어 전체 diff/status에는 이번 변경 외 파일들이 함께 보입니다.
