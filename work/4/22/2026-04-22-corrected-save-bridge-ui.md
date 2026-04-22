# 2026-04-22 Corrected-save bridge UI

## 변경 파일
- `core/agent_loop.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/MessageBubble.tsx`
- `app/frontend/src/components/ChatArea.tsx`
- `app/frontend/src/App.tsx`
- `work/4/22/2026-04-22-corrected-save-bridge-ui.md`

## 사용 skill
- `approval-flow-audit`: corrected-save bridge가 새 저장을 즉시 실행하지 않고 기존 approval 요청 경로로 들어가는지 확인했습니다.
- `security-gate`: 새 frontend action이 `/api/chat`의 approval-gated request만 만들며 로컬 저장 승인 경계를 우회하지 않는지 확인했습니다.
- `finalize-lite`: 필수 검증 결과, 문서 동기화 제한, closeout 준비 상태를 실제 실행 결과 기준으로 정리했습니다.
- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 검증, 남은 리스크를 Korean `/work` 형식으로 기록했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 785의 exact slice에 따라 approval reason raw string을 seq 779 enum constant로 치환했습니다.
- React에서 corrected-save bridge를 호출할 수 있도록 `수정본 저장` 버튼과 `corrected_save_message_id` payload 전송 경로를 연결했습니다.

## 핵심 변경
- `_reissue_pending_approval`의 `reason_scope` / `reason_label`을 `ApprovalReasonScope.APPROVAL_REISSUE`, `ApprovalReasonLabel.CORRECTED_TEXT_REISSUE`, `ApprovalReasonLabel.PATH_CHANGE`로 치환했습니다.
- `_reject_pending_approval`의 approval reject reason을 `ApprovalReasonScope.APPROVAL_REJECT`, `ApprovalReasonLabel.EXPLICIT_REJECTION`으로 치환했습니다.
- `postCorrectedSave(sessionId, messageId)`를 추가해 `/api/chat`에 `corrected_save_message_id`를 보냅니다.
- `MessageBubble`에 `onCorrectedSave` prop과 `수정본 저장` 버튼을 추가했습니다. 버튼은 assistant message에서 항상 보이고, `message.corrected_text`가 없으면 disabled 상태로 남습니다.
- `ChatArea`와 `App`에 `onCorrectedSave` passthrough와 handler를 연결했습니다. streaming bubble에는 새 prop을 전달하지 않았습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py` → 통과
- `python3 -m unittest tests.test_smoke` → 150 tests OK
- `git diff --check -- core/agent_loop.py app/frontend/src/api/client.ts app/frontend/src/components/MessageBubble.tsx app/frontend/src/components/ChatArea.tsx app/frontend/src/App.tsx` → 통과

## 남은 리스크
- frontend TypeScript build는 handoff 필수 검증에 없고, `app/frontend/src/hooks/useChat.ts`의 기존 TypeScript 오류가 명시된 범위 밖이라 실행하지 않았습니다.
- docs는 이번 handoff가 다섯 구현 파일만 허용하므로 수정하지 않았습니다.
- 시작 시점에 `core/agent_loop.py`, `core/contracts.py`, `storage/session_store.py`, `verify/4/22/2026-04-22-post-cleanup-launcher-automation-realignment.md` 변경과 `report/gemini/2026-04-22-milestone6-axis1-done-next-scope.md`, `report/gemini/2026-04-22-milestone6-reason-label-done-next-scope.md`, 기존 `/work` untracked 파일들이 이미 있었습니다.
- commit/push/PR은 implement lane 금지사항이라 실행하지 않았습니다.
