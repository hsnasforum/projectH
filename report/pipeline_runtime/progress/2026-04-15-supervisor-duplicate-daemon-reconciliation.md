## 변경 파일
- pipeline_runtime/cli.py
- tests/test_pipeline_runtime_cli.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- doc-sync

## 변경 이유
- 실운영에서 같은 `project_root + session`으로 supervisor daemon이 2개 살아 있으면서 옛 run이 `current_run.json`을 다시 덮어썼습니다.
- 그 결과 stale operator stop suppression과 launcher start 안정화 코드가 테스트에서는 맞아도, 라이브에서는 더 오래된 run 상태가 다시 보이는 split-brain이 발생했습니다.

## 핵심 변경
- `pipeline_runtime.cli`에 live supervisor reconciliation 경로를 추가했습니다.
  - `/proc/*/cmdline` 기준으로 같은 `project_root + session`의 `pipeline_runtime.cli daemon` pid를 수집합니다.
  - live daemon이 1개뿐이면 pidfile을 그 pid로 복구합니다.
  - live daemon이 2개 이상이면 `stop`/`restart` 전에 모두 종료시켜 single writer를 회복합니다.
- `stop` 경로는 pidfile 하나만 믿지 않고 matching daemon 전체를 내리도록 바꿨습니다.
- QA/Runbook/기술설계 문서에 duplicate supervisor reconciliation 규칙을 추가했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py pipeline_runtime/supervisor.py pipeline-launcher.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_pipeline_launcher`
- live restart 확인:
  - duplicate daemon 2개 존재 확인
  - `python3 -m pipeline_runtime.cli stop /home/xpdlqj/code/projectH --session aip-projectH`
  - `python3 -m pipeline_runtime.cli start /home/xpdlqj/code/projectH --mode experimental --session aip-projectH --no-attach`
  - 새 run 하나만 남고 `current_run.json`과 `supervisor.pid`가 같은 run으로 수렴함을 확인

## 남은 리스크
- duplicate daemon 정리는 현재 `project_root + session` 기준입니다. 세션명을 일부러 공유하는 특수 운영 패턴이 있다면 같은 묶음으로 정리됩니다.
- `pipeline-launcher.py`는 curses TUI라 비-TTY 환경에서 직접 실행 검증은 제한적이며, 이번 라운드에서는 관련 unit test와 runtime status truth로 확인했습니다.
