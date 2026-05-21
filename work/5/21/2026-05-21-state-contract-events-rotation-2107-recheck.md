# 2026-05-21 state contract events rotation 2107 recheck

## 변경 파일
- `work/5/21/2026-05-21-state-contract-events-rotation-2107-recheck.md` 신규 작성
- 이번 2107 재확인 라운드에서 신규 코드 수정은 없습니다.
- 확인 대상 기존 변경: `pipeline_runtime/state_contract.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_state_contract.py`, `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `security-gate`: runtime snapshot contract와 `events.jsonl` 로테이션이 승인 경계나 외부 publication 경계를 완화하지 않는지 재확인하기 위해 사용했습니다.
- `work-log-closeout`: 중복 handoff에 대해 실제 확인 내용과 재실행 검증 결과를 `/work`에 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2107 handoff가 이전 `state_contract_refactor_events_rotation` 슬라이스와 동일한 B9/D2 범위를 다시 요청했습니다.
- 현재 worktree에 이미 B9/D2 구현과 테스트가 반영되어 있어, 추가 코드 변경 대신 READ_FIRST와 성공 기준을 기준으로 재검증했습니다.

## 핵심 변경
- `reduce_runtime_snapshot()`은 이미 `_extract_autonomy_section()`, `_extract_control_section()`, `_extract_round_section()`, `_extract_lane_summary()`, `_extract_queue_section()` 및 조합 helper를 사용하는 thin wrapper로 분해되어 있음을 확인했습니다.
- `reduce_runtime_snapshot()` 본체는 `inspect.getsource()` 기준 11줄로, 30줄 이하 기준을 만족합니다.
- `DEFAULT_EVENTS_MAX_LINES = 2000`과 `_append_event()`의 500 이벤트 단위 rotation 경로가 이미 반영되어 있음을 확인했습니다.
- `events_rotated` marker 기록 및 2000줄 tail 보존 테스트가 존재함을 확인했습니다.
- 지정 READ_FIRST인 `verify/5/21/2026-05-21-sha256-role-receipt-schema-fixes.md`를 확인했고, 해당 verify note가 다음 슬라이스로 B9/D2를 지목한 맥락과 현재 구현 상태가 일치함을 확인했습니다.

## 검증
- 통과: `python3 - <<'PY' ... inspect.getsource(reduce_runtime_snapshot) ...`
  - 결과: `11`
- 통과: `python3 -m py_compile pipeline_runtime/state_contract.py pipeline_runtime/supervisor.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_state_contract -v 2>&1 | tail -5`
  - 결과: `Ran 230 tests`, `OK`
- 통과: `git diff --check -- pipeline_runtime/state_contract.py pipeline_runtime/supervisor.py`

## 남은 리스크
- 이번 라운드는 이미 반영된 B9/D2 구현을 재확인한 것이므로 신규 코드 변경은 없습니다.
- `events_rotated` marker는 최종 2000줄 안에 포함되도록 기존 tail 1999줄 + marker 1줄로 보존하는 현재 구현을 유지합니다.
- `.pipeline/config/agent_profile.json`, lane catalog 설정, runtime policy, sha256/receipt/schema, tmux adapter, 기존 `/work`/`verify` dirty 항목은 이전 슬라이스에서 이어진 변경이며 되돌리지 않았습니다.
- commit, push, PR 생성, merge, release, publication은 실행하지 않았습니다.
