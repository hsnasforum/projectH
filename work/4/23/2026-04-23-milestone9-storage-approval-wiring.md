# 2026-04-23 Milestone 9 storage approval wiring

## 변경 파일
- `core/contracts.py`
- `storage/session_store.py`
- `tests/test_session_store.py`
- `work/4/23/2026-04-23-milestone9-storage-approval-wiring.md`

## 사용 skill
- `approval-flow-audit`: pending approval 저장 구조가 바뀌므로 save-note 승인 invariant와 operator action pending record 보존 범위를 확인했습니다.
- `security-gate`: 승인 큐와 session persistence를 건드리는 변경이라 local-first, audit, rollback 기대값을 점검했습니다.
- `finalize-lite`: 구현 종료 전 실행한 체크, 문서 동기화 범위, `/work` closeout 준비 상태를 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 870이 Milestone 9 Axis 2로 `OperatorActionContract`를 pending approval queue에 연결하도록 지시했습니다.
- save-note 승인 normalizer는 `requested_path`를 요구하므로 operator action 요청은 별도 raw pending record로 기록되어야 했습니다.

## 핵심 변경
- `core/contracts.py`에 `OperatorActionRecord` `TypedDict(total=False)`를 추가했습니다.
- `ApprovalKind`에 `OPERATOR_ACTION = "operator_action"`을 추가했습니다.
- `storage/session_store.py`에 `record_operator_action_request()`를 추가해 operator action approval id를 만들고 `pending_approvals`에 `status: pending`으로 저장하도록 했습니다.
- 기존 save-note normalizer를 우회하되, session 재로드 시 operator action pending record가 사라지지 않도록 `_normalize_operator_action_record()`와 `_normalize_pending_approval_record()`를 추가했습니다.
- `tests/test_session_store.py`에 operator action pending approval round-trip 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile core/contracts.py storage/session_store.py` -> 통과
- `git diff --check -- core/contracts.py storage/session_store.py` -> 통과
- `python3 -m unittest tests.test_session_store -v 2>&1 | tail -20` -> 12개 테스트 통과 출력 확인
- `python3 -m unittest tests.test_session_store -v` -> 12개 테스트 통과
- `git diff --check -- core/contracts.py storage/session_store.py tests/test_session_store.py` -> 통과

## 남은 리스크
- 이번 라운드는 operator action request를 pending approval queue에 기록하는 storage wiring까지만 구현했습니다.
- 실제 local file edit, shell execute, session mutation 실행 경로와 승인 UI 처리는 아직 연결하지 않았습니다.
- operator action record는 승인 대기 상태로 audit 가능하게 저장되지만, outcome 처리와 rollback 실행은 별도 handoff 범위입니다.
- 문서 동기화는 이번 handoff에서 요구되지 않아 수행하지 않았습니다. 필요하면 별도 verify/handoff 라운드에서 판단해야 합니다.
