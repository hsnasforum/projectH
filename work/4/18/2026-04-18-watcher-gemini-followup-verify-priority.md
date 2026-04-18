# 2026-04-18 watcher Gemini follow-up verify 우선순위 복구

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `work/4/18/2026-04-18-watcher-gemini-followup-verify-priority.md`

## 사용 skill
- `doc-sync` - current-run verify가 Gemini arbitration보다 먼저 step되어야 한다는 현재 구현 truth를 `.pipeline/README.md` 한 줄로 맞췄습니다.
- `work-log-closeout` - 이번 라운드 직접 수정 파일, 실제 실행 검증, live 재기동 관찰 결과를 projectH `/work` 형식으로 정리했습니다.

## 변경 이유
- live run `20260418T122654Z-p446611`에서 `work/4/18/2026-04-18-process-starttime-fingerprint-proc-ctime-third-fallback.md` 검증 라운드가 `Gemini -> Codex follow-up` 이후 멈춘 것처럼 보였고, 실제 상태를 확인해 보니 Codex pane은 `/verify`와 `.pipeline/gemini_request.md`를 이미 쓴 뒤 prompt로 돌아와 있었지만 job state는 계속 `VERIFY_RUNNING`에 남아 있었습니다.
- 원인은 `_poll()`의 순서였습니다. 열린 `.pipeline/gemini_request.md` 또는 `.pipeline/gemini_advice.md`가 있으면 함수가 너무 일찍 `return`해서, 바로 아래의 current-run `VERIFY_RUNNING` / `VERIFY_PENDING` step이 아예 실행되지 않았습니다.
- 이 순서 버그 때문에 `TASK_DONE -> current-round /verify receipt + next control -> receipt close` close chain이 arbitration slot 존재만으로 얼어붙을 수 있었고, 사용자는 이를 "gemini 이후 codex가 멈춤"으로 보게 됩니다.

## 핵심 변경
- `watcher_core.py`
  - `_poll()`에서 current-run `VERIFY_RUNNING` / `VERIFY_PENDING` job step을 Gemini arbitration pending return보다 앞으로 옮겼습니다.
  - 결과적으로 열린 `.pipeline/gemini_request.md` / `.pipeline/gemini_advice.md`가 있어도 current verify round는 terminal close 또는 재큐잉까지 계속 진행됩니다.
- `tests/test_watcher_core.py`
  - `test_poll_steps_current_run_verify_running_before_pending_gemini_advice`
  - `test_poll_steps_current_run_verify_pending_before_pending_gemini_request`
  - 위 두 회귀를 추가해 pending arbitration slot이 있어도 `_poll()`이 current-run verify를 먼저 step한다는 경계를 고정했습니다.
- `.pipeline/README.md`
  - current-run `VERIFY_RUNNING` job은 열린 Gemini control slot보다 먼저 step되어 close chain을 얼리지 않는다는 계약을 명시적으로 적었습니다.
- live 확인
  - `python3 -m pipeline_runtime.cli restart --session aip-projectH --no-attach /home/xpdlqj/code/projectH` 이후 새 run `20260418T125154Z-p479474`가 올라왔고, watcher는 startup에서 stale old job state를 `previous_run_nonterminal`로 archive한 뒤 `startup_turn_codex_followup`로 Codex를 다시 깨웠습니다.
  - 관찰 창에서는 `status.json`상 `runtime_state=RUNNING`, `Codex=WORKING(note=followup)`이었고, tmux pane에도 실제 follow-up reasoning이 이어지고 있어 blank freeze는 보이지 않았습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 129 tests`, `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과
- `python3 -m pipeline_runtime.cli restart --session aip-projectH --no-attach /home/xpdlqj/code/projectH`
  - 결과: 새 run `20260418T125154Z-p479474` 기동
- live 관찰
  - `.pipeline/runs/20260418T125154Z-p479474/status.json`에서 `runtime_state=RUNNING`, `control.active_control_file=.pipeline/gemini_advice.md`, `lanes.Codex.state=WORKING`
  - `.pipeline/logs/experimental/watcher.log`에서 `startup_turn_codex_followup`, `notify_codex_followup`, `codex response activity detected`
  - `tmux capture-pane -pt %197 -S -80`에서 Codex가 `ROLE: followup` 프롬프트를 읽고 `.pipeline` cleanup 제안의 범위 적합성을 계속 검토하는 출력 확인

## 남은 리스크
- 이번 수정은 "Gemini control slot 때문에 current verify round step이 얼어붙는 순서 버그"를 닫는 슬라이스입니다. 재기동 후 live pane은 실제로 움직였지만, seq 327 control outcome이 관찰 창 안에서 아직 쓰이진 않았으므로 follow-up 자체가 오래 걸리거나 별도 판단 루프에 머무는 문제는 별도 축으로 남아 있을 수 있습니다.
- 재기동 과정에서 old run의 stuck job state `20260418-2026-04-18-process-starttime-fin-ddab3709`는 `previous_run_nonterminal`로 archive됐습니다. 즉 이번 live 확인은 "새 코드가 follow-up 차례에서 멈추지 않고 움직인다"까지는 봤지만, 기존 stuck round를 in-place로 닫는 replay는 아닙니다.
- same-family dirty worktree가 이미 누적된 파일(`watcher_core.py`, `tests/test_watcher_core.py`, `.pipeline/README.md`) 위에 이번 hunk를 얹었습니다. 이 closeout의 직접 수정 범위는 `_poll()` 순서 조정, 회귀 2개 추가, README 계약 1줄 보강으로 한정됩니다.
