## 변경 파일
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/21/2026-04-21-g4-force-stopped-dispatch-selection-contract-tests.md`

## 사용 skill
- `finalize-lite`: 지정된 검증 5개만 다시 실행하고 `/work` closeout 사실관계를 정리했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` CONTROL_SEQ 599는 seq 593 scope violation 잔여분 중 `_force_stopped_surface`와 `dispatch_selection` event의 행동 계약을 테스트로 고정하라고 지시했습니다.
- `dispatch_selection`은 이미 전용 테스트가 있었지만, `_force_stopped_surface`는 `True`일 때 STOPPED를 강제 surface하는 동작과 기본 경로의 차이를 직접 비교하는 테스트가 부족했습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_supervisor.py`에 `test_force_stopped_surface_overrides_status_to_stopped`를 추가했습니다.
- 같은 `_write_status()` 호출 조건에서 `_force_stopped_surface=False`면 `runtime_state == "RUNNING"`과 READY lane surface를 유지하고, `_force_stopped_surface=True`면 `runtime_state == "STOPPED"`와 OFF lane surface로 덮어쓰는지 고정했습니다.
- `dispatch_selection` event 계약은 기존 `test_build_artifacts_emits_dispatch_selection_event`, `test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`, `test_dispatch_selection_payload_key_stability`가 이미 event 존재와 payload key를 직접 고정하고 있어 이번 라운드에서는 추가하지 않았습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 출력 없음, `rc=0`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 104 tests in 0.768s`
  - `OK`
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - `Ran 7 tests in 0.004s`
  - `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - `Ran 36 tests in 0.060s`
  - `OK`
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 출력 없음, `rc=0`

## 남은 리스크
- 이번 라운드는 테스트 파일 한 곳만 수정했습니다. production 코드와 문서는 건드리지 않았습니다.
- handoff가 명시한 `test_operator_request_schema`와 live runtime 경로는 이번 슬라이스 범위 밖이라 여전히 미확인입니다.
- AXIS-G4 end-to-end에서 synthetic task hint 값이 실제 `cli.py`의 `DISPATCH_SEEN` 방출까지 이어지는지는 verify lane의 별도 런타임 확인이 필요합니다.
