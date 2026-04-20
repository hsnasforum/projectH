# 2026-04-18 `prune_smoke_dirs` live-arb 계약 stdout/dry-run pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-manual-cleanup-helper-early-return-guards-pinning.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 manual wrapper의 세 early-return guard를 regression으로 잠갔습니다.
- 같은 smoke-cleanup family에서 아직 regression으로 좁게 고정돼 있지 않은 가장 가까운 current-risk는 shared helper `prune_smoke_dirs`의 live-arb-style 비보호(`protect_tracked=0`) 경로 두 contract입니다.
  - live run(`dry_run=0`)에서 stdout에 `KEEP <newest>` + `DELETE <older>` 진단이 정확히 나오고 `PROTECT`는 절대 나오지 않는다.
  - `dry_run=1`에서 같은 KEEP/DELETE 진단을 내면서도 매칭 디렉터리는 전부 그대로 남는다.
  두 contract는 manual/live-arb wrapper regression에서 "디렉터리 결과"로는 간접 커버됐지만, direct helper 경로에서 stdout과 dry-run의 non-destructive 성격을 같이 잠그는 테스트는 없었습니다.
- 이번 slice는 그 두 contract를 direct-caller regression으로 pin down하고, helper 동작과 manual/live-arb wrapper 계약은 그대로 둡니다. scope는 `.pipeline/smoke-cleanup-lib.sh` + `.pipeline/README.md` + `tests/test_pipeline_smoke_cleanup.py` 안으로 제한합니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 두 개의 direct-caller regression을 추가했습니다.
  - `test_live_arb_prune_smoke_dirs_live_run_emits_keep_delete_stdout`: `live-arb-smoke-older`(mtime 100), `live-arb-smoke-middle`(200), `live-arb-smoke-newest`(300)를 두고 기존 helper `_call_prune(root, "live-arb-smoke-*", keep_recent=1, protect_tracked=0, dry_run=0)`을 실행합니다. stdout에 `KEEP <newest>`, `DELETE <middle>`, `DELETE <older>`가 실제로 찍히는지, `PROTECT ` substring은 절대 나오지 않는지, 디렉터리 결과는 newest만 살아남는지를 같이 assert합니다.
  - `test_live_arb_prune_smoke_dirs_dry_run_preserves_and_reports`: 같은 세 디렉터리를 둔 상태에서 `dry_run=1`로 helper를 호출해 stdout 진단은 live run과 동일한 `KEEP`/`DELETE` 조합이면서 `PROTECT`는 없고, 세 디렉터리가 모두 남는지를 assert합니다. 이로써 "dry-run은 plan만 찍고 실제 삭제는 하지 않는다"는 shared-helper 계약을 좁게 잠갑니다.
- `.pipeline/smoke-cleanup-lib.sh`와 `.pipeline/cleanup-old-smoke-dirs.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. `prune_smoke_dirs`의 live-arb-style 비보호 경로 동작은 기존과 동일하며, 이번 라운드는 해당 stdout/dry-run 계약을 direct-caller regression으로 좁게 pin down한 것이 전부입니다. 이번 slice는 test-only 라운드입니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. 현재 README `smoke 디렉터리 정리 규약` 섹션의 "KEEP/PROTECT/DELETE 세 가지 출력"과 "`dry_run=1`이면 실제 삭제 없이 같은 경로 로그" 설명은 이번에 잠근 contract와 정확히 일치하므로 문구 추가가 필요하지 않습니다. "README dedupe-only cleanup"은 handoff scope-limits가 금지한 범위이기도 합니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 25 tests`, `OK`. 신규 `test_live_arb_prune_smoke_dirs_live_run_emits_keep_delete_stdout`, `test_live_arb_prune_smoke_dirs_dry_run_preserves_and_reports` 두 건이 현재 tree에서 실제로 녹색이며, 기존 23건(manual/live-arb/blocked/zero-receipt/script invalid error/helper invalid input/early-return guards/fail-closed)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 handoff가 요구한 direct-helper rerun 두 건을 실행했습니다.
  - live: `prune_smoke_dirs "<tmpdir>/.pipeline" "live-arb-smoke-*" 1 0 0` → stdout `KEEP <newest>`, `DELETE <middle>`, `DELETE <older>`가 순서대로 찍히고 디렉터리는 newest만 남음.
  - dry-run: 같은 helper를 `dry_run=1`로 호출 → stdout 진단은 동일하고 세 디렉터리 모두 그대로 보존됨.
  이 결과는 추가한 두 regression이 기대하는 동작과 정확히 일치합니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 shared helper `prune_smoke_dirs`의 live-arb 경로 stdout/dry-run 계약만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- 새 두 테스트는 stdout substring assertion으로 `KEEP <path>` / `DELETE <path>`를 잠급니다. 진단 포맷을 바꾸고 싶다면 두 테스트와 `.pipeline/README.md`, 기존 manual/live-arb/blocked wrapper regression까지 한 라운드에서 같이 움직여야 drift 없이 넘길 수 있습니다.
- 이번 slice는 `protect_tracked=0` 경로만 잠갔습니다. `protect_tracked=1` 경로의 stdout/dry-run contract는 blocked/manual regression에서 결과 기반으로 커버되지만, 같은 깊이의 stdout/dry-run direct-caller pinning이 필요한지는 다음 라운드에서 판단할 문제로 남아 있습니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, README 두 섹션 중복 정리, helper stdout 포맷 규약 문서화 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 `prune_smoke_dirs`의 `protect_tracked=1` 경로 직접 stdout/dry-run pinning, 또는 manual cleanup README 두 섹션 중복 정리가 남아 있습니다.
