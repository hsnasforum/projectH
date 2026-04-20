# 2026-04-18 manual cleanup project-root resolution verification

## 변경 파일
- `verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-manual-cleanup-project-root-resolution-pinning.md`가 manual cleanup script의 `PROJECT_ROOT` 진입 계약을 focused regression 두 건으로 고정했다고 주장하므로, 현재 tree와 좁은 재검증 결과가 그 설명과 실제로 맞는지 다시 확인해야 했습니다.
- user가 같은 verify path를 같은 날 manual smoke-cleanup family 검증 슬롯로 재사용하도록 지정했으므로, 이전 pattern-override fallback verify 내용을 이번 project-root resolution round truth로 갱신합니다.

## 핵심 변경
- latest `/work`의 핵심 설명은 현재 tree와 일치합니다.
  - `tests/test_pipeline_smoke_cleanup.py`에는 실제로 `test_manual_cleanup_script_omitted_project_root_uses_cwd`와 `test_manual_cleanup_script_invalid_project_root_fails_cd`가 추가되어 있습니다.
  - 두 테스트는 positional 인자 생략 시 `pwd` fallback으로 현재 작업 디렉터리를 `PROJECT_ROOT`로 쓰는 경계와, 존재하지 않는 path를 explicit 인자로 넘겼을 때 `cd` 실패로 즉시 non-zero 종료하는 경계를 script boundary에서 직접 고정합니다.
  - `.pipeline/smoke-cleanup-lib.sh`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/README.md`는 이번 라운드에서 추가 수정 없이 이전 same-family 상태를 유지합니다. 따라서 latest `/work`의 "test-only project-root resolution pinning" 설명도 현재 tree와 맞습니다.
- focused rerun은 모두 통과했습니다.
  - `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`는 `Ran 38 tests`, `OK`였습니다.
  - `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`는 통과했습니다.
  - `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`도 출력 없이 종료됐습니다.
- docs/plan 문맥도 이번 round와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline cleanup work를 여전히 shipped browser gate 밖의 internal/operator tooling family로 두고 있으므로, 이번 slice를 same-family current-risk reduction으로 보는 편이 맞습니다.
- latest `/work`의 dirty-worktree 설명도 현재 repo truth와 충돌하지 않습니다.
  - `git status --short` 기준으로 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 tracked modified 상태였고, `tmp/` 및 same-day `/work`·`/verify` note들은 untracked 상태였습니다.

## 검증
- `git diff -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: cumulative diff 기준으로 earlier same-family helper/script/README changes가 함께 보이지만, latest `/work`가 설명한 이번 round의 새 추가분은 `tests/test_pipeline_smoke_cleanup.py`의 project-root regression 두 건이며 현재 tree와 일치함을 확인했습니다.
- `git status --short`
  - 결과: `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`가 tracked modified, `tmp/`와 same-day `/work` / `/verify` note들이 untracked로 보였습니다.
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 38 tests`, `OK`
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0
- 임시 git repo에서 handoff가 요구한 focused rerun 두 건
  - omitted `PROJECT_ROOT`: git-backed `repo with spaces`에서 `PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh`를 인자 없이 실행하면 `Smoke root: <cwd>/.pipeline`, `Pattern: live-arb-smoke-*`, `Found: 2`, `KEEP <live-arb-smoke-new two>`, `DELETE <live-arb-smoke-old one>`이 공백 포함 전체 경로로 출력됐고 dry-run이라 두 디렉터리는 그대로 남았습니다.
  - invalid explicit `PROJECT_ROOT`: `bash .pipeline/cleanup-old-smoke-dirs.sh '/nonexistent path with spaces/missing'`는 exit code `1`로 끝났고 stderr에 `.pipeline/cleanup-old-smoke-dirs.sh: line 6: cd: /nonexistent path with spaces/missing: No such file or directory`만 남겼으며 stdout header block 없이 기존 `live-arb-smoke-1`, `live-arb-smoke-2`를 그대로 보존했습니다.
- 다음 slice tie-break를 위한 추가 probe
  - 결과: non-git root에서 default live-arb pattern으로 `PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash cleanup-old-smoke-dirs.sh "<non-git root>"`를 실행하면 exit code `2`, stdout header block, stderr `prune_smoke_dirs: protect_tracked=1 requires a git-backed smoke root, got <root>/.pipeline`, 그리고 디렉터리 보존이 확인됐습니다.
  - 결과: 같은 non-git root에서 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke*'` override를 걸어도 동일하게 exit code `2`, stdout header block, 같은 stderr diagnostic, 그리고 `live-blocked-smoke-*` 디렉터리 보존이 확인됐습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경은 manual cleanup script entry 계약만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- `PROJECT_ROOT` 계약은 닫혔지만, manual cleanup script의 non-git root fail-closed 경계는 아직 repo regression으로 고정돼 있지 않습니다. 현재 probe상 default live-arb pattern과 blocked override 모두 exit code `2` + header block + helper stderr diagnostic + 디렉터리 보존으로 일관되게 끝나지만, 이 안전 경계는 이후 refactor에서 쉽게 drift할 수 있습니다.
- `_smoke_enumerate_dirs`는 여전히 탭/개행이 들어간 path를 완전히 안전하게 다루지 않습니다. 현재 smoke directory naming 관행상 낮은 리스크이지만 helper-level residual risk입니다.
- `.pipeline/README.md`의 manual cleanup 설명 중복, archive policy, fixture 재배치, 다른 smoke family wrapper 경계는 이번 verify 범위 밖입니다.
