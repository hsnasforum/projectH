# 2026-04-18 manual cleanup PROJECT_ROOT 해결 계약 pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-manual-cleanup-pattern-override-fallback-pinning.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 `.pipeline/cleanup-old-smoke-dirs.sh`의 `PIPELINE_SMOKE_PATTERN` 입력 계약(빈 override fallback + malformed pattern no-match)을 regression으로 잠갔습니다.
- 같은 manual script 경계에서 아직 regression으로 좁게 고정돼 있지 않은 current-risk는 `PROJECT_ROOT` 해결 계약이었습니다. probe로 확인된 현재 동작은 두 가지입니다.
  - positional 인자 없이 실행하면 `${1:-$(pwd)}` fallback으로 현재 작업 디렉터리를 `PROJECT_ROOT`로 쓰고, `SMOKE_ROOT`는 `<cwd>/.pipeline`이 된다.
  - 존재하지 않는 경로를 explicit 인자로 넘기면 `PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"` 라인에서 `cd`가 실패하며 shell 기본 `cd: <path>: No such file or directory` 진단이 stderr로 나가고, 전체 script는 exit 1로 종료되며 header block 이전에 끊긴다.
  두 경로 모두 operator-visible current contract이지만 repo-level regression이 없어 refactor가 fallback이나 에러 경로 동작을 조용히 바꿀 수 있었습니다.
- 이번 slice는 그 두 entry contract만 regression으로 잠그고, helper/script 동작은 그대로 둡니다. scope는 `.pipeline/cleanup-old-smoke-dirs.sh` + `.pipeline/README.md` + `tests/test_pipeline_smoke_cleanup.py` 안으로 제한합니다. 이번 라운드는 test-only 라운드입니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 두 테스트를 추가했습니다.
  - `test_manual_cleanup_script_omitted_project_root_uses_cwd`: `tempfile.TemporaryDirectory()` 밑에 `repo with spaces` 하위 디렉터리를 만들어 공백 포함 project root를 쓰는 git-backed 임시 repo를 준비하고, 그 안에 `.pipeline/smoke-cleanup-lib.sh`, `.pipeline/cleanup-old-smoke-dirs.sh`, `live-arb-smoke-old one`(mtime 100), `live-arb-smoke-new two`(mtime 300)를 배치합니다. 이어서 `PIPELINE_SMOKE_PATTERN`을 env에서 삭제하고 `PIPELINE_SMOKE_KEEP_RECENT=1`, `PIPELINE_SMOKE_CLEANUP_DRY_RUN=1`로 `bash <script>`를 positional 인자 없이 실행합니다. assertion은 (a) stdout에 `Smoke root: <project_root with spaces>/.pipeline`, `Pattern: live-arb-smoke-*`, `Found: 2`가 찍히는지, (b) `KEEP <live-arb-smoke-new two>`, `DELETE <live-arb-smoke-old one>`이 공백 포함 전체 경로로 찍히는지, (c) dry-run이라 두 디렉터리 모두 디스크에 남는지를 확인합니다. 이 테스트는 "omitted PROJECT_ROOT → `$(pwd)` fallback" + "default pattern → `live-arb-smoke-*`" + "공백 포함 path-safety" 세 계약을 한 점에서 같이 잠급니다.
  - `test_manual_cleanup_script_invalid_project_root_fails_cd`: 기존 `_make_temp_repo` helper로 `live-arb-smoke-1`, `live-arb-smoke-2` 두 디렉터리를 둔 repo를 만들고 script를 `bash <script> "/nonexistent path with spaces/missing"` + `PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`으로 실행합니다. assertion은 (a) exit code 1, (b) stderr에 `No such file or directory`와 missing path substring이 그대로 있는지, (c) stdout에 header block(`Smoke root:`/`Pattern:`/`Found:`/`Keep recent:`/`Dry run:`) / `Nothing to clean.` / `Cleanup disabled` / destructive diagnostic이 전혀 없는지, (d) 기존 두 smoke 디렉터리가 모두 보존되는지를 확인합니다. missing path가 space를 포함해도 stderr echo가 그대로 유지됨을 같이 잠급니다.
- `.pipeline/smoke-cleanup-lib.sh`, `.pipeline/cleanup-old-smoke-dirs.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. 두 entry contract 동작은 기존 그대로이며, 이번 라운드는 regression으로 좁게 잠근 것이 전부입니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. 현재 README 수동 cleanup 블록은 `PIPELINE_SMOKE_PATTERN` override 의미만 적고 있고 `PROJECT_ROOT` 인자 / 생략 시 fallback / invalid 인자 에러 경로를 명시하지 않은 상태입니다. 이 세 경로를 새로 문서화하는 것은 operator-visible behavior 문서 추가에 해당하므로 handoff scope-limits의 "broader docs cleanup 금지"에 닿을 수 있어, 이번 라운드에서는 현재 docs truth를 그대로 유지하고 regression으로만 잠갔습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 38 tests`, `OK`. 신규 `test_manual_cleanup_script_omitted_project_root_uses_cwd`, `test_manual_cleanup_script_invalid_project_root_fails_cd` 두 건이 현재 tree에서 실제로 녹색이며, 기존 36건(manual/live-arb/blocked wrapper, script receipts, helper guards, direct-caller stdout pinning, space-path helper fix, caller space propagation, blocked-pattern non-destructive receipts, pattern override fallback 등)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 handoff가 요구한 focused rerun 두 건을 실행했습니다.
  - omitted PROJECT_ROOT: `parent=$(mktemp -d)`, `mkdir "$parent/repo with spaces"`, `pushd` 후 git init + 공백 포함 live-arb 두 디렉터리를 두고 `PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh`(인자 없음)을 실행했을 때 stdout에 `Smoke root: <parent>/repo with spaces/.pipeline`, `Pattern: live-arb-smoke-*`, `Found: 2`, `KEEP <live-arb-smoke-new two>`, `DELETE <live-arb-smoke-old one>`이 공백을 포함한 전체 경로로 찍혔고 두 디렉터리는 dry-run이므로 보존됐습니다.
  - invalid PROJECT_ROOT: 같은 repo에서 `bash .pipeline/cleanup-old-smoke-dirs.sh "/nonexistent path with spaces/missing"`을 실행했을 때 exit code 1, stdout 빈 상태, stderr에 `.pipeline/cleanup-old-smoke-dirs.sh: line 6: cd: /nonexistent path with spaces/missing: No such file or directory`가 찍혔으며 기존 `live-arb-smoke-`* 두 디렉터리는 그대로 남아 있음을 확인했습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 manual cleanup script entry 계약만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- `test_manual_cleanup_script_invalid_project_root_fails_cd`는 stderr substring assertion으로 `No such file or directory`와 missing path를 잠급니다. bash 버전에 따라 `cd` 에러 메시지 포맷이 미묘하게 다를 수 있으므로, CI에서 다른 bash(예: bash 3)로 돌릴 때는 이 문자열을 다시 대조해야 합니다. 현재 개발 환경 bash에서는 정상 통과합니다.
- `test_manual_cleanup_script_omitted_project_root_uses_cwd`는 전용 setup을 이 테스트 안에 inline으로 풀었습니다. 비슷한 공백 경로 테스트가 앞으로 더 생기면 공통 헬퍼로 추출하는 것이 중복을 줄이는 길이지만, 한 건 상태에서는 handoff가 금지한 scope 확장 없이 inline이 더 경제적입니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, README 수동 cleanup 섹션과 `smoke 디렉터리 정리 규약` 섹션 중복 정리, helper stdout 포맷 규약 문서화, `PROJECT_ROOT` entry 계약의 README 추가 서술 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 manual cleanup script entry에서 `-` (stdin) / absolute vs relative 인자 차이 regression, 또는 README 두 섹션 중복 정리가 남아 있습니다.
