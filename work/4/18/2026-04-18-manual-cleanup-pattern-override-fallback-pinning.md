# 2026-04-18 manual cleanup PIPELINE_SMOKE_PATTERN 입력 계약 pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-manual-cleanup-blocked-pattern-non-destructive-receipts-pinning.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 `.pipeline/cleanup-old-smoke-dirs.sh`의 blocked-pattern 하에서의 `Cleanup disabled` / `Nothing to clean.` / `No <pattern> directories found` 세 non-destructive receipt 분기를 regression으로 잠갔습니다.
- 같은 manual script 경계에서 아직 regression으로 좁게 고정돼 있지 않은 current-risk는 `PIPELINE_SMOKE_PATTERN` 입력 계약이었습니다. probe로 확인된 현재 동작은 다음과 같습니다.
  - `PIPELINE_SMOKE_PATTERN=''`(빈 override)은 script 상단 `${PIPELINE_SMOKE_PATTERN:-live-arb-smoke-*}` fallback으로 흘러 live-arb 디렉터리만 타겟팅하고, live-blocked sibling은 건드리지 않는다.
  - malformed-but-shell-safe 패턴(예: `live-blocked-smoke[`)은 find가 매칭에 실패하므로 정확히 `No live-blocked-smoke[ directories found under <root>/.pipeline` receipt 한 줄만 남기고 header block이나 어떤 디렉터리도 건드리지 않는다.
  두 경로 모두 operator-visible current contract이지만 repo-level regression이 없어 refactor가 fallback 또는 malformed 경로 동작을 조용히 바꿀 수 있는 상태였습니다.
- 이번 slice는 그 두 입력 계약만 regression으로 잠그고, helper/script 동작은 그대로 둡니다. scope는 `.pipeline/cleanup-old-smoke-dirs.sh` + `.pipeline/README.md` + `tests/test_pipeline_smoke_cleanup.py` 안으로 제한합니다. 이번 라운드는 test-only 라운드입니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 두 테스트를 추가했습니다.
  - `test_manual_cleanup_script_empty_pattern_falls_back_to_live_arb`: 임시 repo에 `live-arb-smoke-old one`(mtime 100), `live-arb-smoke-new two`(mtime 300), `live-blocked-smoke-TRACKED one`(mtime 200) 세 공백 포함 디렉터리를 두고, `.pipeline/cleanup-old-smoke-dirs.sh`를 `PIPELINE_SMOKE_PATTERN=''`, `PIPELINE_SMOKE_KEEP_RECENT=1`, `PIPELINE_SMOKE_CLEANUP_DRY_RUN=1`로 실행합니다. assertion은 (a) stdout header에 `Pattern: live-arb-smoke-*`와 `Found: 2`가 찍히는지, (b) `KEEP <arb_newer>` / `DELETE <arb_older>` 진단에 live-arb 두 경로만 실리는지, (c) stdout에 `live-blocked-smoke` substring이 절대 섞이지 않는지, (d) dry-run이라 세 디렉터리 전부 디스크에 그대로 남는지를 확인합니다. 이 테스트는 "빈 override는 blank pattern이 아니라 live-arb fallback으로 흘러간다"는 계약을 한 곳에서 잠급니다.
  - `test_manual_cleanup_script_malformed_pattern_no_match_receipt`: `live-blocked-smoke-TRACKED one`(tracked)와 `live-arb-smoke-new two`(untracked) 두 디렉터리를 둔 임시 repo에서 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke['`, `PIPELINE_SMOKE_KEEP_RECENT=1`, `PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`으로 script를 실행합니다. assertion은 (a) stdout에 `No live-blocked-smoke[ directories found under <smoke_root>` 한 줄이 정확히 보이는지, (b) header block(`Smoke root:`, `Pattern:`, `Found:`, `Keep recent:`, `Dry run:`)과 `Nothing to clean.` / `Cleanup disabled` / `KEEP `/`PROTECT `/`DELETE ` 진단이 모두 섞이지 않는지, (c) 두 기존 디렉터리가 전부 보존되는지를 확인합니다. malformed pattern도 live run에서 파괴적으로 동작하지 않는다는 계약까지 한 테스트 안에서 잠급니다.
- `.pipeline/smoke-cleanup-lib.sh`, `.pipeline/cleanup-old-smoke-dirs.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. 두 입력 경로 동작은 이전 라운드들에서 이미 그대로였으며, 이번 라운드는 input-contract를 regression으로 좁게 잠근 것이 전부입니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. 현재 README 수동 cleanup 블록은 `PIPELINE_SMOKE_PATTERN=...`로 다른 generated pattern을 override할 수 있다고만 명시하며, 빈 override / malformed 값의 구체적인 fallback 동작을 문서화하지 않은 상태입니다. 이 두 경로를 새로 문서화하는 것은 operator-visible behavior document 추가에 해당하며 handoff scope-limits의 "broader docs cleanup 금지"와 충돌할 여지가 있어, 이번 라운드에서는 현재 docs truth를 그대로 유지하고 regression으로만 계약을 잠갔습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 36 tests`, `OK`. 신규 `test_manual_cleanup_script_empty_pattern_falls_back_to_live_arb`, `test_manual_cleanup_script_malformed_pattern_no_match_receipt` 두 건이 현재 tree에서 실제로 녹색이며, 기존 34건(manual/live-arb/blocked wrapper, script receipts, helper guards, direct-caller stdout pinning, space-path helper fix, live-arb 및 blocked caller space propagation, blocked-pattern non-destructive receipts 등)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 handoff가 요구한 focused rerun 두 건을 실행했습니다.
  - 빈 override: `PIPELINE_SMOKE_PATTERN='' PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir"` → stdout header에 `Pattern: live-arb-smoke-*`, `Found: 2`가 찍히고 `KEEP <tmpdir>/.pipeline/live-arb-smoke-new two`, `DELETE <tmpdir>/.pipeline/live-arb-smoke-old one`만 출력됐습니다. `live-blocked-smoke-TRACKED one`은 stdout에도, 디스크에도 영향을 받지 않았습니다.
  - malformed: `PIPELINE_SMOKE_PATTERN='live-blocked-smoke[' PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=0 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir"` → stdout에는 `No live-blocked-smoke[ directories found under <tmpdir>/.pipeline` 한 줄만 남고 header block / destructive diagnostic은 전혀 찍히지 않았으며, 두 기존 디렉터리(`live-blocked-smoke-TRACKED one`, `live-arb-smoke-new two`)는 모두 보존됐습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 manual cleanup script의 `PIPELINE_SMOKE_PATTERN` 입력 계약만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- 두 신규 테스트는 stdout substring assertion으로 계약을 잠급니다. "빈 override → live-arb fallback" 또는 "malformed pattern → no-match receipt" 계약을 바꾸고 싶다면 이 두 테스트, 기존 manual/live-arb/blocked regression 전체, 그리고 `.pipeline/README.md` 수동 cleanup 블록을 한 라운드에서 같이 수정해야 drift 없이 움직일 수 있습니다.
- malformed pattern regression은 `live-blocked-smoke[` 한 예시만 잠급니다. 다른 malformed 입력(예: `*[`, `live-arb-smoke-` 같은 실제 존재하는 prefix)은 script/helper 동작이 다를 수 있고, 이번 scope 밖입니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, helper stdout 포맷 규약 문서화, README 수동 cleanup 섹션과 `smoke 디렉터리 정리 규약` 섹션 중복 정리 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 manual cleanup script의 invalid PROJECT_ROOT 인자 계약 regression, README 두 섹션 중복 정리, 혹은 `_smoke_enumerate_dirs` 탭/개행 path-safety 확장이 남아 있습니다.
