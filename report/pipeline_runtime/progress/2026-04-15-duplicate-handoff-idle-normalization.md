# 2026-04-15 duplicate handoff suppression and Claude idle normalization

## 변경 파일
- `watcher_core.py`
- `pipeline_runtime/cli.py`
- `pipeline_runtime/wrapper_events.py`
- `pipeline_runtime/supervisor.py`
- `pipeline-launcher.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_cli.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_launcher.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 사용 skill
- `doc-sync`

## 변경 이유
- 같은 `STATUS: implement` handoff가 이미 끝난 상태인데도 active control로 남으면 Claude lane이 실제로는 프롬프트 대기인데 `WORKING`처럼 보이는 정지 표면이 있었습니다.
- runtime 본류 기준으로는 canonical control file을 지우지 않으면서도, duplicate/no-op handoff를 다시 active work로 surface하지 않도록 supervisor/wrapper/watcher를 같은 계약으로 접어야 했습니다.

## 핵심 변경
- watcher raw log에 duplicate/no-op triage의 `handoff_sha`를 함께 남기도록 보강했습니다.
- supervisor가 watcher raw signal에서 `handoff_already_completed`를 읽어 `control_duplicate_ignored` event를 쓰고, Claude lane을 `READY + waiting_next_control`로 surface하도록 바꿨습니다.
- stale `CLAUDE_ACTIVE` turn_state만으로 Claude를 계속 active lane으로 붙잡지 않도록 `active_control_status`, `control_seq`, latest receipt, duplicate marker를 같이 보게 했습니다.
- wrapper `TASK_DONE`에 optional `reason`을 붙여 `duplicate_handoff`와 일반 `task_hint_cleared`를 구분할 수 있게 했습니다.
- launcher focused detail이 implement lane에서 `control_duplicate_ignored` runtime event를 같이 보여주도록 맞췄습니다.
- runtime 문서에 duplicate handoff suppression, `waiting_next_control`, `TASK_DONE.detail.reason`, `control_duplicate_ignored`를 반영했습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/cli.py pipeline_runtime/wrapper_events.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_launcher.py tests/test_controller_server.py`
- `python3 -m unittest -v tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_pipeline_launcher tests.test_controller_server tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_backend tests.test_pipeline_gui_app tests.test_pipeline_gui_agents`
- `python3 -m unittest -v tests.test_watcher_core`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental synthetic-soak --duration-sec 30 --sample-interval-sec 1 --min-receipts 1 --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-15-synthetic-soak-short-duplicate-handoff.md`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental fault-check --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-15-fault-check-duplicate-handoff.md`
- `git diff --check -- watcher_core.py pipeline_runtime/cli.py pipeline_runtime/wrapper_events.py pipeline_runtime/supervisor.py pipeline-launcher.py tests/test_watcher_core.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_launcher.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 남은 리스크
- 이번 slice는 duplicate/no-op implement handoff suppression과 lane idle normalization에 집중했습니다. 최신 코드 기준 6h/24h synthetic soak rerun과 최종 cutover sign-off는 여전히 별도 채택 단계입니다.
- supervisor는 watcher raw log를 read-only 입력으로 사용합니다. 장기적으로 duplicate/no-op control suppression을 더 명시적인 supervisor-owned fact로 격리할 여지는 남아 있습니다.
