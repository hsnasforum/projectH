# 2026-04-19 tmux scaffold failure surfacing

## 변경 파일
- 이번 라운드 직접 편집:
  - `pipeline_runtime/tmux_adapter.py`
  - `work/4/19/2026-04-19-tmux-scaffold-failure-surfacing.md`
- 이번 라운드 범위 밖의 기존 dirty worktree:
  - `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py`, `.pipeline/README.md` (직전 session_missing bounded recovery 라운드 산출물)
  - `tests/test_tmux_adapter.py` (직전 라운드가 이미 `create_scaffold()` 회귀 5건을 추가해둔 상태)
  - watcher/manual-cleanup, controller cozy, runtime docs/tests 등 이 슬라이스와 무관한 기존 편집

## 사용 skill
- `superpowers:using-superpowers`: 세션 시작 시 필수 skill 확인 규칙을 따르기 위해 사용.
- `superpowers:test-driven-development`: 기존 실패 회귀 5건을 먼저 확인한 뒤 그 계약에 맞춰 `create_scaffold()`를 좁게 고치는 순서를 지키기 위해 사용.
- `work-log-closeout`: 이번 adapter 구현 라운드의 `/work` 기록을 repo 규약 형식으로 남기기 위해 사용.

## 변경 이유
- 직전 라운드는 supervisor의 `session_missing` bounded recovery 경계를 고정하면서 `_spawn_runtime_session()`이 cold start와 recovery 양쪽에서 같은 `TmuxAdapter.create_scaffold()`를 재사용하도록 정리했습니다.
- 그 결과 recovery가 의존하는 scaffold 경로에서 필수 실패가 조용히 삼켜지면, supervisor는 `session_recovery_completed`를 찍어놓고도 실제 pane 구조가 부서진 상태로 다음 poll을 맞게 됩니다. 이는 `session_recovery_failed` 한 번으로 수렴해야 할 실패를 숨겨 retry 경계를 다시 흐리는 same-family current risk입니다.
- `python3 -m unittest -v tests.test_tmux_adapter`가 5건 실패로 이미 이 gap을 명시하고 있었고, 가장 작은 same-family 수정은 docs/live replay를 한 번 더 도는 대신 adapter에서 required step failure를 먼저 표면화하는 것이었습니다.

## 핵심 변경
- `pipeline_runtime/tmux_adapter.py`에 shared 헬퍼 `_run_required(cmd, description, *, timeout=5.0)`을 추가해, returncode가 0이 아닐 때 stderr/stdout/exit code를 description과 묶어 `RuntimeError`로 올리게 했습니다. 비중요 set-option은 계속 기존 `_run()`을 거쳐 실패를 허용합니다.
- `create_scaffold()`에서 `window-size manual`을 cosmetic loop에서 분리해 `tmux set-option -t <session>:0 window-size manual`로 required step으로 올렸습니다. 기존 `set-window-option ... window-size manual` 한 줄은 제거해 중복을 없앴습니다.
- base pane id를 읽는 `display-message` 결과가 빈 문자열이거나 returncode가 0이 아니면 `"tmux display-message for base pane id returned empty pane id: ..."` 문구로 `RuntimeError`를 올리도록 했습니다.
- Codex/Gemini split을 만드는 두 번의 `split-window` 호출을 `_split_pane_required()` shared helper로 묶어, returncode 실패 또는 빈 pane id일 때 `"tmux split <lane> pane failed: ..."` 문구로 raise합니다.
- `select-layout even-horizontal`도 `_run_required()`를 거쳐 실패 시 `"tmux select-layout even-horizontal failed: ..."`로 raise합니다.
- 상태 표시(`status-style`, `message-style`, `status-format[0]`, `pane-*-border-style`, `status-left/right`, `remain-on-exit`, `window-status-*` 등) 같은 polish 옵션은 계속 비중요 경계로 남겨 `test_create_scaffold_tolerates_cosmetic_option_failure`가 요구하는 tolerance를 유지합니다.
- 이 라운드는 대체로 이미 supervisor 쪽이 catch하는 runtime 실패 경로의 truthful surface를 복원하는 성격입니다. healthy happy path 동작은 바뀌지 않지만, scaffold 단계가 실제 실패할 때는 supervisor가 기존 `session_recovery_failed` 경로로 확정적으로 들어가도록 contract가 좁혀졌습니다.
- `.pipeline/README.md`는 건드리지 않았습니다. 기존 문서는 `session_missing` bounded recovery 경계만 적고 있고, 이번 adapter 변경은 해당 문구와 충돌하지 않으며 별도 scaffold-failure contract 문장이 없어 drift 위험이 없다고 판단했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py`
  - 결과: 통과(출력 없음)
- `python3 -m unittest -v tests.test_tmux_adapter`
  - 결과: `Ran 7 tests`, `OK` (이전 실패 5건 포함 전원 통과)
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_recreates_scaffold_once_before_lane_restart tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_session_loss_failed_recovery_is_bounded_without_lane_restart_loop`
  - 결과: `Ran 2 tests`, `OK`
- `git diff --check -- pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py .pipeline/README.md`
  - 결과: 출력 없음
- broad browser suite(`make e2e-test`)는 이번 라운드와 무관한 Python-only adapter 변경이라 생략했습니다.

## 남은 리스크
- 이번 라운드는 unit regression 계약만 복원했습니다. 실제 host에서 `session_missing` 이후 scaffold가 실패할 때 supervisor의 `session_recovery_failed` event/데그레이드 surface까지 연결되는지는 `scripts/pipeline_runtime_gate.py`의 live session-loss 단계에서 별도로 확인하는 편이 맞습니다.
- `window-size manual`을 `set-window-option`에서 `set-option -t <session>:0`으로 바꿨습니다. tmux 대부분의 버전에서는 동일하게 해석되지만, 극히 오래된 tmux 배포본에서는 window-option-only 처리를 할 수 있으므로 실제 runtime tmux 버전이 바뀐 환경에서는 scaffold가 required failure로 올라올 수 있습니다. 그런 경우에는 옵션 설정 자체를 고치지 adapter contract를 다시 느슨하게 돌리지 않는 편이 맞습니다.
- cosmetic 옵션 목록은 여전히 문자열 match로 걸러지므로, 나중에 status/style polish 항목을 더 추가하면서 실수로 필수 항목을 cosmetic loop에 섞지 않도록 주의해야 합니다.
