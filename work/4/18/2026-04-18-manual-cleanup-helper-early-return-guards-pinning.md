# 2026-04-18 manual smoke-cleanup helper early-return guard 계약 pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-manual-cleanup-helper-invalid-input-pinning.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 `prune_manual_smoke_dirs` helper의 non-empty invalid `keep_recent` 입력 no-op 계약(`abc`, `-1`, `1.5`)을 direct-caller regression으로 닫았습니다.
- 같은 manual cleanup helper 경계에서 아직 regression으로 좁게 고정돼 있지 않은 마지막 current-risk는 나머지 세 early-return guard입니다.
  - 빈 `keep_recent`(`[ -z "$keep_recent" ]`)
  - 빈 `smoke_root`(`[ -z "$smoke_root" ]`)
  - 빈 `pattern`(`[ -z "$pattern" ]`)
  세 guard 모두 현재 `return 0`로 silent no-op이지만, helper refactor가 이 branch 중 하나를 조용히 파괴적 경로로 바꿔도 잡아 줄 테스트가 없었습니다. 세 guard는 같은 helper, 같은 no-op 계약, 같은 검증 경로를 공유하므로 한 bundle로 묶는 편이 scope에 맞습니다.
- 이번 slice는 그 bundle만 regression으로 pin down하고, helper/script split과 현재 script-level receipts는 그대로 둡니다. scope는 manual smoke cleanup helper/script/docs/tests 경계 안으로 제한합니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 `test_manual_cleanup_caller_noop_on_early_return_guards`를 추가했습니다. `live-arb-smoke-one`, `live-arb-smoke-two` 두 디렉터리를 둔 임시 repo에서 세 case를 subTest로 돌립니다.
  - `empty_keep_recent`: `prune_manual_smoke_dirs "<root>/.pipeline" "live-arb-smoke-*" "" 0`
  - `missing_smoke_root`: `prune_manual_smoke_dirs "" "live-arb-smoke-*" "3" 0`
  - `missing_pattern`: `prune_manual_smoke_dirs "<root>/.pipeline" "" "3" 0`
- 각 subTest에서 아래 네 가지를 assert합니다.
  - `returncode == 0` (early-return guard는 silent no-op이며 에러 exit로 올라가지 않는다)
  - stdout에 `KEEP ` / `PROTECT ` / `DELETE ` substring이 없다 (파괴적 helper 경로로 흘러가지 않았다)
  - 두 smoke 디렉터리가 그대로 남는다 (real smoke_root가 있어도 guard가 iteration에 들어가지 않았음을 확인)
- subTest 주석으로, 세 case가 각각 어느 guard에 대응되는지와 "real smoke_root가 살아 있는 한 guard 경로는 matching 디렉터리를 절대 건드리지 않아야 한다"는 contract shape를 명시해 두었습니다.
- `.pipeline/smoke-cleanup-lib.sh`와 `.pipeline/cleanup-old-smoke-dirs.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. 세 early-return guard는 기존 code 그대로이며, 이번 라운드는 해당 no-op 계약을 direct-caller regression으로 좁게 pin down한 것이 전부입니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. 현재 README는 `PIPELINE_SMOKE_KEEP_RECENT=0` fail-safe와 explicit disabled-cleanup receipt만 명시하고, helper의 internal early-return guard는 library-level defensive 계약이라 docs 추가 없이도 helper/script split이 truthful하게 읽힙니다. helper guard 문구를 README에 다시 싣는 것은 handoff가 금지한 "README dedupe-only cleanup" 쪽으로 흘러가므로 피했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 23 tests`, `OK`. 신규 `test_manual_cleanup_caller_noop_on_early_return_guards` 한 건(subTest 3개 포함)이 현재 tree에서 실제로 녹색이며, 기존 22건(blocked/live-arb/manual non-delete receipt/zero-receipt/script invalid error/helper invalid input/fail-closed)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 focused direct-helper rerun을 두 번 실행했습니다.
  - rerun 1: `prune_manual_smoke_dirs "<tmpdir>/.pipeline" "live-arb-smoke-*" "" 0` → exit 0, stdout 빈 상태, `live-arb-smoke-one`/`live-arb-smoke-two` 보존.
  - rerun 2: `prune_manual_smoke_dirs "<tmpdir>/.pipeline" "" "3" 0` → exit 0, stdout 빈 상태, 두 디렉터리 보존.
  handoff가 요구한 "empty keep_recent"와 "missing smoke_root 또는 missing pattern" 경로를 모두 직접 관찰했습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 manual cleanup helper의 early-return guard 계약만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- 새 테스트는 세 guard를 subTest 하나로 묶었습니다. guard가 늘어나거나 순서가 바뀌면 `cases` 리스트와 문서가 같이 움직여야 silent drift를 피할 수 있습니다.
- helper가 invalid/missing 입력에서 silent no-op으로 동작하는 것과 script가 script-level invalid 입력(`PIPELINE_SMOKE_KEEP_RECENT`이 "abc" 등)에서 stderr + exit 1로 동작하는 계약은 의도적으로 다릅니다. 이 비대칭을 좁히려면 helper, script, README, regression 묶음을 한 라운드에서 같이 수정해야 하며, 이번 scope는 그 비대칭을 기존 상태 그대로 잠갔을 뿐입니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, helper stdout 진단 strict pinning, README 두 섹션 중복 정리 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 `prune_smoke_dirs` 저층 계약 pinning(`KEEP` 줄 포맷, `dry_run=1`/`protect_tracked=0` 조합 stdout), 또는 manual cleanup 관련 README 두 섹션 중복 정리 정도가 남아 있습니다.
