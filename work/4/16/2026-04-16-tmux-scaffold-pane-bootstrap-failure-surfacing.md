# 2026-04-16 tmux scaffold pane bootstrap failure surfacing

## 변경 파일
- `pipeline_runtime/tmux_adapter.py`
- `tests/test_tmux_adapter.py`
- `work/4/16/2026-04-16-tmux-scaffold-pane-bootstrap-failure-surfacing.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드(`work/4/16/2026-04-16-tmux-scaffold-option-failure-surfacing.md`)에서 required scaffold option(`window-size manual`, `destroy-unattached` 등) 적용 실패를 surface하도록 `_run_required()` 헬퍼와 required/cosmetic 분리를 도입했습니다.
- 그러나 `verify/4/16/2026-04-16-controller-office-reset-base-verification.md`에서 식별된 잔여 리스크가 남아 있었습니다: 옵션 적용 이후의 pane bootstrap 단계 — base pane id 조회(`display-message`), 두 번의 `split-window`, `select-layout` — 가 여전히 return code와 빈 stdout을 무시하고 있었습니다.
- 이 경로가 실패하면 scaffold가 빈 pane id나 half-built layout으로 구성되어 이후 lane 운영이 조용히 깨질 수 있습니다.

## 핵심 변경
- `pipeline_runtime/tmux_adapter.py`
  - base pane `display-message`, 두 `split-window`, `select-layout` 호출을 기존 `_run()` 대신 `_run_required()`로 교체하여, tmux가 non-zero exit를 반환하면 label 포함 `RuntimeError`가 발생합니다.
  - `display-message`와 `split-window`는 stdout이 빈 문자열인 경우에도 별도로 "empty pane id" `RuntimeError`를 발생시킵니다 (return code 0이지만 pane id가 없는 edge case 대응).
- `tests/test_tmux_adapter.py`
  - `test_create_scaffold_raises_on_split_window_failure`: `split-window`가 `returncode=1`을 반환하면 `RuntimeError`가 발생하고 label에 `split Codex pane`이 포함되는지 검증합니다.
  - `test_create_scaffold_raises_on_empty_base_pane_id`: `display-message`가 성공(`returncode=0`)하지만 빈 stdout을 반환하면 `empty pane id` 에러가 발생하는지 검증합니다.
  - `test_create_scaffold_raises_on_select_layout_failure`: `select-layout`이 실패하면 `RuntimeError`가 발생하고 label에 `select-layout`이 포함되는지 검증합니다.

## 검증
- `python3 -m unittest -v tests.test_tmux_adapter`
  - 결과: `Ran 7 tests in 0.003s`, `OK`
- `python3 -m py_compile pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py`
  - 결과: 출력 없음 (성공)
- `git diff --check -- pipeline_runtime/tmux_adapter.py tests/test_tmux_adapter.py work/4/16`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `rg -n "[ \t]+$" tests/test_tmux_adapter.py`
  - 결과: 매치 없음 (untracked 파일 보조 whitespace 확인)
- tmux socket 접근 가능 여부: 이전 라운드에서 live session 접근이 확인되었으나, 이번 라운드에서는 별도 runtime proof를 수행하지 않았습니다 (코드 변경은 다음 `create_scaffold()` 호출 시 적용).

## 남은 리스크
- `create_scaffold()` 바깥의 다른 메서드(`spawn_watcher` 제외)에서는 여전히 tmux 명령 실패를 조용히 무시하는 곳이 있습니다 (예: `send_input`, `capture_tail`). 이들은 scaffold 구축 경로가 아니므로 이번 슬라이스 범위 밖입니다.
- scaffold bootstrap 실패 시 `RuntimeError`가 발생하지만, 이미 생성된 session이 정리되지는 않습니다 (half-created session이 남을 수 있음). 현재는 다음 `create_scaffold()` 호출 시 `kill_session()`이 정리하므로 실질적 문제는 아닙니다.
- 기존 7개 테스트 모두 mock 기반이며, 실제 tmux와의 통합 테스트는 없습니다.
