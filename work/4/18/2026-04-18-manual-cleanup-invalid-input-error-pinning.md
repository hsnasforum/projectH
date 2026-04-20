# 2026-04-18 manual smoke-cleanup invalid-input 에러 계약 pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-manual-cleanup-non-delete-receipt-pinning.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 `.pipeline/cleanup-old-smoke-dirs.sh`의 두 non-delete receipt 분기(`Nothing to clean.`, `No <pattern> directories found under <smoke_root>`)를 focused regression으로 닫았습니다.
- 같은 script 경계에서 아직 regression으로 좁게 고정돼 있지 않은 마지막 operator-facing 분기는 invalid `PIPELINE_SMOKE_KEEP_RECENT` 에러 계약입니다. script는 현재 `PIPELINE_SMOKE_KEEP_RECENT must be a non-negative integer`를 stderr로 찍고 exit 1로 끝나지만, 이 정확한 계약(exit code, stdout 빈 상태, stderr 문구, matching 디렉터리 보존)을 테스트가 잠가 두지 않아 누군가 문구/흐름을 조용히 바꾸면 조용히 drift할 수 있습니다.
- 이번 slice는 그 에러 분기 하나만 regression으로 pin down하고, 기존 helper boundary와 모든 receipt 분기는 그대로 둡니다. scope는 manual smoke cleanup script/docs/tests 경계 안으로 제한합니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 `test_manual_cleanup_script_rejects_invalid_keep_recent`를 추가했습니다. `live-arb-smoke-1`, `live-arb-smoke-2` 두 디렉터리를 둔 임시 repo에서 `PIPELINE_SMOKE_PATTERN='live-arb-smoke-*'`, `PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`으로 고정하고 `PIPELINE_SMOKE_KEEP_RECENT`을 `abc`, `-1`, `1.5` 세 가지 invalid value로 돌리는 subTest 루프를 돌립니다. 각 실행에서 아래 네 가지를 assert합니다.
  - `returncode == 1`
  - `stdout == ""` (에러 분기는 operator receipt 한 줄도 남기지 않는다)
  - `stderr`에 `PIPELINE_SMOKE_KEEP_RECENT must be a non-negative integer` substring이 그대로 있다
  - 두 smoke 디렉터리는 그대로 남아 있다
- subTest 루프 주석으로, 빈 문자열(`""`)은 script 상단의 `KEEP_RECENT="${PIPELINE_SMOKE_KEEP_RECENT:-3}"` 기본값 때문에 이 에러 분기에 도달하지 못한다는 점을 같이 남겨 두었습니다. 그래서 이 테스트는 "non-empty but not a non-negative integer" 영역만 좁게 고정하며, 다른 분기(기본값 fallback, fail-safe no-op, destructive helper)와 경계가 섞이지 않습니다.
- `.pipeline/cleanup-old-smoke-dirs.sh`와 `.pipeline/smoke-cleanup-lib.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. invalid-input 에러 분기 문구/흐름은 기존과 동일하며, 이번 라운드는 해당 stderr+exit 계약을 regression으로 좁게 pin down한 것이 전부입니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. 현재 README는 `PIPELINE_SMOKE_KEEP_RECENT=0` fail-safe와 explicit receipt 한 줄을 설명하고, "non-negative integer" 에러 경로는 이미 스크립트 상단에 명시돼 있어 문서 추가 없이도 truthful하게 읽힙니다. invalid-input 문구를 README에 다시 싣는 것은 docs dedupe 성격으로 scope가 넓어지므로 피했습니다. 이 판단은 handoff의 "Update ... only if needed" 조건 + scope-limits의 "do not widen into README dedupe-only cleanup"을 동시에 만족합니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 21 tests`, `OK`. 신규 `test_manual_cleanup_script_rejects_invalid_keep_recent` 한 건(subTest 3개 포함)이 현재 tree에서 실제로 녹색이며, 기존 20건(blocked/live-arb/manual non-delete receipt/zero-receipt/fail-closed)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 invalid-input focused rerun을 실행했습니다. `.pipeline/live-arb-smoke-1~2`와 `PIPELINE_SMOKE_PATTERN='live-arb-smoke-*'`, `PIPELINE_SMOKE_KEEP_RECENT=abc`, `PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`으로 script를 실행했을 때 exit 1, stdout 빈 상태, stderr `PIPELINE_SMOKE_KEEP_RECENT must be a non-negative integer`, 그리고 두 디렉터리 보존까지 handoff가 요구한 네 계약이 실제로 관찰됐습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 manual cleanup script의 invalid-input 에러 계약만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- 새 테스트는 stderr 문구를 substring으로 assert합니다. 문구를 바꾸려면 이 regression과, 이번 라운드에서 일부러 손대지 않은 `.pipeline/README.md`에서 에러 계약을 같이 문서화하는 결정을 한 라운드에서 같이 처리해야 drift가 조용히 들어오지 않습니다.
- 빈 문자열 `""` 입력은 script가 기본값 `3`으로 대체하기 때문에 이 에러 분기에 도달하지 못합니다. "empty string은 반드시 실패해야 한다"로 계약을 바꾸고 싶다면 script + test + README가 같이 움직여야 하며, 이번 scope 밖입니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, README 수동 cleanup 섹션과 `smoke 디렉터리 정리 규약` 섹션 중복 정리, helper-level invalid-input 계약 pinning 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 helper-level invalid-input 진단(지금은 조용히 `return 0`) regression, manual cleanup stdout header 포맷 strict pinning, 또는 README 두 섹션 중복 정리가 남아 있습니다.
