# 2026-04-21 scope violation retrospective

## 변경 파일
- `pipeline_runtime/supervisor.py`
  - 기존 dirty worktree 기록 대상: `_force_stopped_surface` 기반 STOPPED surface, `dispatch_selection` event emission, `turn_state` name normalization.
  - 이번 라운드 코드 변경 없음.
- `pipeline_runtime/control_writers.py`
  - 기존 dirty worktree 기록 대상: `decision_class` validation.
  - 이번 라운드 코드 변경 없음.
- `work/4/21/2026-04-21-scope-violation-retrospective.md` (새 파일)

## 사용 skill
- `work-log-closeout`: 누락된 scope-violation 변경의 출처, 목적, 검증 근거를 표준 `/work` 형식으로 정리했습니다.

## 변경 이유
- seq 635 SCOPE_VIOLATION 이후 commit 전 dirty worktree에 남아 있던 4개 변경군이 별도 `/work` 노트 없이 존재했습니다.
- `_force_stopped_surface`는 `shutdown_runtime()`의 마지막 status write에서 런타임 종료 상태를 `STOPPED`, lane `OFF`, watcher inactive, idle turn state로 강제 표면화하기 위한 플래그입니다.
- `dispatch_selection` event emission은 `_build_artifacts()`가 최신 work/verify 경로, 날짜 키, mtime snapshot을 매 `_write_status()` cycle에서 이벤트로 남겨 dispatcher trace를 보강하기 위한 변경입니다.
- `turn_state` name normalization은 `CLAUDE_ACTIVE` / `CODEX_FOLLOWUP` 같은 owner-specific legacy name을 `IMPLEMENT_ACTIVE` / `VERIFY_FOLLOWUP` 계열의 lane-agnostic vocabulary로 canonicalize하기 위한 변경입니다.
- `control_writers.py`의 `decision_class` validation은 `.pipeline/operator_request.md` 또는 operator candidate status에 지원하지 않는 `decision_class` literal이 들어오는 경우 조기에 `ValueError`로 차단하기 위한 변경입니다.

## 핵심 변경
- `RuntimeSupervisor.__init__`에 `self._force_stopped_surface = False`가 추가되어 기본 경로는 기존 상태 surface를 유지합니다.
- `shutdown_runtime()`은 종료 직후 `_force_stopped_surface=True`로 final `_write_status()`를 실행하고, `_write_status()`는 degraded/control/active round/watcher/lane/task hint를 STOPPED 상태에 맞게 정리합니다.
- `_build_artifacts()`는 최신 `/work`와 대응 `/verify` 경로를 계산한 뒤 `dispatch_selection` event를 방출해 현재 dispatcher가 어떤 기록 쌍을 보았는지 추적할 수 있게 합니다.
- supervisor의 task hint, lane working surface, lane status note 경로는 `canonical_turn_state_name(...)`을 통해 `IMPLEMENT_ACTIVE`, `VERIFY_FOLLOWUP`, `ADVISORY_ACTIVE`, `OPERATOR_WAIT` 중심으로 판단합니다.
- `control_writers.py`는 normalized `decision_class`가 `SUPPORTED_DECISION_CLASSES`에 없으면 unsupported literal을 그대로 통과시키지 않고 `ValueError`를 발생시킵니다.

## 검증
- 기존 검증 근거: `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - seq 645 verify 기록 기준 `Ran 119 tests ... OK`, `rc=0`
- 기존 검증 근거: `python3 -m unittest tests.test_watcher_core`
  - seq 645 verify 기록 기준 `Ran 160 tests ... OK`, `rc=0`
- 기존 검증 근거: `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - seq 635 verify 기록 기준 `Ran 7 tests ... OK`, `rc=0`
- 이번 라운드 재실행: `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/control_writers.py`
  - 출력 없음, `rc=0`
- 이번 라운드 재실행: `python3 -m unittest tests.test_pipeline_runtime_supervisor 2>&1 | tail -3`
  - `Ran 119 tests in 1.064s`
  - `OK`, `rc=0`
- 이번 라운드 재실행: `python3 -m unittest tests.test_pipeline_runtime_control_writers 2>&1 | tail -3`
  - `Ran 7 tests in 0.006s`
  - `OK`, `rc=0`

## 남은 리스크
- 없음. 위 4개 변경군은 기존 verify 기록상 code-green이며, seq 645 이후 이번 라운드에서는 코드 변경을 하지 않았습니다.
