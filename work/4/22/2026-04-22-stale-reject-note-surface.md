# 2026-04-22 Stale reject-note surface

## 변경 파일
- `storage/session_store.py`
- `app/frontend/src/components/MessageBubble.tsx`
- `work/4/22/2026-04-22-stale-reject-note-surface.md`

## 사용 skill
- `approval-flow-audit`: save-completion과 correction 전환이 명시 승인 저장 흐름을 우회하지 않고 기존 session message 기록만 정리하는지 확인했습니다.
- `security-gate`: reject note가 로컬 session 기록에만 저장되고, stale clear가 저장 파일/승인 기록을 직접 변경하지 않는지 확인했습니다.
- `finalize-lite`: handoff 필수 검증, 문서 동기화 제한, closeout 준비 상태를 실제 결과 기준으로 정리했습니다.
- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 검증, 남은 리스크를 Korean `/work` 형식으로 기록했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 789의 exact slice에 따라 `rejected` outcome을 supersede하는 correction/save 완료 시 `content_reason_record`가 stale 상태로 남지 않게 했습니다.
- `content_verdict === "rejected"` 동안 사용자가 기존 거절 이유를 볼 수 있고 blur 시 업데이트할 수 있는 persistent inline note surface를 추가했습니다.

## 핵심 변경
- `record_correction_for_message`에서 correction 제출 후 `candidate_*` 기록과 함께 `content_reason_record`를 제거합니다.
- `record_corrected_outcome_for_artifact`에서 `stored_outcome == "accepted_as_is"`인 save-completion 전환 시 `content_reason_record`를 제거합니다.
- `MessageBubble`의 hover-only `거절됨` static indicator를 메시지 본문 안의 persistent rejected block으로 옮겼습니다.
- rejected block에 `content_reason_record.reason_note` 기반 `defaultValue` / `key` textarea를 추가하고, blur 시 non-empty note만 `onContentReasonNote`로 저장하게 했습니다.
- 기존 initial reject popup의 `showRejectNote`, confirm/cancel, reject button 흐름은 변경하지 않았습니다.

## 검증
- `python3 -m py_compile storage/session_store.py` → 통과
- `python3 -m unittest tests.test_smoke` → 150 tests OK
- `git diff --check -- storage/session_store.py app/frontend/src/components/MessageBubble.tsx` → 통과

## 남은 리스크
- frontend TypeScript build는 handoff 필수 검증에 없어서 실행하지 않았습니다.
- docs는 이번 handoff가 `storage/session_store.py`와 `MessageBubble.tsx`만 허용하므로 수정하지 않았습니다.
- 시작 시점에 `work/4/22/2026-04-22-milestone6-axis1-bundle-commit-push.md`가 이미 untracked 상태였습니다.
- commit/push/PR은 implement lane 금지사항이라 실행하지 않았습니다.
