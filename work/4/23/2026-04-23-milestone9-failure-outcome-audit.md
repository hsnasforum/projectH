# 2026-04-23 Milestone 9 failure outcome audit

## 변경 파일

- `core/agent_loop.py`
- `tests/test_session_store.py`
- `work/4/23/2026-04-23-milestone9-failure-outcome-audit.md`

## 사용 skill

- `approval-flow-audit`: 승인 후 operator action 실패도 세션 감사 기록에 남기는지 확인했습니다. 기존 `save_note` 승인 경로는 변경하지 않았습니다.
- `security-gate`: 지원하지 않는 operator action은 실행하지 않고 실패 outcome만 로컬 세션 기록에 남기는 범위인지 확인했습니다.
- `finalize-lite`: handoff 지정 검증과 추가 직접 검증으로 구현 범위를 닫았습니다.
- `work-log-closeout`: 변경 파일, 검증, 잔여 리스크를 `/work`에 기록했습니다.

## 변경 이유

`CONTROL_SEQ: 882` handoff의 Milestone 9 Axis 5 final 범위입니다. 이전 round에서 operator action 성공 outcome은 `operator_action_history`에 남았지만, 승인 이후 실행 단계에서 `ValueError`가 발생하는 실패 outcome은 감사 기록에 남지 않는 틈이 있었습니다. 이번 변경은 실패도 같은 세션 히스토리에 보존해 승인 기반 실행 흐름의 감사성을 맞추는 것입니다.

## 핵심 변경

- `core/agent_loop.py`의 `_execute_pending_approval` operator action 분기에서 `execute_operator_action()`이 `ValueError`를 내면, 반환 전에 `status="failed"`와 `error=str(exc)`를 담아 `record_operator_action_outcome()`을 호출하도록 했습니다.
- 성공 경로의 `status="executed"` 및 `preview` 기록은 그대로 두었습니다.
- `tests/test_session_store.py`에 실패 outcome 저장 회귀 테스트를 추가해 `status`, `error`, `completed_at` 보존을 확인했습니다.

## 검증

- `python3 -m py_compile core/agent_loop.py`
- `git diff --check -- core/agent_loop.py`
- `python3 -m unittest tests.test_session_store -v 2>&1 | tail -20`  
  - 14개 테스트 통과
- `python3 -m unittest tests.test_operator_executor tests.test_eval_loader -v 2>&1 | tail -5`  
  - 13개 테스트 통과
- `python3 -m unittest tests.test_session_store -v`  
  - 14개 테스트 통과
- `python3 -m unittest tests.test_operator_executor tests.test_eval_loader -v`  
  - 13개 테스트 통과
- `git diff --check -- core/agent_loop.py tests/test_session_store.py`

## 남은 리스크

- UI 노출, rollback 동작, 문서 동기화는 이번 handoff 범위가 아니어서 변경하지 않았습니다.
- 지원하지 않는 action kind는 계속 실행되지 않으며, 이번 변경은 실패 감사 기록만 추가합니다.
- 실패 outcome은 현재 흐름처럼 pending approval이 pop된 뒤 실행 단계에서 실패한 경우에 기록됩니다.
