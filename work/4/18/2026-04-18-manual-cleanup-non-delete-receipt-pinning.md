# 2026-04-18 manual smoke-cleanup non-delete receipt 분기 pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-manual-cleanup-keep-recent-zero-receipt.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 `PIPELINE_SMOKE_KEEP_RECENT=0` disabled-cleanup receipt 경로를 focused regression과 함께 닫았습니다.
- 같은 manual cleanup 경계 안에서 남아 있던 가장 작은 current-risk는 `.pipeline/cleanup-old-smoke-dirs.sh`의 다른 두 non-delete 분기(`No <pattern> directories found under <smoke_root>` / `Nothing to clean.`)가 실제 operator-facing receipt인데도 focused regression으로 고정돼 있지 않아, 누군가 이 stdout 문구를 조용히 바꾸거나 destructive helper 경로로 흘려도 테스트가 잡지 못한다는 점이었습니다.
- 이번 slice는 그 두 분기의 stdout 계약을 script 단에서 pin down하고, `PIPELINE_SMOKE_KEEP_RECENT=0` receipt 경로와 helper-level `prune_manual_smoke_dirs` 계약은 그대로 둡니다. scope는 manual smoke cleanup script/docs/tests 경계 안으로 제한합니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 두 개의 script-level regression을 추가했습니다.
  - `test_manual_cleanup_script_no_matching_dirs_receipt`: 임시 repo에 `.pipeline/unrelated-workspace` 하나만 두고 `PIPELINE_SMOKE_PATTERN='live-arb-smoke-*'`, `PIPELINE_SMOKE_KEEP_RECENT=3`, `PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`으로 script를 실행합니다. stdout에 `No live-arb-smoke-* directories found under <smoke_root>` receipt가 정확히 나오는지, 그리고 `DELETE `/`PROTECT `/`KEEP `/`Nothing to clean.`/`Cleanup disabled` 같은 다른 경로의 문구가 섞이지 않는지를 함께 확인합니다. 무관한 directory(`unrelated-workspace`)가 삭제되지 않는지도 같이 assert합니다.
  - `test_manual_cleanup_script_nothing_to_clean_receipt`: `.pipeline/live-arb-smoke-1`, `live-arb-smoke-2` 두 개를 두고 `PIPELINE_SMOKE_KEEP_RECENT=3`(키프 윈도우 > 발견 수)으로 실행해 `Nothing to clean.` 분기에 진입시킵니다. stdout에 `Smoke root: ...`, `Pattern: live-arb-smoke-*`, `Found: 2`, `Keep recent: 3`, `Nothing to clean.`이 같이 찍히는지, 그리고 destructive helper 경로(`DELETE `/`PROTECT `/`KEEP `)와 `Cleanup disabled` 문구는 섞이지 않는지, 두 디렉터리가 모두 그대로 남는지를 확인합니다.
- `.pipeline/cleanup-old-smoke-dirs.sh`와 `.pipeline/smoke-cleanup-lib.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. 두 non-delete 분기의 문구/동작은 기존과 동일하며, 이번 라운드는 해당 stdout 계약을 regression으로 좁게 pin down한 것이 전부입니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. README는 `PIPELINE_SMOKE_KEEP_RECENT=0` receipt 계약을 이미 직전 라운드에서 명시했고, 이번 라운드는 동작을 바꾸지 않는 pin-down이라 문서 truth가 추가로 drift하지 않습니다. 기존 `smoke 디렉터리 정리 규약` 섹션에서 두 non-delete 분기 문구를 중복 재명시하면 docs-only dedupe 작업으로 넘어가 scope를 넘게 되어 피했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 20 tests`, `OK`. 신규 `test_manual_cleanup_script_no_matching_dirs_receipt`, `test_manual_cleanup_script_nothing_to_clean_receipt` 두 건이 현재 tree에서 실제로 녹색이며, 기존 18건(블로크드/라이브-아브/매뉴얼/zero-receipt/fail-closed)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 `Nothing to clean.` focused rerun을 실행했습니다. `.pipeline/live-arb-smoke-1`, `live-arb-smoke-2`와 `PIPELINE_SMOKE_KEEP_RECENT=3`으로 실행한 stdout에 `Smoke root: ...`, `Pattern: live-arb-smoke-*`, `Found: 2`, `Keep recent: 3`, `Dry run: 0`, `Nothing to clean.`이 순서대로 찍혔고 두 디렉터리는 그대로 남았습니다.
- 같은 임시 repo에서 `No <pattern> directories found under <smoke_root>` focused rerun도 같이 실행했습니다. `.pipeline/unrelated-workspace`만 있고 `live-arb-smoke-*`는 없는 상태에서 stdout에 `No live-arb-smoke-* directories found under <tmpdir>/.pipeline`이 찍히고 helper-level 경로로 내려가지 않았습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 manual cleanup script stdout 계약을 regression으로 좁히는 same-family current-risk reduction이며 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`, 직전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- 새 두 테스트는 stdout 문구를 substring으로 assert합니다. 문구를 바꾸려면 regression과 `.pipeline/README.md`를 한 라운드에서 같이 수정해야 하며, 이는 기존 `Cleanup disabled` receipt와 같은 운영 원칙입니다.
- `test_manual_cleanup_script_no_matching_dirs_receipt`는 `find ... -name live-arb-smoke-*`가 매칭하지 않는다는 전제 위에 `unrelated-workspace`만 seed합니다. 다른 smoke pattern이 `.pipeline/` 최상단에 같이 생기는 환경에서 이 script가 어떻게 굴러야 하는지는 이번 scope 밖입니다. 필요하면 다음 라운드에서 별도로 다뤄야 합니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, README 수동 cleanup/`smoke 디렉터리 정리 규약` 섹션 중복 정리 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family risk 후보로는 README의 두 섹션 중복 정리, `prune_smoke_dirs` enumeration 경로가 non-directory match를 어떻게 다루는지 regression, 또는 helper stdout 진단 포맷 자체를 strict하게 잡는 테스트 정도가 남아 있습니다.
