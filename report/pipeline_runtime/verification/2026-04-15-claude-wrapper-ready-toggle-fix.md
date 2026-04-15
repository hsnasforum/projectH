# 2026-04-15 Claude wrapper ready-toggle fix verification

## 검증 범위
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 실행한 검증
- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_cli`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --mode experimental --session aip-projectH --no-attach`

## 결과
- `py_compile` 통과
- `tests.test_pipeline_runtime_cli` 3건 통과
- `tests.test_pipeline_runtime_supervisor` 19건 통과
- live runtime 재기동 후 Claude lane 재확인
  - current run: `20260415T085315Z-p2721886`
  - Claude wrapper log: `TASK_ACCEPTED` 이후 40초 이상 `TASK_DONE/READY` 재발 없음
  - supervisor event log: `lane_working` 이후 `lane_ready` 재발 없음
  - runtime status: Claude `WORKING`, note `seq 136`

## 해석
- 이번 문제는 Codex 때와 같은 계열이지만 Claude lane에서 더 자주 재현되었습니다.
- 원인은 `task_hint`가 아직 active인데 wrapper가 prompt 재등장만으로 `TASK_DONE/READY`를 emit한 데 있습니다.
- 수정 후에는 task hint가 실제로 inactive가 되기 전에는 prompt가 다시 보여도 accepted task를 닫지 않으므로, implement lane의 false `READY` 반복이 멈췄습니다.

## 메모
- 이번 검증은 launcher/controller 표시 문제를 넘어서 wrapper event source 자체를 바로잡는 데 초점을 맞췄습니다.
- implement lane task identity를 closed verify job과 분리하는 후속 정리는 별도 개선 후보로 남습니다.
