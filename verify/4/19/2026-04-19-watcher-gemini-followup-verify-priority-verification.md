# 2026-04-19 watcher Gemini follow-up verify priority verification

## 변경 파일
- `verify/4/19/2026-04-19-watcher-gemini-followup-verify-priority-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- user가 지정한 latest `/work`인 `work/4/18/2026-04-18-watcher-gemini-followup-verify-priority.md`가 watcher `_poll()` 순서 버그를 닫았다고 주장하므로, 그 코드/테스트/문서/런타임 근거가 현재 트리와 실제로 맞는지 다시 확인해야 했습니다.
- prompt에 적힌 `VERIFY` 경로 `verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`는 unrelated manual-cleanup truth이므로 덮어쓰지 않았습니다. 이번 watcher round는 오늘자 새 `/verify` note로 별도 close하는 편이 truthful합니다.

## 핵심 변경
- latest `/work`의 핵심 코드/테스트 주장은 현재 트리와 일치합니다.
  - `watcher_core.py`의 `_poll()`은 now-current run `VERIFY_RUNNING` job을 Gemini arbitration pending return보다 먼저 step하고, 이어서 current run `VERIFY_PENDING` job도 같은 위치에서 우선 step합니다.
  - `tests/test_watcher_core.py`에는 `test_poll_steps_current_run_verify_running_before_pending_gemini_advice`와 `test_poll_steps_current_run_verify_pending_before_pending_gemini_request`가 실제로 들어 있습니다.
  - `.pipeline/README.md`에도 current-run verify step이 열린 `.pipeline/gemini_request.md` / `.pipeline/gemini_advice.md`보다 먼저 굴러 close chain을 얼리지 않는다는 문장이 현재 구현 truth로 적혀 있습니다.
- 좁은 재실행도 모두 통과했습니다.
  - `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`는 통과했습니다.
  - `python3 -m unittest -v tests.test_watcher_core`는 현재 `Ran 129 tests`, `OK`였습니다.
  - `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`도 통과했습니다.
- live claim은 partially corroborated지만 이번 verify에서 full rerun까지는 하지 않았습니다.
  - archived run `.pipeline/runs/20260418T125154Z-p479474/events.jsonl`에는 실제로 `runtime_started`, early `control_changed` to `.pipeline/gemini_advice.md`, 그리고 `lane_working` for `Codex`가 남아 있어 `/work`가 적은 "restart 뒤 follow-up 차례에서 Codex가 움직였다"는 큰 방향은 현재 artifact와 모순되지 않습니다.
  - 다만 같은 run의 current `status.json`은 지금 시점에는 이미 `STOPPED`/all lanes `OFF`로 내려가 있어 `/work`가 적은 당시의 transient `runtime_state=RUNNING`, `Codex=WORKING(note=followup)` snapshot을 그대로 다시 보여주지는 않습니다.
  - `.pipeline/logs/experimental/watcher.log`도 live rolling log라서 `/work`가 적은 특정 시점의 `startup_turn_codex_followup` 관찰을 그대로 재생해 주지 않습니다. 따라서 이번 `/verify`는 run artifact로 방향성만 대조했고, restart 자체는 다시 실행하지 않았습니다.
- same-family next risk는 current-run verify step priority가 아니라 Codex `TASK_ACCEPTED` evidence drift로 좁혀졌습니다.
  - 이번 verify 라운드 중 live watcher log에는 `20260419-2026-04-18-watcher-gemini-follow-3e06195c` job이 `DISPATCH_SEEN` 뒤 `codex response activity detected`를 보였는데도 `VERIFY_RUNNING -> VERIFY_PENDING (task_accept_missing)`로 되감겼습니다.
  - later same-family round인 `verify/4/18/2026-04-18-verify-dispatch-folded-accept-guard-verification.md`는 same-dispatch `TASK_DONE`가 이미 있는 post-accept fold case를 닫았지만, 이번 live evidence는 `TASK_DONE` 이전의 pre-done accept emission이 아직 흔들릴 수 있음을 보여 줍니다.
  - 따라서 `.pipeline/claude_handoff.md`는 `CONTROL_SEQ: 349`로 Codex wrapper `TASK_ACCEPTED` evidence를 watcher pane confirmation과 더 가깝게 맞추는 exact slice로 갱신했습니다.

## 검증
- `git status --short`
  - 결과: watcher family와 별도로 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `controller/assets/*`, `controller/js/cozy.js`, `pipeline_runtime/cli.py`, `tests/test_pipeline_runtime_cli.py`, `tests/test_pipeline_smoke_cleanup.py` 등 broad dirty worktree가 존재함을 확인했습니다. 이번 verify는 그중 `watcher_core.py`, `tests/test_watcher_core.py`, `.pipeline/README.md` truth만 직접 다뤘습니다.
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 129 tests`, `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 출력 없음, exit code `0`
- 직접 코드/문서 대조
  - 대상: `watcher_core.py`, `tests/test_watcher_core.py`, `.pipeline/README.md`
  - 결과: `_poll()`의 current-run `VERIFY_RUNNING` / `VERIFY_PENDING` 우선 step, regression 2개, README contract가 latest `/work` 설명과 일치함을 확인했습니다.
- archived runtime artifact 대조
  - 대상: `.pipeline/runs/20260418T125154Z-p479474/events.jsonl`, `.pipeline/runs/20260418T125154Z-p479474/status.json`, `.pipeline/runs/20260418T125154Z-p479474/wrapper-events/codex.jsonl`, `.pipeline/logs/experimental/watcher.log`
  - 결과: historical run id와 Codex `lane_working` evidence는 확인했지만, `/work`가 적은 transient live snapshot 자체를 현재 파일만으로 완전히 재생하지는 못했습니다. current `status.json`은 이미 `STOPPED`이고 rolling watcher log는 later session들에 의해 갱신돼 있습니다.
- current live incident evidence
  - 대상: `.pipeline/logs/experimental/watcher.log`
  - 결과: `2026-04-19T00:09:59`에 `codex response activity detected: attempt 1`, 이어서 `2026-04-19T00:10:30`에 same job `VERIFY_RUNNING -> VERIFY_PENDING (dispatch stall after 31s total with no TASK_ACCEPTED after DISPATCH_SEEN before 30s deadline)`가 남아 있음을 확인했습니다.
- `python3 -m pipeline_runtime.cli restart --session aip-projectH --no-attach /home/xpdlqj/code/projectH`는 이번 verify에서 다시 실행하지 않았습니다.
  - 이유: current automation 세션에 직접 영향을 주는 조작이고, 이번 round의 핵심 코드 truth는 unit/file/artifact 대조만으로 이미 판정 가능했기 때문입니다.

## 남은 리스크
- latest `/work`의 `_poll()` priority fix는 닫혔지만, current live evidence상 Codex wrapper acceptance path는 여전히 `DISPATCH_SEEN` 뒤 `TASK_ACCEPTED`를 놓칠 수 있습니다.
- current repo에는 later same-family fixes(`verify dispatch folded accept guard`, `watcher exporter current run owner metadata`)까지 이미 섞여 있으므로, next slice는 older priority bug 재개방이 아니라 wrapper acceptance evidence mismatch 쪽으로 잡는 편이 맞습니다.
- unrelated broad dirty worktree가 많아 live restart/stash 기반 비교는 이번 verify에서 intentionally 생략했습니다. 다음 implementation round도 그 변경들을 revert하지 않고 좁은 파일 집합 안에서 움직여야 합니다.
