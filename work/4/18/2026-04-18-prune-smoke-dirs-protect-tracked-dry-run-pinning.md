# 2026-04-18 `prune_smoke_dirs` protected 경로 dry-run stdout 계약 pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-prune-smoke-dirs-live-arb-stdout-dry-run-pinning.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 shared helper `prune_smoke_dirs`의 live-arb-style 비보호(`protect_tracked=0`) 경로 stdout/dry-run 계약을 direct-caller regression으로 잠갔습니다.
- 같은 smoke-cleanup helper 경계에서 아직 regression으로 좁게 고정돼 있지 않은 현재 current-risk는 대칭되는 protected 경로입니다. `prune_smoke_dirs(... protect_tracked=1, dry_run=1 ...)`는 manual cleanup script regression(`test_manual_cleanup_script_protects_tracked_under_pattern_override`)에서 결과 기반으로 대부분 커버되지만, shared helper 자체에 대해 `PROTECT` + `KEEP` + `DELETE` 세 verb와 non-destructive dry-run 동작을 한 장소에서 같이 잠그는 direct-caller 테스트는 없었습니다.
- 이번 slice는 그 한 contract만 direct-caller regression으로 pin down하고, helper 동작과 manual/live-arb wrapper 계약은 그대로 둡니다. scope는 `.pipeline/smoke-cleanup-lib.sh` + `.pipeline/README.md` + `tests/test_pipeline_smoke_cleanup.py` 안으로 제한합니다. 이번 slice는 test-only 라운드입니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 `test_prune_smoke_dirs_protect_tracked_dry_run_emits_all_three_verbs`를 추가했습니다. 임시 repo에 세 디렉터리를 mtime 오름차순으로 준비합니다.
  - `live-blocked-smoke-TRACKED`(mtime 100) — `_commit_tracked`로 실제 git tracked entry로 등록.
  - `live-blocked-smoke-older`(mtime 200) — untracked generated.
  - `live-blocked-smoke-newest`(mtime 300) — untracked generated.
- 그 상태에서 기존 `_call_prune(root, "live-blocked-smoke-*", keep_recent=1, protect_tracked=1, dry_run=1)`을 실행하고 아래를 assert합니다.
  - stdout에 `KEEP <newest_untracked>` / `PROTECT <tracked>` / `DELETE <older_untracked>` 세 verb가 한 번에 보인다.
  - `dry_run=1`이므로 세 디렉터리가 모두 디스크에 남는다. `DELETE` 줄이 찍혔어도 실제 삭제는 일어나지 않는다.
- 테스트 주석으로 세 verb가 각각 어떤 분기에서 유래하는지(`KEEP` = newest-first window, `PROTECT` = protect_tracked=1 + git-tracked 경로, `DELETE` = dry-run plan)와 "dry-run은 plan만 찍는다"는 helper 계약을 명시했습니다.
- `.pipeline/smoke-cleanup-lib.sh`와 `.pipeline/cleanup-old-smoke-dirs.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. `prune_smoke_dirs` protected dry-run 경로 동작은 기존과 동일하며, 이번 라운드는 그 stdout/dry-run 계약을 direct-caller regression 하나로 좁게 pin down한 것이 전부입니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. `smoke 디렉터리 정리 규약` 섹션이 이미 `protect_tracked=1` 분기와 `dry_run=1` plan-only 동작을 명시적으로 설명하고 있어 이번에 잠근 contract와 일치합니다. 같은 문구를 다시 추가하는 것은 handoff scope-limits가 금지한 docs-only dedupe으로 흘러가므로 피했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 26 tests`, `OK`. 신규 `test_prune_smoke_dirs_protect_tracked_dry_run_emits_all_three_verbs` 한 건이 현재 tree에서 실제로 녹색이며, 기존 25건(blocked/live-arb/manual/zero-receipt/script invalid error/helper invalid input/early-return guards/live-arb direct stdout/fail-closed)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 handoff가 요구한 direct-helper rerun을 실행했습니다. `live-blocked-smoke-TRACKED`를 git tracked로 commit한 뒤 mtime을 100/200/300으로 고정하고 `bash -c ". <tmpdir>/.pipeline/smoke-cleanup-lib.sh; prune_smoke_dirs <tmpdir>/.pipeline live-blocked-smoke-* 1 1 1"`을 실행했을 때 stdout에 `KEEP <newest>` / `DELETE <older>` / `PROTECT <tracked>`가 순서대로 찍혔고 세 디렉터리 모두 dry-run 이후에도 그대로 남아 있음을 확인했습니다. 결과는 새 테스트가 기대하는 동작과 정확히 일치합니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 shared helper `prune_smoke_dirs`의 protected 경로 stdout/dry-run 계약만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- 새 테스트는 stdout substring assertion으로 `KEEP <path>` / `PROTECT <path>` / `DELETE <path>` 세 verb를 잠급니다. 진단 포맷을 바꾸고 싶다면 이 테스트와 직전 라운드의 live-arb direct-caller regression, manual/live-arb/blocked wrapper regression, 그리고 `.pipeline/README.md` `smoke 디렉터리 정리 규약` 문구까지 한 라운드에서 같이 움직여야 drift를 피할 수 있습니다.
- 이번 slice는 `protect_tracked=1` + `dry_run=1` 조합만 direct-caller로 잠갔습니다. `protect_tracked=1` + `dry_run=0` 실 삭제 경로에서의 direct-caller stdout + 실제 삭제 결과는 `test_blocked_smoke_protects_tracked_fixture_dir`에서 이미 커버되므로 이번 라운드는 거기로 중복을 옮기지 않았습니다. 다만 dry-run/live의 두 경로를 하나의 direct-caller 테스트로 묶어 엄격하게 잠그고 싶다면, 두 테스트를 하나의 parametrized 구조로 정리하는 리팩터링이 남아 있는 선택지입니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, README 수동 cleanup 섹션과 `smoke 디렉터리 정리 규약` 섹션 중복 정리, helper stdout 포맷 규약 문서화 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 `prune_smoke_dirs` enumeration이 non-directory match를 어떻게 다루는지 regression, `_smoke_enumerate_dirs` sort 안정성 direct pinning, 또는 manual cleanup README 두 섹션 중복 정리가 남아 있습니다.
