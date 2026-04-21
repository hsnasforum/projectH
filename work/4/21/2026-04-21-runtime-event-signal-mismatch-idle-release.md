# 2026-04-21 런타임 이벤트 집계와 signal_mismatch UI 보정

## 변경 파일
- `pipeline_runtime/wrapper_events.py`
- `pipeline_runtime/supervisor.py`
- `pipeline_gui/home_presenter.py`
- `watcher_core.py`
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `.pipeline/README.md`
- `work/4/21/2026-04-21-runtime-event-signal-mismatch-idle-release.md`

## 사용 skill
- `security-gate`: runtime event log, wrapper/supervisor surface, watcher dispatch/idle-release 흐름 변경 전후 위험 경계를 확인했습니다.
- `doc-sync`: `.pipeline` runtime contract 문구가 바뀌어 `.pipeline/README.md`를 동기화했습니다.
- `work-log-closeout`: 구현 라운드 종료 기록을 남깁니다.

## 변경 이유
- wrapper truth는 task-level dispatch/accept/done을 알고 있는데 supervisor/UI surface가 stale pane tail을 더 강하게 믿어 Codex 카드가 `READY + signal_mismatch`처럼 보일 수 있었습니다.
- active implement 중 새 `claude_handoff.md`가 들어왔을 때 pane이 잠깐 busy라 deferred 된 뒤, 나중에 pane이 idle이 되어도 재전달되지 않는 고착 가능성이 있었습니다.
- 선택지 메뉴가 있는 operator stop에서 `commit`, `milestone` 같은 후보 설명 단어만으로 agent-resolvable choice를 막아 자동 후속 triage가 멈출 수 있었습니다.

## 핵심 변경
- supervisor가 run-local `.pipeline/runs/<run_id>/wrapper-events/*.jsonl`의 `DISPATCH_SEEN`, `TASK_ACCEPTED`, `TASK_DONE`, `BRIDGE_DIAGNOSTIC`을 같은 run의 `events.jsonl`에 `source: "wrapper"`로 mirror합니다.
- mirror payload에는 `lane`, `job_id`, `dispatch_id`, `control_seq`, `attempt`, `derived_from`, `wrapper_ts`를 보존하고, `HEARTBEAT`는 mirror하지 않습니다.
- supervisor 재시작으로 같은 run을 이어받아도 기존 `source: "wrapper"` event key를 seed해 중복 mirror를 막습니다.
- matching `done_task.control_seq`가 active implement control seq와 같으면 stale busy tail만으로 `signal_mismatch`를 띄우지 않고 `READY + waiting_next_control`로 표시합니다.
- GUI agent card는 `signal_mismatch`, `waiting_next_control`, `prompt_visible` 같은 raw machine note를 한국어 표시(`상태 확인 필요`, `다음 지시 대기`, `대기 중`)로 변환합니다. raw note는 상세 console/debug surface에 남깁니다.
- watcher는 active implement 중 deferred 된 higher-seq handoff candidate를 저장하고, 이후 poll마다 implement lane idle 여부를 다시 확인해 조건이 맞으면 `claude_handoff_idle_release`로 1회 재전달합니다.
- operator choice menu 판정에서 순수 후보 설명에 등장한 `commit`/`push`/`milestone`/`branch` 단어만으로는 blocker로 보지 않도록 줄였습니다. `approval_record`, safety, destructive, auth/credential, truth-sync, `통과 후`/`완료 후` 순차 승인 문구는 계속 blocker로 남깁니다.
- `.pipeline/README.md`에 wrapper task event mirror, GUI note localization, idle-release 예외, choice-menu advisory-first routing 문구를 동기화했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/wrapper_events.py watcher_core.py pipeline_gui/home_presenter.py` 통과.
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py` 통과.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` 통과. 116 tests.
- `python3 -m unittest tests.test_watcher_core` 통과. 159 tests.
- `python3 -m unittest tests.test_pipeline_gui_home_presenter` 통과. 13 tests.
- `python3 -m unittest tests.test_pipeline_launcher` 통과. 23 tests.
- `python3 -m unittest tests.test_operator_request_schema` 통과. 8 tests.
- `python3 -m unittest tests.test_pipeline_runtime_cli` 통과. 18 tests.
- focused supervisor/watcher/GUI regression도 별도 통과했습니다.
- `git diff --check` 통과.
- 중간에 `tests.test_pipeline_gui_home_presenter.HomePresenterTest...`로 잘못된 class명을 지정한 1회 실행은 실패했고, 올바른 `PipelineGuiHomePresenterTest...` 지정으로 재실행해 통과했습니다.
- runtime smoke:
  - `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach` 실행 완료.
  - current run: `20260421T072522Z-p232707`.
  - `.pipeline/current_run.json`은 run-local `.pipeline/runs/20260421T072522Z-p232707/events.jsonl`를 canonical `events_path`로 가리킵니다.
  - `status.json` 기준 `runtime_state=RUNNING`, `watcher.alive=true`.
  - live current run에서는 wrapper `HEARTBEAT`/`READY`만 관찰되었고 task-level wrapper event는 아직 발생하지 않았습니다. 따라서 live `source="wrapper"` mirror 확인은 이번 smoke에서 재현되지 않았고, focused/unit test로 확인했습니다.

## 남은 리스크
- live runtime에서 실제 `DISPATCH_SEEN` / `TASK_ACCEPTED` / `TASK_DONE`가 발생한 뒤 run-local supervisor `events.jsonl`에 `source: "wrapper"`로 찍히는 장면은 이번 smoke에서 직접 관찰하지 못했습니다.
- restart 시점의 active task hint가 `control_seq=631`만 들고 `job_id`/`dispatch_id`는 비어 있어 task-level wrapper event가 나오지 않았습니다. 다음 실제 dispatch가 발생하면 live event-stream 확인을 한 번 더 하면 좋습니다.
- 현재 worktree에는 이번 round 이전부터 여러 runtime/operator-flow dirty 변경이 남아 있습니다. 이번 round는 해당 변경을 되돌리지 않고 필요한 보정만 얹었습니다.
