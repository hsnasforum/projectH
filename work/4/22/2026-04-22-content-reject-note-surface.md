# 2026-04-22 content reject note surface

## 변경 파일
- `app/frontend/src/api/client.ts`
- `app/frontend/src/types.ts`
- `app/frontend/src/components/MessageBubble.tsx`
- `work/4/22/2026-04-22-content-reject-note-surface.md`

## 사용 skill
- `security-gate`: content verdict와 reason note가 session-local feedback 기록 표면이며 승인/write/storage 경계를 새로 넓히지 않는지 확인했습니다.
- `doc-sync`: UI behavior와 타입 표면 변경에 따른 문서 동기화 필요성을 점검했으며, 이번 handoff 제약상 docs는 수정하지 않았습니다.
- `finalize-lite`: 구현 종료 전 실행한 검증과 남은 리스크를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 774의 exact slice에 따라 React `MessageBubble`에 좁은 `내용 거절` 입력 표면과 optional free-text note 표면을 추가했습니다.
- Milestone 5의 "still later" 범위에 맞춰 label dropdown, multi-select, multi-verdict 확장은 추가하지 않았습니다.

## 핵심 변경
- `client.ts`에 `postContentVerdict()`와 `postContentReasonNote()` API helper를 추가했습니다.
- `types.ts`에 `ContentReasonRecord`를 추가하고 `Message`에 `content_verdict`, `content_reason_record` optional field를 추가했습니다.
- `MessageBubble.tsx`에 optional `onContentVerdict`, `onContentReasonNote` props와 reject-note local state를 추가했습니다.
- assistant message hover action 영역에 `내용 거절` 버튼, optional note textarea, `거절됨` indicator를 추가했습니다.
- `onContentVerdict` prop이 없으면 새 UI가 렌더링되지 않도록 유지했고, non-empty note가 있을 때만 `onContentReasonNote`를 호출하게 했습니다.

## 검증
- `python3 -m unittest tests.test_smoke` 통과 (`150 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 라운드는 commit/push/PR을 수행하지 않았습니다.
- handoff 제약에 따라 docs, backend, storage, pipeline control 파일은 수정하지 않았습니다.
- parent call site 연결은 이번 handoff에서 금지되어 있어 `MessageBubble`의 새 content reject UI는 `onContentVerdict` prop이 전달되는 경로에서만 표시됩니다.
- TypeScript/frontend build는 handoff 필수 검증에 포함되지 않아 실행하지 않았습니다.
- 작업 시작 전부터 선행 라운드의 dirty tree가 남아 있어 전체 diff/status에는 이번 변경 외 파일들이 함께 보입니다.
