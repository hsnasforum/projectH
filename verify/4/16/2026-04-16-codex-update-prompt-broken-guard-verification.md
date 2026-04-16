# 2026-04-16 codex update prompt broken guard verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- `work/4/16/2026-04-16-codex-update-prompt-broken-guard.md`가 주장한 Codex self-update prompt miss 진단과 guard 수정 truth를 현재 코드, 테스트, run artifact 기준으로 다시 대조하는 라운드입니다.
- 다만 verification 시점에는 더 최신 `/work`인 `work/4/16/2026-04-16-controller-office-view-idea-directives.md`가 이미 생겨 있었으므로, 이번 note는 지정된 `/work` 검증까지만 닫고 다음 implement handoff는 멈춰야 합니다.

## 핵심 변경
- `pipeline_runtime/cli.py`에는 `_is_codex_update_prompt()`가 추가되어 Codex update dialog를 `READY(prompt_visible)`로 오인하지 않도록 막고, `_maybe_auto_dismiss_blocking_prompt()`는 `Skip until next version` 입력을 보내도록 연결돼 있습니다.
- `tests/test_pipeline_runtime_cli.py`에는 update dialog auto-dismiss와 no-READY misclassification 회귀 테스트가 실제로 들어 있으며, focused rerun이 통과했습니다.
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`에도 unattended runtime에서 update dialog를 `prompt_visible`로 surface하면 안 된다는 문서 sync가 들어 있습니다.
- 원래 broken 진단은 live pane 재현이 아니라 stored run artifact로 확인됐습니다. `.pipeline/runs/20260416T044347Z-p13826/wrapper-events/codex.jsonl`에는 `READY(reason=prompt_visible)` 직후 `BROKEN(reason=exit:0)`가 남아 있고, 같은 run의 `events.jsonl`에는 `degraded_entered(reason=codex_exit:0)`가 남아 있습니다.
- verification 시점의 live runtime은 이미 다음 run으로 진행되어 `.pipeline/current_run.json` 기준 `run_id=20260416T045735Z-p31079`, `runtime_state=RUNNING`, Codex lane `WORKING`, lane note `seq 174`, `control_status=implement`였습니다. 따라서 기존 verify 초안의 "현재 runtime도 degraded" 서술은 stale이었고 이번 note에서 artifact 기준으로 바로잡았습니다.
- `pipeline_runtime/cli.py`와 runtime docs 두 파일에는 같은 날 다른 round의 변경도 함께 섞여 있습니다. 이번 검증은 update-prompt guard 관련 hunk가 실제로 존재함을 확인한 것이며, 해당 파일의 전체 dirty diff를 전부 이 `/work` 한 건으로 재귀속한 것은 아닙니다.

## 검증
- `rg -n "_is_codex_update_prompt|_CODEX_UPDATE_SKIP_MARKERS|_text_is_ready|_maybe_auto_dismiss_blocking_prompt|Please restart Codex|Skip until next version|update prompt" pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: update prompt guard helper, READY 차단, auto-dismiss, 두 runtime docs 문구가 모두 확인됐습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli`
  - 결과: `Ran 10 tests in 0.019s`, `OK`
- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 결과: 오류 없음
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: 출력 없음
- `python3 - <<'PY' ... .pipeline/current_run.json / status.json 확인 ... PY`
  - 결과: current run은 `20260416T045735Z-p31079`, `runtime_state=RUNNING`, Codex lane `WORKING`, lane note `seq 174`, `control_status=implement`였습니다.
- `rg -n "codex_exit:0|Please restart Codex|Update available|Skip until next version|exit:0" .pipeline/runs .pipeline/current_run.json`
  - 결과: `.pipeline/runs/20260416T044347Z-p13826/` 아래에서 `codex_exit:0` degraded artifact와 Codex wrapper `BROKEN(reason=exit:0)` 기록을 확인했습니다.
- `tmux capture-pane -pt %5 -S -200`
  - 결과: `can't find pane: %5`

## 남은 리스크
- 원래 issue가 발생했던 pane `%5`는 현재 존재하지 않아, work note에 적힌 pane 출력은 live rerun이 아니라 stored run artifact 기준으로만 다시 확인할 수 있었습니다.
- `_CODEX_UPDATE_SKIP_MARKERS`는 현재 dialog copy(`Update available`, `Update now`, `Skip until next version`)에 맞춰져 있습니다. Codex CLI 문구가 다시 바뀌면 marker 조정이 필요할 수 있습니다.
- 더 최신 `/work`인 `work/4/16/2026-04-16-controller-office-view-idea-directives.md`가 아직 `/verify`와 짝지어지지 않았으므로, 이 note만으로 다음 implement handoff를 새로 여는 것은 truth-sync 기준에 맞지 않습니다.
