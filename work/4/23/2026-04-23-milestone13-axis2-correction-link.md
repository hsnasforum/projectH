# 2026-04-23 Milestone 13 Axis 2 correction link

## 변경 파일
- `storage/correction_store.py`
- `app/handlers/feedback.py`
- `tests/test_export_utility.py`
- `work/4/23/2026-04-23-milestone13-axis2-correction-link.md` (이 파일)

## 사용 skill
- `security-gate`: correction record에 session message 기반 preference id를 보존하는 변경이 로컬 감사/평가 기록 범위에 머무르는지 확인했다.
- `finalize-lite`: 지정 검증 결과와 implement-lane 금지사항 준수 여부를 점검했다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 Korean closeout으로 남겼다.

## 변경 이유
- M13 Axis 1에서 assistant session message에 `applied_preference_ids`가 저장되지만, 사용자가 correction을 제출할 때 correction record에는 해당 preference id가 남지 않았다.
- CONTROL_SEQ 961 handoff에 따라 personalized 응답이 이후 correction과 연결되는지 추적할 수 있도록 correction store 기록에 applied preference id를 보존했다.

## 핵심 변경
- `CorrectionStore.record_correction()`에 `applied_preference_ids: list[str] | None = None` 파라미터를 추가했다.
- 새 correction record dict에 `applied_preference_ids` 필드를 저장한다.
- `FeedbackHandlerMixin.submit_correction()`의 `record_correction()` 호출부가 `updated_message.get("applied_preference_ids")`를 전달한다.
- `tests/test_export_utility.py`에 `record_correction()`이 `["pref-abc"]`와 `None`을 각각 record에 보존하는지 확인하는 테스트를 추가했다.
- `session_store.py`, `agent_loop.py`, `preference_store.py`, 계약 파일, `.pipeline` control slot은 수정하지 않았다.

## 검증
- `python3 -m py_compile storage/correction_store.py app/handlers/feedback.py`
  - 통과, 출력 없음
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets tests.test_evaluate_traces -v 2>&1 | tail -5`
  - `Ran 58 tests in 0.060s`
  - `OK`
- `git diff --check -- storage/correction_store.py app/handlers/feedback.py`
  - 통과, 출력 없음
- `git diff --check -- storage/correction_store.py app/handlers/feedback.py tests/test_export_utility.py`
  - 통과, 출력 없음

## 남은 리스크
- 이번 slice는 correction record에 적용 preference id를 연결하는 최소 변경이다. preference 효과 판정, UI 표시, 자동 활성화 정책은 포함하지 않았다.
- `applied_preference_ids`는 session message에서 전달된 값을 그대로 보존한다. 별도 정규화나 schema 계약 추가는 handoff 범위 밖이라 수행하지 않았다.
- 기존 untracked `work/4/23/2026-04-23-milestone13-docsync-commit-push.md`는 선행 commit/push closeout으로 남아 있으며 이번 round에서 수정하지 않았다.
- 커밋, 푸시, PR 생성, next-slice 선택, `.pipeline` control slot 작성은 수행하지 않았다.
