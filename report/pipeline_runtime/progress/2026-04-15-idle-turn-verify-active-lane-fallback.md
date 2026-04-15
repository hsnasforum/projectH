## 변경 파일
- pipeline_runtime/supervisor.py
- tests/test_pipeline_runtime_supervisor.py

## 사용 skill
- 없음

## 변경 이유
- Claude 구현 라운드가 끝난 뒤 watcher가 새 verify job을 Codex에 정상 dispatch했는데도, supervisor surface가 다음 작업을 바로 이어서 보여주지 못하는 구간이 있었습니다.
- 원인은 `turn_state`가 잠깐 `IDLE`로 내려간 순간 `active_round.status=VERIFY_RUNNING`보다 `turn_state`를 우선해 active lane을 비워 버린 데 있었습니다.

## 핵심 변경
- `RuntimeSupervisor._active_lane_for_runtime()`를 추가해 active lane 계산을 `turn_state` 단독이 아니라 `turn_state + active_round` 기준으로 접었습니다.
- `turn_state`가 `IDLE`이어도 `active_round.state`가 `VERIFY_PENDING`, `VERIFYING`, `RECEIPT_PENDING`이면 verify owner lane을 활성 lane으로 유지하도록 보강했습니다.
- `_write_status()`가 새 fallback 경로를 사용하도록 바꿔, watcher가 이미 verify round를 열어 둔 동안 launcher/controller가 Codex를 다시 `WORKING`으로 surface하도록 맞췄습니다.
- 회귀 테스트를 추가해 `turn_state=IDLE`이면서 active round가 `VERIFYING`인 경우에도 active lane이 `Codex`로 계산되도록 고정했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
- live 재기동 확인:
  - `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --mode experimental --session aip-projectH --no-attach`
  - run `20260415T085955Z-p2732359`
  - `status.json`: Codex `WORKING`, note `seq 136`
  - `task-hints/codex.json`: `active: true`, `job_id: 20260415-2026-04-15-reviewed-memory-bound-2cea9f50`
  - `wrapper-events/codex.jsonl`: `TASK_ACCEPTED` 기록 확인

## 남은 리스크
- 이번 수정은 verify/follow-up surface fallback을 바로잡는 것입니다. watcher가 `VERIFY_PENDING` 이전 discovery/stabilizing 구간에서 `IDLE`을 남기는 표시는 여전히 짧게 보일 수 있으나, 그 구간은 아직 verify owner가 확정되지 않은 상태라 의도된 보수적 동작입니다.
- 최신 6h/24h synthetic soak와 최종 cutover sign-off는 별도 채택 게이트로 남아 있습니다.
