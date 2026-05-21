# 2026-05-21 Pipeline launcher Task 3 perf caching

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/21/2026-05-21-pipeline-launcher-task3-perf-caching.md`

## 사용 skill

- `security-gate`: runtime supervisor가 제어 파일 SHA와 `raw.jsonl` 판정 결과를 캐싱하므로, 로컬 로그/상태 경계와 operator-visible duplicate handoff 표면이 바뀌지 않는지 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실패 확인, 검증 결과, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `docs/superpowers/plans/2026-05-21-pipeline-launcher-bugfixes.md`의 Task 3(P3/P4)만 실행했습니다.
- `verify/5/21/2026-05-21-pipeline-launcher-task2-logic-correctness.md`에서 남은 미수정 이슈 중 Task 3(P3/P4)이 다음 권장 슬라이스로 확인되어 있었습니다.
- 반복 status poll마다 같은 제어 파일 SHA 계산과 `raw.jsonl` 재파싱이 발생하는 성능 비용을 줄이는 것이 목적입니다.

## 핵심 변경

- P4: `RuntimeSupervisor.__init__`에 `_control_sha_cache`를 추가하고, `_control_handoff_sha()`가 같은 path/mtime 조합에서는 `read_bytes()` 없이 캐시된 SHA256을 반환하게 했습니다.
- P3: `RuntimeSupervisor.__init__`에 `_duplicate_marker_cache_key`와 `_duplicate_marker_cache_result`를 추가했습니다.
- P3: `_duplicate_control_marker()`가 artifact truth 검사 이후 `(control_path|handoff_sha|active_control_updated_at)` 키가 같으면 `raw.jsonl`을 다시 읽지 않고 이전 duplicate marker 결과를 반환하게 했습니다.
- P3: `raw.jsonl` 없음, read 실패, 즉시 marker 반환, fallback 반환 경로가 모두 같은 helper를 통해 캐시 키/결과를 갱신하도록 정리했습니다.
- P4/P3 회귀 테스트를 추가해 같은 제어 조합에서 `read_bytes()`와 `raw.jsonl read_text()`가 각각 1회만 호출되는지 확인했습니다.

## 검증

- 수정 전 실패 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_control_handoff_sha_uses_mtime_cache tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_duplicate_control_marker_caches_result_for_same_key`
  - 결과: 두 테스트 모두 실패했습니다. `_control_handoff_sha()`는 같은 파일을 2회 읽었고, `_duplicate_control_marker()`는 같은 key에서 `raw.jsonl`을 2회 읽었습니다.
- 수정 후 focused 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_control_handoff_sha_uses_mtime_cache tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_duplicate_control_marker_caches_result_for_same_key tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_duplicate_control_marker_accepts_already_done_blocked_reason tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_duplicate_control_marker_accepts_verified_handoff_truth_without_raw_log`
  - `Ran 4 tests in 0.015s` / `OK`.
- 지정 컴파일 확인:
  - `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 통과했습니다.
- 지정 전체 supervisor 테스트 확인:
  - `python3 -m unittest tests.test_pipeline_runtime_supervisor -v`
  - `Ran 187 tests in 1.169s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py work/5/21`
  - closeout 작성 전후 모두 통과했습니다.

## 남은 리스크

- Task 4-C/D(P5/P7)는 이번 라운드 범위 밖이라 건드리지 않았습니다.
- Task 1, Task 2, Task 4-A/B는 이미 앞선 라운드에서 완료된 상태로 보고 이번 변경에는 포함하지 않았습니다.
- Playwright, E2E, live runtime start/stop 검증은 요청 범위 밖이라 실행하지 않았습니다.
- 작업 시작 시점부터 대상 파일은 기존 dirty 상태였고, 이 기록은 Task 3(P3/P4) 변경만 설명합니다.
- commit, push, PR publish, merge, release는 수행하지 않았습니다.
