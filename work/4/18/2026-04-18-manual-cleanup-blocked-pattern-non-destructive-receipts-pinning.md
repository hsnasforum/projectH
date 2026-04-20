# 2026-04-18 manual cleanup blocked-pattern non-destructive receipt 분기 pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-blocked-caller-space-path-propagation-pinning.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 `prune_blocked_smoke_dirs` wrapper와 `.pipeline/cleanup-old-smoke-dirs.sh`의 live-blocked-smoke 패턴 파괴적/dry-run 경로를 공백 포함 경로에 대해 regression으로 잠갔습니다.
- 같은 owner 경계에서 아직 regression으로 좁게 고정돼 있지 않은 다음 current-risk는 manual script의 세 non-destructive receipt 분기입니다.
  - `PIPELINE_SMOKE_KEEP_RECENT=0`: header block + `Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0, preserving all matching live-blocked-smoke* directories.`
  - `Nothing to clean.`(match 수 <= KEEP_RECENT): header block + `Nothing to clean.`
  - no match: header block 없이 `No live-blocked-smoke* directories found under <root>/.pipeline`
  세 경로 모두 현재 코드에서 올바르게 동작하지만, `PIPELINE_SMOKE_PATTERN='live-blocked-smoke*'` override에 대해 operator-visible contract를 잠그는 repo-level regression이 없어 refactor가 문구나 header 출력을 조용히 바꿔도 잡히지 않는 상태였습니다.
- 이번 slice는 그 세 분기만 regression으로 잠그고, helper/script 동작은 그대로 둡니다. scope는 `.pipeline/cleanup-old-smoke-dirs.sh` + `.pipeline/README.md` + `tests/test_pipeline_smoke_cleanup.py` 안으로 제한합니다. 이번 라운드는 test-only 라운드입니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 세 테스트를 추가했습니다.
  - `test_manual_cleanup_script_blocked_pattern_disabled_cleanup_receipt`: 임시 repo에 `live-blocked-smoke-TRACKED one`(mtime 100, git tracked), `live-blocked-smoke-old two`(mtime 200, untracked) 두 공백 포함 디렉터리를 두고 script를 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke*' PIPELINE_SMOKE_KEEP_RECENT=0 PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`으로 실행합니다. stdout에 header block(`Smoke root`, `Pattern: live-blocked-smoke*`, `Found: 2`, `Keep recent: 0`)과 `Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0, preserving all matching live-blocked-smoke* directories.`이 나오는지, 그리고 `DELETE ` / `PROTECT ` / `KEEP ` 파괴적 진단이 없고 두 디렉터리가 그대로 남는지를 assert합니다.
  - `test_manual_cleanup_script_blocked_pattern_nothing_to_clean_receipt`: 같은 두 디렉터리 + `PIPELINE_SMOKE_KEEP_RECENT=3`으로 실행해 header block과 `Nothing to clean.`이 출력되는지, helper-level 파괴적 진단 / `Cleanup disabled` 문구가 섞이지 않는지, 두 디렉터리가 보존되는지를 확인합니다.
  - `test_manual_cleanup_script_blocked_pattern_no_matching_dirs_receipt`: 임시 repo에 `unrelated-workspace` 하나만 두고 script를 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke*'`으로 실행해 `No live-blocked-smoke* directories found under <smoke_root>` receipt만 찍히고 header block(`Smoke root:`, `Pattern:`, `Found:`, `Keep recent:`, `Dry run:`), `Nothing to clean.`, `Cleanup disabled`, 파괴적 diagnostic이 모두 없는지 확인합니다. `unrelated-workspace`도 보존되는지 같이 assert해 pattern matcher가 sibling 디렉터리를 건드리지 않는 경계도 잠급니다.
- 세 테스트 모두 기존 `_install_manual_cleanup_script` 헬퍼를 써서 actual `.pipeline/cleanup-old-smoke-dirs.sh`를 `bash <script> <root>`로 실행합니다. 이번 slice는 test-only라 script 본문이나 shared helper는 전혀 바꾸지 않았습니다.
- `.pipeline/smoke-cleanup-lib.sh`, `.pipeline/cleanup-old-smoke-dirs.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. 세 receipt 분기 동작은 직전 라운드들(invalid-input 에러, disabled-cleanup receipt, `Nothing to clean.` / `No <pattern> directories found` receipt, 공백 경로 propagation)까지 순차적으로 쌓은 결과 그대로이며, 이번 라운드는 blocked-pattern override 축에서 같은 contract를 regression으로 좁게 잠근 것이 전부입니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. 수동 cleanup 블록이 현재 설명하는 `PIPELINE_SMOKE_KEEP_RECENT=0` fail-safe + explicit receipt 한 줄은 `live-arb-smoke*`/`live-blocked-smoke*` 양쪽 override에 대해 동일한 문장으로 읽히고, `Nothing to clean.` / `No <pattern> directories found` 분기는 이미 operator-visible contract로 명시하지 않은 상태이므로 새 문구를 넣는 것은 handoff scope-limits의 docs-only dedupe 쪽으로 흐릅니다. 따라서 README 추가 없이 진행했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 34 tests`, `OK`. 신규 `test_manual_cleanup_script_blocked_pattern_disabled_cleanup_receipt`, `test_manual_cleanup_script_blocked_pattern_nothing_to_clean_receipt`, `test_manual_cleanup_script_blocked_pattern_no_matching_dirs_receipt` 세 건이 현재 tree에서 실제로 녹색이며, 기존 31건(manual/live-arb/blocked wrapper, script receipts, helper guards, direct-caller stdout pinning, space-path helper fix, live-arb 및 blocked caller space propagation 등)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 handoff가 요구한 focused rerun 세 건을 실행했습니다.
  - disabled-cleanup: `PIPELINE_SMOKE_PATTERN='live-blocked-smoke*' PIPELINE_SMOKE_KEEP_RECENT=0 PIPELINE_SMOKE_CLEANUP_DRY_RUN=0 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir"` → stdout에 header block 다음 `Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0, preserving all matching live-blocked-smoke* directories.`이 찍히고 `live-blocked-smoke-TRACKED one`, `live-blocked-smoke-old two` 두 디렉터리가 그대로 보존됐습니다.
  - nothing-to-clean: 같은 두 디렉터리에 `PIPELINE_SMOKE_KEEP_RECENT=3`으로 재실행 → header block + `Nothing to clean.` 조합이 찍히고 두 디렉터리 보존이 확인됐습니다.
  - no-match: 같은 임시 repo의 blocked 디렉터리를 지우고 `unrelated-workspace`만 둔 상태에서 재실행 → stdout에는 `No live-blocked-smoke* directories found under <tmpdir>/.pipeline` 한 줄만 남고 header block(`Smoke root:`, `Pattern:`, `Found:`, `Keep recent:`, `Dry run:`)은 출력되지 않았으며, `unrelated-workspace`도 보존됐습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 manual cleanup script의 blocked-pattern override 축 receipt 계약만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- 세 신규 테스트는 stdout substring 기반으로 header block / disabled-cleanup receipt / `Nothing to clean.` / `No <pattern> directories found under <root>/.pipeline` 문구를 잠급니다. 진단 포맷을 바꾸려면 이 테스트, 기존 live-arb 계열 receipt regression, 그리고 `.pipeline/README.md` 수동 cleanup 블록을 한 라운드에서 같이 움직여야 drift가 조용히 들어오지 않습니다.
- `test_manual_cleanup_script_blocked_pattern_no_matching_dirs_receipt`는 `unrelated-workspace` 디렉터리 하나만 seed합니다. 다른 sibling pattern이 섞인 환경에서 blocked-pattern override가 어떻게 굴러야 하는지는 이번 scope 밖이며, 필요하면 다음 라운드에서 별도로 다뤄야 합니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, helper stdout 포맷 규약 문서화, README 수동 cleanup 섹션과 `smoke 디렉터리 정리 규약` 섹션 중복 정리 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 manual cleanup script의 invalid pattern/빈 PATTERN override 계약 regression, 혹은 README 두 섹션 중복 정리가 남아 있습니다.
