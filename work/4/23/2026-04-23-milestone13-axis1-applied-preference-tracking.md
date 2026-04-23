# 2026-04-23 Milestone 13 Axis 1 applied preference tracking

## 변경 파일
- `app/handlers/chat.py`
- `storage/session_store.py`
- `tests/test_export_utility.py`
- `work/4/23/2026-04-23-milestone13-axis1-applied-preference-tracking.md` (이 파일)

## 사용 skill
- `security-gate`: session message 저장 필드와 trace export payload 변경이 로컬 session 기록 범위에 머무르는지 확인했다.
- `finalize-lite`: 지정 검증 결과와 doc-sync 필요 여부, implement-lane 금지사항 준수 여부를 점검했다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 Korean closeout으로 남겼다.

## 변경 이유
- `AgentResponse.applied_preferences`는 이미 응답 직렬화에는 포함되지만, `_handle_chat_impl()`의 마지막 assistant message 저장 payload에는 남지 않았다.
- Milestone 13 Axis 1 handoff에 따라 적용된 preference fingerprint를 session message에 저장하고, 이후 trace export 경로에서 확인할 수 있게 했다.

## 핵심 변경
- `app/handlers/chat.py`의 `update_last_message()` payload에 `applied_preference_ids`를 추가했다.
- `response.applied_preferences`가 있을 때만 `[p["fingerprint"] for p in response.applied_preferences]` 형태로 session message에 저장한다.
- `storage/session_store.py`의 `stream_trace_pairs()`가 `applied_preference_ids` key를 yield하도록 했다.
- `tests/test_export_utility.py`에 preference가 적용되지 않은 trace pair에서도 `applied_preference_ids` key가 존재하고 값은 `None`임을 확인하는 테스트를 추가했다.
- `preference_store.py`, `correction_store.py`, `agent_loop.py`, 계약 파일, `.pipeline` control slot은 수정하지 않았다.

## 검증
- `python3 -m py_compile app/handlers/chat.py storage/session_store.py`
  - 통과, 출력 없음
- `python3 -m unittest tests.test_session_store tests.test_export_utility -v 2>&1 | tail -5`
  - `Ran 28 tests in 0.045s`
  - `OK`
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets tests.test_evaluate_traces -v 2>&1 | tail -5`
  - `Ran 57 tests in 0.067s`
  - `OK`
- `git diff --check -- app/handlers/chat.py storage/session_store.py`
  - 통과, 출력 없음
- `git diff --check -- app/handlers/chat.py storage/session_store.py tests/test_export_utility.py`
  - 통과, 출력 없음

## 남은 리스크
- 이번 slice는 적용된 preference id를 추적 payload에 싣는 최소 변경이다. preference 활성화 정책, UI 표시 방식, 평가 기준 변경은 포함하지 않았다.
- 신규 필드는 session message local JSON에 저장되는 감사/평가 보조 필드이며 approval/write policy를 변경하지 않는다.
- 기존 untracked `report/gemini/*` 및 PR/M12 closeout 작업 파일들은 선행 작업물로 남아 있으며 이번 round에서 수정하지 않았다.
- 커밋, 푸시, PR 생성, next-slice 선택, `.pipeline` control slot 작성은 수행하지 않았다.
