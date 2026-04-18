# 2026-04-18 live-arb auto-prune caller, shared wrapper + focused regression

## 변경 파일
- `.pipeline/smoke-cleanup-lib.sh`
- `.pipeline/smoke-three-agent-arbitration.sh`
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- superpowers:using-superpowers
- superpowers:test-driven-development

## 변경 이유
- 직전 라운드(`work/4/18/2026-04-18-blocked-auto-triage-caller-focused-regression.md`)와 그 verify는 `.pipeline/smoke-implement-blocked-auto-triage.sh`의 auto-prune caller를 shared `prune_blocked_smoke_dirs` helper로 올려 focused regression으로 덮었습니다.
- 같은 smoke-cleanup family 안에 남아 있던 가장 좁은 sibling 위험은 `.pipeline/smoke-three-agent-arbitration.sh`의 live-arb auto-prune caller가 여전히 `prune_smoke_dirs "$PROJECT_ROOT/.pipeline" "live-arb-smoke-*" "$keep_recent" 0 0`을 인라인으로 호출해, 캐럴 contract(pattern + `protect_tracked=0`)가 캘러 쪽에 깔려 있고 regression은 간접 커버에 머물렀다는 점이었습니다.
- 이번 라운드는 blocked-smoke 쪽에서 쓴 shared-wrapper 패턴을 그대로 live-arb 쪽에 복사해, sibling caller 경계까지 같은 방식으로 닫는 것이 목적입니다. scope는 smoke cleanup helper/caller ownership 안으로만 움직입니다.

## 핵심 변경
- `.pipeline/smoke-cleanup-lib.sh`에 `prune_live_arb_smoke_dirs <project_root> <keep_recent>` helper를 추가했습니다. `prune_blocked_smoke_dirs`와 대칭 구조로, 인자/가드 동작은 동일하되 내부 호출만 `prune_smoke_dirs "$project_root/.pipeline" "live-arb-smoke-*" "$keep_recent" 0 0 >/dev/null`로 고정했습니다. live-arb smoke는 모든 workspace가 generated이기 때문에 `protect_tracked=0`을 유지하고, 주석에도 "checked-in fixtures live under this pattern이 아님"을 명시해 두었습니다.
- `.pipeline/smoke-three-agent-arbitration.sh`의 `prune_old_smoke_dirs`는 이제 상수를 복제하지 않고 `prune_live_arb_smoke_dirs "$PROJECT_ROOT" "$keep_recent"`로 위임합니다. 호출 지점(`prune_old_smoke_dirs "$KEEP_RECENT_SMOKES"`)과 환경변수 계약은 그대로라 live smoke의 관찰 가능 동작은 바뀌지 않습니다. 주석에는 이 caller가 shared helper로 커버된다는 사실을 남겼습니다.
- `tests/test_pipeline_smoke_cleanup.py`에 live-arb caller용 focused regression 네 개를 추가했습니다.
  - `test_live_arb_caller_keeps_newest_and_prunes_older`: `live-arb-smoke-1~5`를 5개 두고 `keep_recent=3`으로 shared helper를 직접 호출해 최신 3개는 살고 오래된 2개는 실제로 삭제되는지 확인합니다.
  - `test_live_arb_caller_noop_when_keep_recent_invalid`: 빈 문자열, `0`, 음수, 비숫자 입력에 대해 caller가 아무 것도 지우지 않는 no-op임을 확인해, 이번에 추가한 가드 회귀를 좁게 잠급니다.
  - `test_live_arb_caller_does_not_touch_blocked_smoke_dirs`: 같은 `.pipeline` 아래 `live-blocked-smoke-*` 디렉터리를 같이 두고 live-arb helper를 호출했을 때 blocked 디렉터리는 전혀 건드리지 않는지를 확인합니다. 두 wrapper의 pattern이 섞이지 않는지 좁게 고정하는 cross-family 가드입니다.
  - `test_live_arb_script_delegates_to_shared_helper`: 실제 `.pipeline/smoke-three-agent-arbitration.sh` 텍스트에 `prune_live_arb_smoke_dirs` 호출이 들어 있는지 grep으로 확인해, 누군가 다시 caller를 인라인으로 되돌리면 즉시 실패하도록 잡았습니다.
- `.pipeline/README.md`는 건드리지 않았습니다. 외부에서 본 계약(환경변수, smoke 실행 방식, stdout/stderr 관찰 가능 출력)은 동일하기 때문입니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 12 tests`, `OK` (기존 8 + 신규 4). 기존 blocked-smoke/live-arb/manual cleanup/fail-closed regression은 그대로 통과했습니다.
- `bash -n .pipeline/smoke-three-agent-arbitration.sh .pipeline/smoke-cleanup-lib.sh` → 통과
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/smoke-three-agent-arbitration.sh tests/test_pipeline_smoke_cleanup.py` → 출력 없음
  - 참고: `.pipeline/smoke-cleanup-lib.sh`와 `tests/test_pipeline_smoke_cleanup.py`는 repo에서 untracked 상태라 whitespace check 대상에 포함되지 않습니다. 두 파일의 최종 내용은 위 unit test 재실행과 직접 편집으로 확인했습니다.
- 실제 tmux 기반 `smoke-three-agent-arbitration.sh` live rerun은 이번 라운드에서 돌리지 않았습니다. 이번 변경은 caller 내부 호출 본체만 shared helper로 교체했고(환경변수/인자/리다이렉션/관찰 가능 출력 계약 동일), unit test에서도 live tmux session을 스폰하지 않는 것이 기존 컨벤션이기 때문에 caller 경계는 shared helper 계약 + "script가 helper에 위임한다"는 문자열 regression으로 좁게 닫는 편이 same-family current-risk reduction에 맞습니다.

## 남은 리스크
- `prune_live_arb_smoke_dirs`는 `protect_tracked=0`을 의도적으로 고정했습니다. 만약 나중에 `live-arb-smoke-*` 패턴 아래에도 checked-in fixture를 두게 되면 이 wrapper가 silent fallback처럼 보일 수 있으므로, 그 때는 pattern/protect_tracked 계약 자체를 이 wrapper 안에서 재설계해야 합니다.
- `test_live_arb_script_delegates_to_shared_helper`는 실제 스크립트 경로를 텍스트 grep으로 확인합니다. shared helper 이름을 rename하는 refactor는 lib/script/테스트 세 곳을 한 번에 고쳐야 한다는 점이 여전합니다. tmux 전체 경로 재실행은 이번 slice 밖입니다.
- `.pipeline/live-blocked-smoke-*` 체크인 fixture 디렉터리의 위치/크기 정리, archive policy, 다른 smoke family의 auto-prune caller wrapping은 여전히 이번 scope 밖입니다. 관련 slice는 별도 라운드로 유지합니다.
