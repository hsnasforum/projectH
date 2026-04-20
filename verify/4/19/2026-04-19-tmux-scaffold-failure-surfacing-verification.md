# 2026-04-19 tmux scaffold failure surfacing verification

## 변경 파일
- `verify/4/19/2026-04-19-tmux-scaffold-failure-surfacing-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/19/2026-04-19-tmux-scaffold-failure-surfacing.md`가 `TmuxAdapter.create_scaffold()`의 required scaffold-step failure surfacing을 복구했다고 주장하므로, 현재 tree의 실제 코드/테스트/dirty-worktree 상태가 그 설명과 맞는지 다시 확인해야 했습니다.
- prompt에 적힌 `VERIFY` 경로 `verify/4/19/2026-04-19-session-missing-bounded-recovery-verification.md`는 직전 same-family predecessor verify라서 읽고 이어받았지만, latest `/work`가 새 구현 라운드이므로 이번 tmux adapter round는 별도 `/verify` note로 닫는 편이 truthful합니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 코드와 대체로 일치합니다.
  - `pipeline_runtime/tmux_adapter.py`에는 `_run_required(...)`가 실제로 추가되어 있고, required tmux step 실패를 `RuntimeError`로 surface합니다.
  - `create_scaffold()`는 `window-size manual`을 required `set-option`으로 분리했고, base pane id empty, split-window failure/empty pane id, `select-layout` failure를 각각 명시적 예외로 올립니다.
  - `python3 -m unittest -v tests.test_tmux_adapter` 재실행에서도 `/work`가 말한 회귀 5건을 포함한 7개 테스트가 모두 통과했습니다.
- current tree 기준으로는 `/work`의 dirty-worktree inventory에 작은 drift가 1건 있습니다.
  - `git status --short pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py .pipeline/README.md` 결과는 `pipeline_runtime/tmux_adapter.py`와 `.pipeline/README.md`만 modified였습니다.
  - 따라서 `/work`가 `이번 라운드 범위 밖의 기존 dirty worktree`에 적은 `tests/test_tmux_adapter.py`는 현재 tree에서는 dirty로 보이지 않습니다.
  - 다만 이 불일치는 inventory 한 줄 수준이고, 구현/검증의 핵심 주장을 뒤집지는 않습니다. 실제 회귀 테스트 내용은 파일에 존재하며 재실행도 통과했습니다.
- `.pipeline/README.md`를 이번 라운드에서 새로 건드렸다는 증거는 현재 tree에 없습니다.
  - `git diff --name-only -- pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py .pipeline/README.md` 결과도 `.pipeline/README.md`와 `pipeline_runtime/tmux_adapter.py`만 보여 주며, README 쪽 diff는 직전 same-family/other-family 누적 dirty로 보입니다.
  - 따라서 `/work`의 “README는 이번 범위에서 건드리지 않았다”는 판단은 현재 tree와 충돌하지 않습니다.
- same-family 다음 current-risk는 live adoption gate가 bounded session recovery attempt 자체를 충분히 읽지 못하는 지점으로 좁혀졌습니다.
  - `scripts/pipeline_runtime_gate.py`의 `session loss degraded` 체크는 현재 `degraded_reason`, `degraded_reasons`, `secondary_recovery_failures`만 구조화해 남기고, bounded `session_recovery_completed` / `session_recovery_failed` event 증거는 읽지 않습니다.
  - `tests/test_pipeline_runtime_gate.py`도 representative `session_missing` 유지와 later `lane recovery` payload는 확인하지만, session-loss 직후의 bounded session-recovery terminal event 자체는 아직 contract로 잠그지 않습니다.
  - 그래서 supervisor가 `session_missing` degraded는 남기더라도 recovery attempt emit을 잃어버리는 회귀는 현재 gate에서 바로 잡히지 않을 수 있습니다.
- 위 판단에 따라 `.pipeline/claude_handoff.md`를 `CONTROL_SEQ: 351`의 same-family next slice로 갱신했습니다.
  - next slice는 `fault-check`의 `session loss degraded` 단계가 recovery-expected 상황에서 bounded `session_recovery_*` terminal event evidence까지 요구하도록 좁힙니다.
  - next-slice ambiguity나 operator-only decision은 남지 않았으므로 `.pipeline/gemini_request.md`나 `.pipeline/operator_request.md`는 새로 쓰지 않았습니다.

## 검증
- `git status --short`
  - 결과: broad dirty worktree가 여전히 존재했고, 관련 범위에서는 `.pipeline/README.md`, `pipeline_runtime/tmux_adapter.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py` 등이 modified였습니다. `tests/test_tmux_adapter.py`는 current tree에서 dirty가 아니었습니다.
- `git status --short pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py .pipeline/README.md`
  - 결과: `M .pipeline/README.md`, `M pipeline_runtime/tmux_adapter.py`만 출력됐고 `tests/test_tmux_adapter.py`는 출력되지 않았습니다.
- `git diff --name-only -- pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py .pipeline/README.md`
  - 결과: `.pipeline/README.md`, `pipeline_runtime/tmux_adapter.py`
- `git diff --stat -- pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py .pipeline/README.md`
  - 결과: `.pipeline/README.md | 5 ++-`, `pipeline_runtime/tmux_adapter.py | 77 ...`, `tests/test_tmux_adapter.py`는 없음
- `python3 -m py_compile pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_tmux_adapter`
  - 결과: `Ran 7 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_recreates_scaffold_once_before_lane_restart tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_failed_recovery_is_bounded_without_lane_restart_loop`
  - 결과: `Ran 2 tests`, `OK`
- `git diff --check -- pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py .pipeline/README.md`
  - 결과: 출력 없음, exit code `0`
- 직접 코드/테스트 대조
  - 대상: `pipeline_runtime/tmux_adapter.py`, `tests/test_tmux_adapter.py`, `scripts/pipeline_runtime_gate.py`, `tests/test_pipeline_runtime_gate.py`
  - 결과: adapter의 required failure surfacing 구현은 `/work` 설명과 일치했고, gate/session-loss 쪽은 아직 `session_recovery_completed` / `session_recovery_failed` terminal event evidence를 직접 읽는 계약이 없음을 확인했습니다.
- live tmux runtime, `python3 scripts/pipeline_runtime_gate.py fault-check ...`, browser/controller 검증은 이번 verify에서 다시 실행하지 않았습니다.
  - 이유: latest `/work`의 Python-only adapter truth 판정에는 unit/file 검증으로 충분했고, live runtime 조작은 현재 automation 세션에 직접 영향을 줄 수 있기 때문입니다.

## 남은 리스크
- latest `/work`의 핵심 구현/검증 주장은 맞지만, dirty-worktree inventory에 `tests/test_tmux_adapter.py`를 포함한 한 줄은 현재 tree와 일치하지 않습니다. 다음 closeout에서는 dirty 목록을 현재 `git status` 기준으로 더 엄밀하게 적는 편이 맞습니다.
- current `fault-check`는 `session_missing` representative reason은 확인하지만 bounded session recovery attempt의 terminal event evidence는 contract로 읽지 않습니다. 그래서 adapter failure surfacing이 live adoption gate에서 실제로 보존되는지까지는 아직 충분히 잠기지 않았습니다.
- live host에서 `window-size manual`이 실제 tmux 버전 차이로 required failure가 되는지, 그리고 그 실패가 `session_recovery_failed` evidence로 surface되는지는 이번 verify에서 다시 재현하지 않았습니다.
