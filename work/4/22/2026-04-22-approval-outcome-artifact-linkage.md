# 2026-04-22 Approval outcome artifact linkage

## 변경 파일
- `core/agent_loop.py`
- `storage/session_store.py`
- `work/4/22/2026-04-22-approval-outcome-artifact-linkage.md`

## 사용 skill
- `approval-flow-audit`: 승인 거절/재발급 흐름이 명시 승인 원칙, pending approval 감사성, overwrite 차단 원칙을 유지하는지 확인했습니다.
- `security-gate`: artifact outcome 기록이 로컬 저장소 내부 기록에 한정되고, 실패 시 승인 흐름을 깨지 않는 guarded 기록인지 확인했습니다.
- `finalize-lite`: handoff 필수 검증과 문서 동기화 필요 여부, closeout 준비 상태를 실제 결과 기준으로 정리했습니다.
- `work-log-closeout`: 구현 라운드의 변경 파일, 검증, 남은 리스크를 Korean `/work` 형식으로 기록했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 782의 exact slice에 따라 content reason note fallback raw string을 seq 779 상수로 마저 치환했습니다.
- 승인 거절과 승인 재발급 outcome이 message/task log뿐 아니라 artifact store에도 남도록 연결했습니다.

## 핵심 변경
- `record_content_reason_note_for_message`의 `content_reason_record.reason_scope` fallback을 `ContentReasonScope.CONTENT_REJECT`로 바꿨습니다.
- `record_content_reason_note_for_message`의 `content_reason_record.reason_label` fallback을 `ContentReasonLabel.EXPLICIT_CONTENT_REJECTION`으로 바꿨습니다.
- `_reissue_pending_approval`에서 task log 기록 직후 `artifact_store.record_outcome(..., outcome="approval_reissued")`를 guarded call로 추가했습니다.
- `_reject_pending_approval`에서 task log 기록 직후 `artifact_store.record_outcome(..., outcome="approval_rejected")`를 guarded call로 추가했습니다.
- `_build_approval_reason_record`의 raw string 값, `record_outcome` 시그니처, session_store/artifact_store public method는 변경하지 않았습니다.

## 검증
- `python3 -m py_compile storage/session_store.py core/agent_loop.py` → 통과
- `python3 -m unittest tests.test_smoke` → 150 tests OK
- `git diff --check -- storage/session_store.py core/agent_loop.py` → 통과

## 남은 리스크
- docs는 handoff constraints가 `storage/session_store.py`와 `core/agent_loop.py`만 허용하므로 이번 slice에서 수정하지 않았습니다.
- artifact outcome 기록은 기존 `try/except Exception: pass` 패턴을 따르므로, artifact store 실패 자체는 사용자 응답에 노출되지 않습니다.
- 시작 시점에 `core/contracts.py`, `storage/session_store.py`, `verify/4/22/2026-04-22-post-cleanup-launcher-automation-realignment.md` 변경과 `report/gemini/2026-04-22-milestone6-reason-label-done-next-scope.md`, `work/4/22/2026-04-22-milestone4-5-bundle-commit-push.md`, `work/4/22/2026-04-22-reason-label-constants.md` untracked 파일이 이미 있었습니다.
- commit/push/PR은 implement lane 금지사항이라 실행하지 않았습니다.
