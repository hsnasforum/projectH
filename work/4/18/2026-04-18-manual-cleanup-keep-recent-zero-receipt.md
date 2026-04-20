# 2026-04-18 manual smoke-cleanup `KEEP_RECENT=0` explicit no-op receipt

## 변경 파일
- `.pipeline/cleanup-old-smoke-dirs.sh`
- `.pipeline/README.md`
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)는 `prune_manual_smoke_dirs`의 `keep_recent <= 0` fail-safe로 삭제 위험 자체는 닫았습니다.
- 그러나 verify 쪽이 직접 남은 current-risk로 남긴 점은, `.pipeline/cleanup-old-smoke-dirs.sh`가 `PIPELINE_SMOKE_KEEP_RECENT=0` 경로에서 header block만 찍고 `prune_manual_smoke_dirs`가 조용히 return하여 operator가 "cleanup이 disabled 상태"와 "helper가 조용히 반환"을 stdout만 보고 구분하기 어렵다는 것이었습니다.
- 이번 slice는 manual cleanup script/docs/tests 경계 안에서 그 operator-facing receipt를 명시적으로 한 줄로 surface하고, 관련 README 설명을 현재 동작에 맞추는 것이 목적입니다. scope는 tracked-state cleanup, archive policy, 다른 smoke family로 넓히지 않았습니다.

## 핵심 변경
- `.pipeline/cleanup-old-smoke-dirs.sh`에 `KEEP_RECENT <= 0` 전용 early-exit 분기를 header block 직후, 기존 "Nothing to clean." 분기 앞에 추가했습니다. 이 분기는 `Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0, preserving all matching <PATTERN> directories.` 한 줄을 stdout으로 찍고 `exit 0`합니다. `<PATTERN>`은 `PIPELINE_SMOKE_PATTERN` override까지 그대로 drive하므로, 예를 들어 `live-blocked-smoke-*` override를 걸어도 실제로 건너뛴 pattern이 그대로 receipt에 드러납니다. helper의 fail-safe 경계와 README 계약을 따른다는 이유를 주석으로 같이 남겼습니다.
- 기존 `prune_manual_smoke_dirs` 호출은 그대로 유지해, 유효한 양수 `KEEP_RECENT` 입력은 이전과 동일하게 `KEEP/PROTECT/DELETE` 진단이 찍히는 helper 계약으로 흘러갑니다. "Nothing to clean." 분기와 enumeration 빈 경우의 조기 종료도 건드리지 않았습니다.
- `tests/test_pipeline_smoke_cleanup.py`의 `test_manual_cleanup_script_keep_recent_zero_preserves_dirs`를 확장해 script stdout을 capture하고 `Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0` 문구와 `live-arb-smoke-*` pattern이 실제 receipt로 보이는지, 그리고 disabled 상태에서는 `KEEP ` / `PROTECT ` / `DELETE ` 파괴적 진단이 나오지 않는지를 같이 assert하도록 고정했습니다. 기존 "세 디렉터리 보존" assertion은 그대로 남겼습니다.
- 다른 tests(helper 경로 `test_manual_cleanup_caller_noop_when_keep_recent_is_zero`, pattern override 보호, dry-run, 삭제 보장 등)는 그대로 통과하며, script 경계가 아닌 helper 경로 계약은 이번 라운드에서 변경하지 않았습니다.
- `.pipeline/README.md`의 수동 cleanup 블록에, `PIPELINE_SMOKE_KEEP_RECENT=0` 경로에서 script가 `Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0, preserving all matching <pattern> directories.` 한 줄을 stdout에 남긴다는 문장을 추가했습니다. 기존 fail-safe no-op 문장은 그대로 유지해, helper 계약과 script 계약이 같은 섹션에서 같이 읽히도록 했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 18 tests`, `OK`. 이번에 바뀐 `test_manual_cleanup_script_keep_recent_zero_preserves_dirs`를 포함한 manual path 전체와 기존 blocked/live-arb/fail-closed regression이 모두 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 handoff가 요구한 focused rerun을 실제로 돌렸습니다. `tmpdir`에 `.pipeline/smoke-cleanup-lib.sh`, `.pipeline/cleanup-old-smoke-dirs.sh`, `live-arb-smoke-1~3` 디렉터리를 준비하고 `PIPELINE_SMOKE_PATTERN='live-arb-smoke-*' PIPELINE_SMOKE_KEEP_RECENT=0 PIPELINE_SMOKE_CLEANUP_DRY_RUN=0 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir"`를 실행했을 때, stdout에는 header block 뒤에 `Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0, preserving all matching live-arb-smoke-* directories.`가 실제로 찍혔고 `live-arb-smoke-1~3` 디렉터리는 전부 그대로 남았습니다.
- broader tmux 기반 live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 manual cleanup script/docs/tests 경계 안의 operator-facing stdout 계약만 좁혔고, shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- `Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0, preserving all matching <pattern> directories.` 문구는 operator-facing 약속입니다. 문구를 바꾸려면 README 문장과 regression assertion을 한 라운드에서 같이 수정해야 합니다.
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드 fail-safe slice의 dirty edits를 들고 있는 modified 상태였습니다. `.pipeline/cleanup-old-smoke-dirs.sh`는 이번 라운드에서 처음 수정된 modified 상태이고, 네 파일 모두 현재 `git status`에서 tracked modified로 보입니다. 이전 `/work`가 일부 파일을 untracked로 적었던 설명은 현재 repo truth와 다르며, 이 메모가 그 차이를 truthful하게 남깁니다. unrelated untracked `tmp/`는 이번 라운드에서도 그대로 두었습니다.
- script에 새로 추가한 early-exit는 `KEEP_RECENT <= 0`만 잡습니다. 유효한 양수 `KEEP_RECENT`에 대한 "Nothing to clean." / KEEP/PROTECT/DELETE diagnostics는 기존 helper 경로를 그대로 탑니다. 이 대칭을 깨려면 helper와 script를 같은 라운드에서 함께 수정해야 합니다.
- tracked-state 정리, archive policy, fixture 재배치, 다른 smoke family wrapper 경계, tmux live smoke 재실행, `smoke-cleanup-lib.sh` owner rename 같은 topic은 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 manual cleanup script의 `-le` 분기/enumeration empty 분기 stdout 계약 회귀나 `.pipeline/README.md`의 수동 cleanup 섹션과 `smoke 디렉터리 정리 규약` 섹션 간 중복 정리 정도가 남아 있습니다.
