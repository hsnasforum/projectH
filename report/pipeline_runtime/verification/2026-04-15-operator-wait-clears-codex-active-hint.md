# 2026-04-15 operator wait clears codex active hint verification

## 검증 범위
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- live runtime status/task-hint

## 실행한 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --mode experimental --session aip-projectH --no-attach`

## 결과
- `py_compile` 통과
- `tests.test_pipeline_runtime_supervisor` 22건 통과
- live 재기동 후 run `20260415T102350Z-p2872254`에서 아래를 확인했습니다.
  - control: `operator_request.md / needs_operator / seq 142`
  - Codex lane: `READY`, note `prompt_visible`
  - `task-hints/codex.json`: `active: false`, `job_id: ""`, `control_seq: -1`

## 해석
- 사용자 화면에 보이던 `Codex WORKING`은 실제 작업 지속이 아니라 stale active hint / active round fallback 때문이었습니다.
- `OPERATOR_WAIT`를 verify fallback보다 우선 처리하면 operator stop이 열린 뒤 Codex surface가 실제 pane 상태와 다시 일치합니다.

## 메모
- 이번 수정은 “Codex가 멈췄는가?”에 대한 surface truth를 바로잡는 성격입니다.
- `operator_request.md`가 열린 뒤에도 active round job state가 watcher 기준으로 잠시 남을 수 있는 점은 별도 follow-up 후보입니다.
