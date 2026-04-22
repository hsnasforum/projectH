# 2026-04-22 Reason label constants

## 변경 파일
- `core/contracts.py`
- `storage/session_store.py`
- `work/4/22/2026-04-22-reason-label-constants.md`

## 사용 skill
- `approval-flow-audit`: approval/content reason label contract가 기존 승인·거절 추적 불변식을 깨지 않는지 확인했습니다.
- `security-gate`: session 저장 기록의 로컬 감사 경계와 approval-gated write 원칙이 바뀌지 않았는지 확인했습니다.
- `finalize-lite`: 실행한 검증, 문서 동기화 필요 여부, closeout 준비 상태를 실제 결과 기준으로 정리했습니다.
- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 검증, 남은 리스크를 Korean `/work` 형식으로 기록했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 779의 exact slice에 따라 approval/content reason label 문자열 계약을 `core/contracts.py`의 enum 상수 패턴으로 정리했습니다.
- 이번 변경은 문자열 값을 바꾸지 않고 raw literal을 enum constant 참조로 치환하는 refactor입니다.

## 핵심 변경
- `ApprovalReasonLabel`을 추가해 기존 `explicit_rejection`, `path_change`, `corrected_text_reissue` 값을 상수화했습니다.
- `ALLOWED_APPROVAL_REASON_LABELS`가 새 `ApprovalReasonLabel` 값을 사용하도록 바꿨습니다.
- `ContentReasonLabel`을 추가해 기존 `explicit_content_rejection` 값을 상수화했습니다.
- `ALLOWED_CONTENT_REASON_LABELS`가 새 `ContentReasonLabel` 값을 사용하도록 바꿨습니다.
- `record_rejected_content_verdict_for_message`의 `content_reason_record.reason_scope` / `reason_label` 기록이 `ContentReasonScope.CONTENT_REJECT`와 `ContentReasonLabel.EXPLICIT_CONTENT_REJECTION`을 사용하도록 바꿨습니다.
- write 승인 조건, overwrite 정책, pending approval 저장 구조, 라벨 문자열 값은 변경하지 않았습니다.

## 검증
- `python3 -m py_compile core/contracts.py storage/session_store.py` → 통과
- `python3 -m unittest tests.test_smoke` → 150 tests OK
- `git diff --check -- core/contracts.py storage/session_store.py` → 통과

## 남은 리스크
- docs는 값과 사용자-visible 동작이 그대로라 이번 handoff 범위에서 수정하지 않았습니다.
- test file 추가/수정은 없으며, 기존 smoke baseline으로 회귀만 확인했습니다.
- commit/push/PR은 implement lane 금지사항이라 실행하지 않았습니다.
- 작업 시작 시점에 `work/4/22/2026-04-22-milestone4-5-bundle-commit-push.md`가 이미 untracked 상태였습니다.
