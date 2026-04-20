# 2026-04-18 manual smoke-cleanup helper invalid-input no-op 계약 pinning

## 변경 파일
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-manual-cleanup-invalid-input-error-pinning.md`와 그 verify(`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`)가 `.pipeline/cleanup-old-smoke-dirs.sh` script-level invalid-input 에러 계약(exit 1 + stderr + stdout 빈 상태 + 디렉터리 보존)을 focused regression으로 닫았습니다.
- 같은 manual cleanup 경계에서 아직 regression으로 좁게 고정돼 있지 않은 다음 current-risk는 shared helper 쪽, 즉 `.pipeline/smoke-cleanup-lib.sh`의 `prune_manual_smoke_dirs`가 non-empty지만 `^[0-9]+$`에 맞지 않는 invalid `keep_recent` 입력을 조용한 no-op(`return 0`)으로 다루는 direct-caller 계약입니다. blocked/live-arb wrapper는 각각 `test_blocked_auto_triage_caller_noop_when_keep_recent_invalid`, `test_live_arb_caller_noop_when_keep_recent_invalid`로 동일한 경계를 이미 잠갔지만, manual wrapper는 helper 직접 호출 경로를 잠그는 대칭 regression이 빠져 있었습니다.
- 이번 slice는 그 helper-level 대칭 하나만 regression으로 pin down하고, script-level invalid-input 에러 계약과 기존 모든 receipt 분기는 그대로 둡니다. scope는 manual smoke cleanup helper/script/docs/tests 경계 안으로 제한합니다.

## 핵심 변경
- `tests/test_pipeline_smoke_cleanup.py`에 `test_manual_cleanup_caller_noop_when_keep_recent_invalid`를 추가했습니다. `live-arb-smoke-one`, `live-arb-smoke-two` 두 디렉터리를 둔 임시 repo에서 helper를 `bash -c "... prune_manual_smoke_dirs <root>/.pipeline live-arb-smoke-* <bad> 0"`으로 직접 호출하는 subTest 루프를 돕니다. `<bad>` 값은 `"abc"`, `"-1"`, `"1.5"` 세 가지로, 각각 non-integer string / 음수 / 소수점을 대표합니다.
- 각 subTest에서 아래 네 가지를 assert합니다.
  - `returncode == 0` (invalid non-empty 입력은 silent no-op이며 에러 exit로 올라가지 않는다)
  - stdout에 `KEEP ` / `PROTECT ` / `DELETE ` substring이 없다 (파괴적 helper 경로로 흘러가지 않았다)
  - 두 smoke 디렉터리가 그대로 남는다
- 루프 구조와 assertion 세트는 blocked/live-arb wrapper invalid-input regression과 거의 대칭이고, 주석으로 "helper refactor가 invalid 입력을 조용히 destructive delete로 바꾸지 못하도록 manual wrapper 경계를 잠근다"는 목적을 남겼습니다. `""` 빈 문자열은 기존 `test_manual_cleanup_caller_noop_when_keep_recent_is_zero`/`test_manual_cleanup_script_keep_recent_zero_preserves_dirs`와 중복이 되고, `.pipeline/cleanup-old-smoke-dirs.sh`의 `${PIPELINE_SMOKE_KEEP_RECENT:-3}` 기본값 fallback과도 겹치므로 이번 helper-level 테스트 scope에서는 뺐습니다.
- `.pipeline/smoke-cleanup-lib.sh`와 `.pipeline/cleanup-old-smoke-dirs.sh`는 이번 라운드에서 코드로 수정하지 않았습니다. helper는 invalid non-empty 입력에 대해 이미 `! [[ "$keep_recent" =~ ^[0-9]+$ ]]` 가드로 `return 0`하고 있고, script는 직전 라운드에서 `exit 1` + stderr 에러 계약을 따로 잠갔기 때문에, 두 경계가 서로 다른 의미로 일관된 상태입니다. helper와 script가 같은 invalid 입력을 서로 다른 방식으로 다루는 이유(helper는 library-level defensive guard, script는 operator-facing error)는 기존 코드 그대로 유지했습니다.
- `.pipeline/README.md`도 이번 라운드에서 수정하지 않았습니다. 현재 README는 `PIPELINE_SMOKE_KEEP_RECENT=0` fail-safe와 explicit disabled-cleanup receipt만 명시하고, helper/script invalid-input 분기는 내부 구현 계약이라 docs-only 재명시 없이도 truthful하게 읽힙니다. helper/script 두 계약이 서로 어긋나지 않는 한 README에 다시 적는 것은 handoff가 금지한 "README dedupe-only cleanup"으로 흘러가므로 피했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 22 tests`, `OK`. 신규 `test_manual_cleanup_caller_noop_when_keep_recent_invalid` 한 건(subTest 3개 포함)이 현재 tree에서 실제로 녹색이며, 기존 21건(blocked/live-arb/manual non-delete receipt/zero-receipt/script invalid error/fail-closed)은 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0.
- 임시 git repo에서 focused direct-helper rerun을 실행했습니다. `.pipeline/live-arb-smoke-one`, `.pipeline/live-arb-smoke-two` 두 디렉터리를 두고 `bash -c ". $tmpdir/.pipeline/smoke-cleanup-lib.sh; prune_manual_smoke_dirs $tmpdir/.pipeline live-arb-smoke-* <bad> 0"`를 `abc`, `-1`, `1.5` 세 값에 대해 연속 실행했을 때 세 번 모두 exit 0, stdout에 `KEEP `/`PROTECT `/`DELETE ` 없음, 그리고 두 디렉터리가 그대로 남는 것을 직접 확인했습니다.
- broader tmux live smoke, runtime/controller/browser 검증은 이번 라운드에서 다시 돌리지 않았습니다. 이번 변경은 manual cleanup helper의 invalid-input no-op 계약만 좁게 잠그는 same-family current-risk reduction이고 shipped browser contract / tmux dispatch / runtime state writer 계약을 넓히지 않았기 때문입니다.

## 남은 리스크
- 이번 라운드 시작 시점에 `.pipeline/README.md`, `.pipeline/cleanup-old-smoke-dirs.sh`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 이미 이전 라운드들 dirty edits를 들고 있는 modified 상태였습니다. 이번 라운드에서 새로 편집한 파일은 `tests/test_pipeline_smoke_cleanup.py` 하나뿐이며, 나머지 세 파일은 이전 라운드 상태 그대로 유지했습니다. unrelated untracked `tmp/`와 이전 `/work` closeouts도 이번 라운드에서 건드리지 않았습니다.
- helper가 invalid 입력에서 silent no-op으로 동작하는 것과 script가 같은 입력에서 stderr + exit 1로 동작하는 계약은 의도적으로 다릅니다. 이 비대칭을 좁히려면 helper, script, README, 세 regression 묶음을 한 라운드에서 같이 수정해야 합니다. 이번 scope는 그 비대칭을 문서화/변경하지 않고 현재 상태 그대로 잠갔을 뿐입니다.
- 빈 문자열 `""`은 이번 helper-level 테스트 scope에서는 빠져 있습니다. 기존 `test_manual_cleanup_caller_noop_when_keep_recent_is_zero`와 script 쪽 `${PIPELINE_SMOKE_KEEP_RECENT:-3}` 기본값 경로가 이미 다른 각도에서 커버하지만, 빈 문자열이 helper에 직접 전달되는 경우(script 외부의 future caller)를 정말로 잠그고 싶다면 별도 테스트 또는 helper 가드 문구 정리가 필요합니다.
- archive policy, fixture 재배치, tracked-state 정리, 다른 smoke family wrapper 경계, tmux live smoke 재실행, README 수동 cleanup 섹션과 `smoke 디렉터리 정리 규약` 섹션 중복 정리, helper stdout 진단 strict pinning 같은 주제는 여전히 이번 scope 밖입니다. 다음 same-family current-risk 후보로는 helper empty-string 입력 regression, `prune_manual_smoke_dirs`의 `smoke_root` 또는 `pattern` 비어있는 경로 no-op regression, README 두 섹션 중복 정리가 남아 있습니다.
