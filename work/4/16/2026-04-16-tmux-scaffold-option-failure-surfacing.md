# 2026-04-16 tmux scaffold option failure surfacing

## 변경 파일
- `pipeline_runtime/tmux_adapter.py`
- `tests/test_tmux_adapter.py`
- `work/4/16/2026-04-16-tmux-scaffold-option-failure-surfacing.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드(`work/4/16/2026-04-16-tmux-scaffold-manual-width-pin.md`)에서 `window-size manual` 옵션을 추가했지만, `verify/4/16/2026-04-16-controller-office-reset-base-verification.md`에서 "create_scaffold()는 여전히 sizing/status 관련 tmux option 적용 실패를 surface하지 않는다"는 잔여 리스크가 확인되었습니다.
- `create_scaffold()`의 `session_options` 루프가 모든 `set-option` / `set-window-option` 호출의 return code를 무시하고 있어, `window-size manual`이나 `destroy-unattached off` 같은 기능적으로 필수인 옵션이 실패해도 scaffold가 성공한 것처럼 지나갔습니다.
- 이 리스크가 해소되지 않으면 width pin이 무음 실패하여 좁은 pane 폭 문제가 재발할 수 있습니다.

## 핵심 변경
- `pipeline_runtime/tmux_adapter.py`
  - `_run_required()` 헬퍼를 추가했습니다. `_run()`을 호출한 뒤 `returncode != 0`이면 `RuntimeError`를 올리며, `label` 파라미터로 실패 원인을 특정할 수 있습니다.
  - `create_scaffold()`의 옵션 목록을 `required_options`와 `cosmetic_options`로 분리했습니다.
    - **required**: `destroy-unattached off` (global/session), `exit-empty off`, `window-size manual`, `remain-on-exit on` — scaffold가 의도한 대로 동작하려면 반드시 성공해야 하는 옵션들입니다.
    - **cosmetic**: `mouse`, `status-style`, `pane-border-style` 등 — 실패해도 scaffold 기능에는 영향 없는 스타일 옵션들입니다.
  - `required_options`는 `_run_required()`로, `cosmetic_options`는 기존 `_run()`으로 실행합니다.
- `tests/test_tmux_adapter.py`
  - `test_create_scaffold_raises_on_required_option_failure`: `window-size manual`이 실패(`returncode=1`)하면 `RuntimeError`가 발생하고, 에러 메시지에 label과 stderr가 포함되는지 검증합니다.
  - `test_create_scaffold_tolerates_cosmetic_option_failure`: `status-style` 같은 cosmetic 옵션이 실패해도 scaffold 생성이 정상 완료되는지 검증합니다.

## 검증
- `python3 -m unittest -v tests.test_tmux_adapter`
  - 결과: `Ran 4 tests in 0.002s`, `OK`
- `python3 -m py_compile pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py`
  - 결과: 출력 없음 (성공)
- `git diff --check -- pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `rg -n "[ \t]+$" tests/test_tmux_adapter.py`
  - 결과: 매치 없음 (untracked 파일 보조 whitespace 확인)
- `tmux show-option -t aip-projectH window-size`
  - 결과: `window-size manual` (live session에서 옵션이 적용된 상태 확인)
- tmux socket 접근 가능하여 live session 확인까지 수행했습니다.

## 남은 리스크
- `_run_required()`는 현재 `create_scaffold()` 내부에서만 사용됩니다. 다른 메서드(`spawn_watcher` 등)에서도 필수 tmux 명령이 실패할 수 있지만, 이번 슬라이스의 범위는 scaffold 옵션 적용에 한정했습니다.
- required/cosmetic 분류는 현재 scaffold 동작 기준입니다. 추후 새 옵션이 추가되면 어느 그룹에 넣을지 판단이 필요합니다.
- cosmetic 옵션 실패는 여전히 조용히 무시됩니다. 로깅이 없으므로 디버깅이 필요할 때 어떤 스타일 옵션이 실패했는지 추적하기 어려울 수 있습니다.
