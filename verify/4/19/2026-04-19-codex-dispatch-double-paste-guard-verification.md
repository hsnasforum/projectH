# 2026-04-19 codex dispatch double paste guard verification

## 변경 파일
- `verify/4/19/2026-04-19-codex-dispatch-double-paste-guard-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/19/2026-04-19-codex-dispatch-double-paste-guard.md`가 Codex verify dispatch에서 prompt consumed 뒤 immediate busy/activity가 비어도 false 재반환으로 되감지하지 않게 고쳤다고 주장하므로, 현재 tree의 실제 helper/test/doc 경계와 현재 run artifact가 그 설명과 맞는지 다시 확인해야 했습니다.
- prompt에 적힌 `VERIFY` 경로 `verify/4/19/2026-04-19-fault-check-session-recovery-consumer-contract-verification.md`는 same-day prior fault-check verify라서 덮어쓰지 않았습니다. 이번 watcher round는 별도 `/verify` note로 닫는 편이 truth 보존에 맞습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 코드와 일치합니다.
  - `watcher_core.py::_dispatch_codex()`는 input cursor가 사라져 prompt가 실제로 consumed된 뒤에는 immediate working indicator나 response activity가 추가로 안 보여도 `"codex dispatch consumed without immediate confirmation: defer acceptance to wrapper events"` 로그를 남기고 `True`를 반환합니다.
  - `tests/test_watcher_core.py::CodexDispatchConfirmationTest`에는 `prompt consumed + no immediate confirmation -> True`, `prompt never consumed -> False`가 각각 실제로 고정돼 있습니다.
  - `.pipeline/README.md`도 verify dispatch helper가 prompt consumed를 dispatch 실패로 되돌리지 않고 wrapper `DISPATCH_SEEN` / `TASK_ACCEPTED` deadline이 acceptance를 맡는다고 현재 계약을 적고 있습니다.
- 좁은 재실행도 `/work`의 검증 주장과 맞았습니다.
  - `python3 -m py_compile watcher_core.py tests/test_watcher_core.py` 통과
  - `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest`는 `Ran 6 tests`, `OK`
  - `python3 -m unittest tests.test_watcher_core`는 `Ran 130 tests`, `OK`
  - `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`는 출력 없이 통과
- current run artifact도 이번 family의 immediate risk가 실제로 낮아졌음을 보여 줍니다.
  - `.pipeline/runs/20260418T162400Z-p758713/wrapper-events/codex.jsonl`에는 current job `20260419-2026-04-19-codex-dispatch-double-514e0ca4`에 대해 first dispatch에서 바로 `DISPATCH_SEEN -> TASK_ACCEPTED -> TASK_DONE`가 순서대로 남아 있습니다.
  - `.pipeline/runs/20260418T162400Z-p758713/status.json`도 verify note/control close 전 마지막 상태가 `completion_stage = receipt_close_pending`인 `VERIFY_RUNNING`으로 남아 있어, 이번 라운드는 false redispatch가 아니라 receipt/control close만 남은 상태였음을 확인했습니다.
- 다만 next control은 `.pipeline/claude_handoff.md`로 바로 고정하지 않고 `.pipeline/gemini_request.md`를 `CONTROL_SEQ: 356`으로 갱신했습니다.
  - 이번 watcher slice는 helper success/failure boundary를 닫았고, current run evidence도 same-family immediate redispatch risk가 이번 round에서는 재현되지 않았습니다.
  - 반면 `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`는 여전히 internal pipeline/operator tooling이 shipped browser release gate 바깥이라고 적고 있습니다.
  - 그래서 다음 한 슬라이스를 또 watcher/runtime family로 이어갈지, 아니면 document-first MVP 우선순위로 축을 되돌릴지에 대한 자동 tie-break 확신이 낮습니다. 이 경우 repo 규약상 Gemini arbitration을 먼저 여는 편이 truthful합니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `watcher_core.py`, `tests/test_watcher_core.py`, `.pipeline/README.md`, `work/4/19/2026-04-19-codex-dispatch-double-paste-guard.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`
  - 결과: latest `/work`가 설명한 helper/test/doc boundary는 현재 tree와 일치했고, product docs는 internal pipeline tooling이 여전히 release-gated internal surface임을 유지하고 있음을 확인했습니다.
- current run artifact 대조
  - 대상: `.pipeline/current_run.json`, `.pipeline/runs/20260418T162400Z-p758713/status.json`, `.pipeline/runs/20260418T162400Z-p758713/events.jsonl`, `.pipeline/runs/20260418T162400Z-p758713/wrapper-events/codex.jsonl`
  - 결과: current verify job이 `dispatch_control_seq = 356`으로 first-dispatch `DISPATCH_SEEN -> TASK_ACCEPTED -> TASK_DONE`까지는 이미 닫았고, close authority만 `receipt_close_pending`에 남아 있음을 확인했습니다.
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest`
  - 결과: `Ran 6 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 130 tests`, `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 출력 없음, exit code `0`
- live tmux restart, browser/controller smoke, full runtime gate는 이번 verify에서 다시 실행하지 않았습니다.
  - 이유: latest `/work`의 핵심 수정은 Python watcher dispatch helper/test/doc 경계였고, current run wrapper artifact까지 이미 남아 있어 이번 truth 판정에는 focused rerun이 충분했습니다.

## 남은 리스크
- 이번 수정은 "prompt consumed 이후 false 반환으로 같은 verify prompt를 다시 paste하는" helper-level 경계를 줄인 것입니다. vendor output 다양성 때문에 wrapper가 `DISPATCH_SEEN` 또는 `TASK_ACCEPTED`를 놓치는 다른 host-specific accept path까지 모두 닫았다고 말할 수는 없습니다.
- 다만 current run evidence에서는 same-family immediate redispatch가 재현되지 않았고, 다음 우선순위는 current-risk evidence보다 roadmap tie-break 성격이 더 강합니다. 그래서 이번 라운드는 direct implement보다 Gemini arbitration이 더 truthful합니다.
- current tree에는 watcher/runtime/controller/browser/docs 쪽 broad dirty worktree가 여전히 남아 있으므로, 다음 implement round가 정해지더라도 unrelated hunks를 revert하지 않고 bounded slice로 움직여야 합니다.
