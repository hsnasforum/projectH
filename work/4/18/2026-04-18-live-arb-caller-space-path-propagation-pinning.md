# 2026-04-18 live-arb caller 경계 공백 포함 경로 propagation pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-prune-smoke-dirs-space-path-safety-fix.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 shared helper `_smoke_enumerate_dirs`의 공백 경로 truncation 버그를 tab-separated `find -printf` + `cut -f2-`로 닫고 direct-helper regression을 추가했습니다.
- 같은 owner 경계에서 아직 regression으로 좁게 고정돼 있지 않은 가장 가까운 current-risk는 두 live-arb entrypoint가 helper fix에 implicit하게 의존한다는 점이었습니다. `prune_live_arb_smoke_dirs` wrapper와 `.pipeline/cleanup-old-smoke-dirs.sh` manual script는 fix 직후 probe로 공백 경로에 대해 올바르게 동작하는 것이 확인됐지만, 두 caller 경계에서 propagation을 잡아 주는 repo-level focused regression이 없어 미래 refactor가 다시 caller 안으로 공백-unsafe 로직(awk/sed 등)을 몰래 넣어도 테스트가 잡지 못했습니다.
- 이번 slice는 그 두 caller를 각각 focused test로 잠그고, helper/script 동작 자체는 그대로 둡니다. scope는 `.pipeline/cleanup-old-smoke-dirs.sh` + `.pipeline/README.md` + `tests/test_pipeline_smoke_cleanup.py` 안으로 제한하며, `_smoke_enumerate_dirs` 재개방은 handoff scope-limits대로 피했습니다. 이번 라운드는 test-only 라운드입니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 `test_live_arb_caller_preserves_paths_with_spaces`를 추가했습니다. 임시 repo에 `live-arb-smoke-old one`(mtime 100), `live-arb-smoke-new two`(mtime 300) 두 디렉터리를 두고 `bash -c ". <root>/.pipeline/smoke-cleanup-lib.sh; prune_live_arb_smoke_dirs <root> 1"`를 실행합니다. wrapper가 내부 `prune_smoke_dirs` stdout을 `>/dev/null`로 삼키므로 assertion은 디스크 상태에만 의존하며, newest 공백 워크스페이스는 살아남고 older 공백 워크스페이스는 실제 삭제되는지를 확인합니다. 주석에 "fix 전에는 두 경로 모두 공백에서 잘려 실제 `rm -rf`가 매칭되지 않았다"는 회귀 근거를 남겼습니다.
- `tests/test_pipeline_smoke_cleanup.py`에 `test_manual_cleanup_script_preserves_paths_with_spaces`를 추가했습니다. 임시 repo에 같은 두 디렉터리를 두고 `.pipeline/cleanup-old-smoke-dirs.sh`를 `PIPELINE_SMOKE_PATTERN='live-arb-smoke*'`, `PIPELINE_SMOKE_KEEP_RECENT=1`로 두 번 실행합니다.
  - `PIPELINE_SMOKE_CLEANUP_DRY_RUN=1`: stdout에 `KEEP <newest full path>`, `DELETE <older full path>`가 공백을 포함한 전체 경로로 찍히고, 두 디렉터리가 모두 디스크에 남는지를 확인합니다.
  - `PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`: stdout 진단은 동일한 full-path 형식이면서 older 디렉터리는 실제로 삭제되고 newest는 보존되는지를 확인합니다.
  두 모드를 한 테스트 안에서 순서대로 실행하는 구조라 dry-run `preserves` → live `removes` propagation을 연속으로 고정합니다.
- `.pipeline/smoke-cleanup-lib.sh`, `.pipeline/cleanup-old-smoke-dirs.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. 두 caller 경계는 직전 라운드 helper fix 덕분에 이미 올바르게 동작하며, 이번 라운드는 그 propagation을 regression으로 잠근 것이 전부입니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. `smoke 디렉터리 정리 규약` 섹션과 수동 cleanup 섹션은 현재 full-path `KEEP/PROTECT/DELETE` 설명과 어긋나지 않으며, 공백 경로 전용 문구를 추가하는 것은 handoff scope-limits의 "docs-only dedupe 금지"로 넘어가므로 피했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 29 tests`, `OK`. 신규 `test_live_arb_caller_preserves_paths_with_spaces`, `test_manual_cleanup_script_preserves_paths_with_spaces` 두 건이 현재 tree에서 실제로 녹색이며, 기존 27건(manual/live-arb/blocked wrapper, script receipts, helper guards, direct-caller stdout pinning, space-path helper fix 등)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 handoff가 요구한 focused rerun 세 건을 실행했습니다.
  - wrapper: `bash -c ". <tmpdir>/.pipeline/smoke-cleanup-lib.sh; prune_live_arb_smoke_dirs <tmpdir> 1"` → `live-arb-smoke-new two`만 남고 `live-arb-smoke-old one`은 실제 삭제됐습니다. wrapper는 `>/dev/null`로 helper stdout을 삼키므로 디스크 결과가 유일한 증거입니다.
  - manual script dry-run: `PIPELINE_SMOKE_PATTERN='live-arb-smoke*' PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir"` → stdout에 `KEEP <tmpdir>/.pipeline/live-arb-smoke-new two`, `DELETE <tmpdir>/.pipeline/live-arb-smoke-old one`이 공백을 포함한 전체 경로로 찍히고 두 디렉터리 모두 보존됐습니다.
  - manual script live: 같은 환경변수에 `PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`으로 실행 → stdout 진단은 동일한 full-path 형식, `live-arb-smoke-old one`은 실제 삭제, `live-arb-smoke-new two`는 보존됐습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 caller-boundary propagation만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- `test_live_arb_caller_preserves_paths_with_spaces`는 wrapper가 `>/dev/null`로 helper stdout을 삼키기 때문에 디스크 결과만 assertion으로 잠갔습니다. 누군가 wrapper 내부를 바꿔 helper stdout을 다시 surface하고 싶다면 이 테스트와 기존 `test_live_arb_caller_keeps_newest_and_prunes_older`를 한 라운드에서 같이 수정해야 silent drift를 피할 수 있습니다.
- 두 신규 테스트는 stdout/disk substring 기반으로 공백 포함 full path만 잠급니다. 탭/개행 포함 이름은 여전히 `mapfile -t` 단계에서 깨지므로 helper fix가 필요한 범위이며, handoff도 이번 scope에서 그 확장을 막고 있습니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, README 수동 cleanup 섹션과 `smoke 디렉터리 정리 규약` 섹션 중복 정리, helper stdout 포맷 규약 문서화 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 `prune_blocked_smoke_dirs` caller 경계 공백 경로 propagation pinning, `_smoke_enumerate_dirs` 탭/개행 path-safety 확장, 또는 manual cleanup README 두 섹션 중복 정리가 남아 있습니다.
