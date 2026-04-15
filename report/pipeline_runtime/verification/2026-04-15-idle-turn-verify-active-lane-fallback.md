# 2026-04-15 idle turn verify active-lane fallback verification

## 검증 범위
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- live runtime surface

## 실행한 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --mode experimental --session aip-projectH --no-attach`
- live 상태/이벤트 확인:
  - `.pipeline/current_run.json`
  - `.pipeline/runs/<run_id>/status.json`
  - `.pipeline/runs/<run_id>/task-hints/codex.json`
  - `.pipeline/runs/<run_id>/wrapper-events/codex.jsonl`
  - Codex pane tail

## 결과
- `py_compile` 통과
- `tests.test_pipeline_runtime_supervisor` 20건 통과
- live 재기동 후 run `20260415T085955Z-p2732359`에서 아래를 확인했습니다.
  - runtime state: `RUNNING`
  - active round: `VERIFYING` / `VERIFY_RUNNING`
  - Codex lane: `WORKING`, note `seq 136`
  - `task-hints/codex.json`: `active: true`
  - `wrapper-events/codex.jsonl`: `TASK_ACCEPTED(job_id=20260415-2026-04-15-reviewed-memory-bound-2cea9f50, control_seq=136, attempt=1)`
  - Codex pane tail: `/work` 대조, `git diff`, focused unittest 재실행 중

## 해석
- 이번 문제는 “Claude 작업이 끝났는데 다음 작업이 실제로 안 이어진 것”이 아니라, watcher가 verify round를 이미 열었는데 supervisor가 `turn_state=IDLE`만 보고 active lane을 비워 UI가 멈춘 것처럼 보인 케이스였습니다.
- 수정 후에는 active round가 verify family 상태이면 `turn_state`가 잠깐 `IDLE`이어도 Codex를 active lane으로 계속 surface하므로, launcher/controller가 runtime truth와 같은 방향으로 보입니다.

## 메모
- 이 수정은 Claude wrapper ready-toggle fix와는 계열이 다릅니다.
- Claude fix는 wrapper event source가 잘못 `TASK_DONE/READY`를 emit한 문제였고, 이번 fix는 watcher dispatch 이후 supervisor surface가 active lane을 잃던 문제를 다룹니다.
