# 2026-05-21 Pipeline launcher Task 4-A/B structural stability

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/21/2026-05-21-pipeline-launcher-task4ab-structural-stability.md`

## 사용 skill

- `security-gate`: runtime 로그 보존, event volume 억제, local supervisor 상태 기록이 바뀌므로 감사 가능성과 로컬 파일 경계를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실패 확인, 검증 결과, 남은 리스크를 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `docs/superpowers/plans/2026-05-21-pipeline-launcher-bugfixes.md`의 Task 4-A(P1)와 Task 4-B(P2)만 실행했습니다.
- `verify/5/21/2026-05-21-pipeline-launcher-task1-bugfixes.md`에서도 P1(raw.jsonl 초기화)과 P2(dispatch_selection 반복 기록)가 다음 고위험 슬라이스로 확인되어 있었습니다.

## 핵심 변경

- P1: `_prepare_runtime_surfaces()`가 더 이상 `logs/experimental/raw.jsonl`을 빈 파일로 초기화하지 않게 했습니다.
- P1 회귀 테스트 `test_prepare_runtime_surfaces_preserves_raw_jsonl`을 추가해 기존 `implement_blocked_detected` 기록이 restart surface 준비 뒤에도 보존되는지 확인했습니다.
- P2: `RuntimeSupervisor.__init__`에 `_last_dispatch_selection_key`를 추가하고, `_build_artifacts()`가 `latest_work|latest_verify` 조합이 바뀐 경우에만 `dispatch_selection` 이벤트를 기록하게 했습니다.
- P2 회귀 테스트 `test_build_artifacts_dispatch_selection_not_emitted_when_unchanged`를 추가해 `_build_artifacts()` 3회 연속 호출 시 이벤트가 1회만 기록되는지 확인했습니다.
- 기존 `dispatch_selection` 발생, monotonic date-key, payload key stability 테스트가 계속 통과하도록 기존 payload shape는 바꾸지 않았습니다.

## 검증

- 수정 전 실패 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_prepare_runtime_surfaces_preserves_raw_jsonl tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_dispatch_selection_not_emitted_when_unchanged`
  - 결과: 두 테스트 모두 실패했습니다. `raw.jsonl` 내용이 지워졌고, `_build_artifacts()` 3회 호출에 `dispatch_selection` 이벤트가 3회 기록됐습니다.
- 수정 후 focused 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_prepare_runtime_surfaces_preserves_raw_jsonl tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_dispatch_selection_not_emitted_when_unchanged tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_emits_dispatch_selection_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_dispatch_selection_payload_key_stability`
  - `Ran 5 tests in 0.024s` / `OK`.
- 지정 컴파일 확인:
  - `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 통과했습니다.
- 지정 전체 supervisor 테스트 확인:
  - `python3 -m unittest tests.test_pipeline_runtime_supervisor -v`
  - `Ran 183 tests in 1.131s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py work/5/21`
  - closeout 작성 전후 모두 통과했습니다.

## 남은 리스크

- Task 4-C/D(P5/P7)는 이번 라운드 범위 밖이라 건드리지 않았습니다.
- Task 1, Task 2, Task 3도 이번 라운드 범위 밖입니다.
- Playwright, E2E, live runtime start/stop 검증은 실행하지 않았습니다.
- 작업 시작 시점부터 `pipeline_runtime/supervisor.py`와 `tests/test_pipeline_runtime_supervisor.py`는 기존 dirty 상태였고, 이번 기록은 P1/P2 변경만 설명합니다.
- commit, push, PR publish, merge, release는 수행하지 않았습니다.
