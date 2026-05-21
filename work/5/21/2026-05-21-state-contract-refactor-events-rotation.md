# 2026-05-21 state contract refactor events rotation

## 변경 파일
- `pipeline_runtime/state_contract.py` 수정
- `pipeline_runtime/supervisor.py` 수정
- `tests/test_pipeline_runtime_state_contract.py` 수정
- `tests/test_pipeline_runtime_supervisor.py` 수정
- `work/5/21/2026-05-21-state-contract-refactor-events-rotation.md` 신규 작성

## 사용 skill
- `security-gate`: runtime snapshot contract와 `events.jsonl` 로그 보존 정책 변경이 local-first 기록과 operator 승인 경계를 완화하지 않는지 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `reduce_runtime_snapshot()`이 runtime/autonomy, control, round, lane, queue/invariant 처리를 한 함수에서 함께 수행해 contract 회귀를 추적하기 어려웠습니다.
- `events.jsonl`은 supervisor poll과 wrapper mirror 이벤트가 누적되지만 최대 줄 수 제한이 없어 `_seed_mirrored_wrapper_event_keys()` 같은 전체 파일 읽기 경로가 점점 무거워질 수 있었습니다.

## 핵심 변경
- `reduce_runtime_snapshot()`을 11줄 thin wrapper로 축소하고, `_extract_autonomy_section()`, `_extract_control_section()`, `_extract_round_section()`, `_extract_lane_summary()`, `_extract_queue_section()` 및 조합 helper로 분해했습니다.
- runtime snapshot 반환 dict 구조는 유지하고, state contract 테스트에 top-level/nested key shape 회귀 테스트를 추가했습니다.
- `DEFAULT_EVENTS_MAX_LINES = 2000`과 500 이벤트 단위 rotation 조건을 추가했습니다.
- `_append_event()`가 500번째 이벤트마다 `events.jsonl`을 읽고 2000줄 초과 시 마지막 1999개 기존 줄과 `events_rotated` marker를 atomic rewrite 하도록 했습니다.
- rotation 중 파일 읽기 또는 쓰기 오류가 발생하면 이벤트 기록 흐름을 막지 않고 조용히 건너뛰도록 했습니다.
- supervisor 테스트에 2000줄 초과 rotation, `rotation_trigger` 보존, `events_rotated` marker 기록을 고정했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/state_contract.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_state_contract.py tests/test_pipeline_runtime_supervisor.py`
- 통과: `python3 -m unittest -v tests.test_pipeline_runtime_state_contract.RuntimeStateContractTests.test_extracted_sections_are_independently_testable tests.test_pipeline_runtime_state_contract.RuntimeStateContractTests.test_reduce_runtime_snapshot_preserves_contract_shape tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_append_event_rotates_events_jsonl_and_records_rotation_event`
  - 결과: `Ran 3 tests`, `OK`
- 통과: `python3 - <<'PY' ... inspect.getsource(reduce_runtime_snapshot) ...`
  - 결과: `reduce_runtime_snapshot()` 본문 `11`줄
- 통과: `python3 -m py_compile pipeline_runtime/state_contract.py pipeline_runtime/supervisor.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_state_contract -v 2>&1 | tail -5`
  - 결과: `Ran 227 tests`, `OK`
- 통과: `git diff --check -- pipeline_runtime/state_contract.py pipeline_runtime/supervisor.py`
- 통과: `git diff --check -- tests/test_pipeline_runtime_state_contract.py tests/test_pipeline_runtime_supervisor.py`

## 남은 리스크
- rotation marker를 최종 2000줄 안에 포함하기 위해 기존 tail 1999줄과 `events_rotated` 1줄을 보존합니다. 즉 rotation 직전 마지막 이벤트는 유지되지만, 기존 이벤트 중 하나는 marker 공간만큼 더 버려집니다.
- rotation 주기는 `_event_seq % 500 == 0` 기준입니다. rotation marker 자체도 seq를 소비하므로 이후 트리거 간격은 marker 기록 여부에 따라 499개 일반 이벤트 뒤가 될 수 있습니다.
- 이번 변경은 supervisor `events.jsonl`에 한정했고 wrapper-events 개별 JSONL 파일 보존 정책은 다루지 않았습니다.
- `.pipeline/config/agent_profile.json`, runtime policy, sha256/receipt/schema, tmux adapter, 기존 `/work`/`verify` dirty 항목은 이번 슬라이스 이전부터 이어진 변경이며 되돌리지 않았습니다.
- commit, push, PR 생성, merge, release, publication은 실행하지 않았습니다.
