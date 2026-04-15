# 2026-04-15 supervisor duplicate daemon reconciliation verification

## 검증 범위
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- runtime single-writer lifecycle
- stale operator stop suppression의 live 적용 조건

## 실행한 검증
- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py pipeline_runtime/supervisor.py pipeline-launcher.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_pipeline_launcher`
- live inspection
  - duplicate daemon 존재 확인
  - local marker 계산 확인
  - runtime stop/start 후 live process, `supervisor.pid`, `current_run.json`, `status.json`, `events.jsonl` 재확인

## 결과
- local code truth:
  - `RuntimeSupervisor._stale_operator_control_marker(...)`는 live `operator_request.md`에 대해 `verified_blockers_resolved`를 반환했습니다.
  - 즉 stale operator stop suppression 로직 자체는 이미 맞았습니다.
- actual runtime root cause:
  - old run daemon `20260415T133320Z-p3111179`
  - new run daemon `20260415T140814Z-p3167346`
  - 두 daemon이 동시에 살아 있어 old run이 `current_run.json`을 다시 덮고 있었습니다.
- fix 적용 후:
  - `pipeline_runtime.cli stop ... --session aip-projectH`가 matching daemon을 모두 종료했습니다.
  - 새 start 뒤 live daemon은 `20260415T141246Z-p3174015` 1개만 남았습니다.
  - `current_run.json`과 `.pipeline/supervisor.pid`가 새 run 하나를 함께 가리켰습니다.
  - `status.json`은 `runtime_state=RUNNING`, `control.active_control_status=none`, all lanes `READY`로 수렴했습니다.
  - `events.jsonl`에 `control_operator_stale_ignored`가 기록됐습니다.

## 해석
- 이번 불안정성의 직접 원인은 launcher 상태 계산보다 먼저, same-session duplicate supervisor가 single-writer 경계를 깨뜨린 것이었습니다.
- stale operator stop suppression은 그 위에서 정상 동작하고 있었지만, 옛 daemon이 `current_run`을 다시 surface해서 효과가 가려졌습니다.
- 따라서 이번 수정은 단순 start UX 보정이 아니라 runtime lifecycle invariant 복구입니다.

## 메모
- 비-TTY 환경에서 `python3 pipeline-launcher.py ...` 직접 실행은 curses 초기화 한계로 실패할 수 있으므로, launcher truth는 unit test와 runtime status/event surface로 검증했습니다.
