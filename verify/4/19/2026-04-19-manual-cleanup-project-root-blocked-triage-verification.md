# 2026-04-19 manual cleanup implement_blocked project-root triage verification

## 변경 파일
- `verify/4/19/2026-04-19-manual-cleanup-project-root-blocked-triage-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- watcher가 전달한 `STATUS: implement_blocked` sentinel은 `.pipeline/claude_handoff.md`의 `CONTROL_SEQ: 347` handoff가 이미 prior `/work` + `/verify`에서 닫힌 `PROJECT_ROOT` regression을 다시 요구하고 있다고 주장했습니다.
- Codex triage 라운드에서는 이 막힘이 실제 truth인지 확인한 뒤, Claude가 같은 닫힌 범위를 다시 구현하지 않도록 next control outcome을 정확히 하나로 다시 열어야 했습니다.

## 핵심 변경
- 현재 tree는 blocked reason과 일치합니다.
  - `tests/test_pipeline_smoke_cleanup.py`에는 이미 `test_manual_cleanup_script_omitted_project_root_uses_cwd`와 `test_manual_cleanup_script_invalid_project_root_fails_cd`가 들어 있습니다.
  - 따라서 `CONTROL_SEQ: 347`이 지시했던 `PROJECT_ROOT` 계약 regression 두 건은 이미 landed 상태이며, 같은 slice를 다시 `implement`로 보내는 것은 truthful하지 않습니다.
- 좁은 재검증도 이 판단을 지지합니다.
  - `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`는 현재 `Ran 38 tests`, `OK`였습니다.
  - `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`도 통과했습니다.
- 다음 same-family current-risk는 manual cleanup script의 non-git `PROJECT_ROOT` fail-closed script boundary로 좁혀졌습니다.
  - non-git temp root에 matching `live-arb-smoke-*` 두 개를 두고 `PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh "<root>"`를 실행하면 현재 구현은 exit code `2`, stdout header block(`Smoke root`, `Pattern`, `Found`, `Keep recent`, `Dry run`), stderr helper diagnostic(`protect_tracked=1 requires a git-backed smoke root`), 디렉터리 보존으로 끝납니다.
  - 같은 non-git root에서 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*'` override를 걸어도 동일한 exit-2/header/stderr/preservation contract가 재현됩니다.
  - 이 두 경계는 안전 관련 current behavior이지만 아직 repo regression으로 잠겨 있지 않으므로, same-family current-risk reduction으로 바로 이어지는 편이 맞습니다.
- 위 판단에 따라 `.pipeline/claude_handoff.md`를 `CONTROL_SEQ: 348`의 새 exact slice로 갱신했습니다.
  - 새 handoff는 `pin manual cleanup non-git-root fail-closed script contract`만 요구합니다.
  - next-slice ambiguity나 operator-only decision은 남지 않았으므로 `.pipeline/gemini_request.md`나 `.pipeline/operator_request.md`는 새로 쓰지 않았습니다.

## 검증
- `git status --short`
  - 결과: same-family overlap으로 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`가 modified 상태였고, unrelated 변경으로 `docs/projectH_pipeline_runtime_docs/03_기초설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`, `pipeline_runtime/cli.py`, `tests/test_pipeline_runtime_cli.py`도 modified 상태였습니다. `tmp/`와 여러 same-day `/work` note는 untracked였습니다.
- `git diff --unified=3 -- .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: project-root regression 두 건이 `tests/test_pipeline_smoke_cleanup.py`에 실제로 들어와 있고, same-family helper/script/README cumulative diff도 latest `/work` + `/verify` 설명과 충돌하지 않음을 확인했습니다.
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 38 tests`, `OK`
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과
- non-git root focused rerun 1
  - 명령: non-git temp root에 `live-arb-smoke-old one`, `live-arb-smoke-new two`를 만들고 `PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir"` 실행
  - 결과: exit code `2`, stdout에 `Smoke root: <tmpdir>/.pipeline`, `Pattern: live-arb-smoke-*`, `Found: 2`, `Keep recent: 1`, `Dry run: 1`가 찍혔고 stderr에 `prune_smoke_dirs: protect_tracked=1 requires a git-backed smoke root, got <tmpdir>/.pipeline`가 남았습니다. `KEEP ` / `DELETE ` / `PROTECT ` line은 없었고 두 디렉터리는 그대로 남았습니다.
- non-git root focused rerun 2
  - 명령: non-git temp root에 `live-blocked-smoke-old one`, `live-blocked-smoke-new two`를 만들고 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*' PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir"` 실행
  - 결과: exit code `2`, stdout에 `Smoke root: <tmpdir>/.pipeline`, `Pattern: live-blocked-smoke-*`, `Found: 2`, `Keep recent: 1`, `Dry run: 1`가 찍혔고 stderr에 같은 helper diagnostic이 남았습니다. `KEEP ` / `DELETE ` / `PROTECT ` line은 없었고 두 디렉터리는 그대로 남았습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 triage 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 판단은 manual cleanup script same-family current-risk selection에 한정됐고, shipped browser contract나 runtime contract를 새로 넓히지 않았기 때문입니다.

## 남은 리스크
- 새 handoff가 겨냥한 non-git `PROJECT_ROOT` fail-closed script contract는 아직 test로 잠기지 않았습니다. 현재는 probe truth만 있고 repo regression은 없습니다.
- `stdin` 대용 `-` 인자, absolute vs relative `PROJECT_ROOT` 차이, manual cleanup README 두 섹션 중복 정리, `_smoke_enumerate_dirs`의 tab/newline path support는 여전히 이번 범위 밖입니다.
- unrelated dirty worktree(`pipeline_runtime/*`, 관련 docs/tests)는 이번 triage와 무관하지만 실제로 존재하므로, 다음 Claude 라운드는 그 변경을 revert하지 않고 같은 tree 위에서 작업해야 합니다.
