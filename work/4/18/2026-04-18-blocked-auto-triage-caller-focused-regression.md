# 2026-04-18 blocked-smoke auto-prune caller, 전용 regression 추가

## 변경 파일
- `.pipeline/smoke-cleanup-lib.sh`
- `.pipeline/smoke-implement-blocked-auto-triage.sh`
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- superpowers:using-superpowers
- superpowers:test-driven-development

## 변경 이유
- 직전 라운드(`work/4/18/2026-04-18-prune-smoke-dirs-fail-closed-outside-git.md`)와 그 verify는 helper-level `prune_smoke_dirs(... protect_tracked=1 ...)` 경계와 수동 cleanup caller까지 focused regression으로 덮었습니다.
- 같은 family에서 남아 있던 가장 좁은 current-risk는 실제 blocked-smoke auto-prune caller인 `.pipeline/smoke-implement-blocked-auto-triage.sh`의 `prune_old_smoke_dirs`였습니다. pattern(`live-blocked-smoke-*`) + `protect_tracked=1` + `dry_run=0` 조합은 caller 파일에 인라인으로 박혀 있어 helper-level 테스트로는 간접 커버에 그쳤고, 이 caller 자체가 바뀌어도 regression이 비명 지르지 않았습니다.
- 이번 라운드는 그 caller contract를 shared lib로 승격하고, caller가 실제로 이 shared path를 통과하는지까지 한 단위 테스트로 묶어 same-family current-risk를 닫는 것이 목적입니다. scope는 cleanup helper/caller ownership 안에서만 움직입니다.

## 핵심 변경
- `.pipeline/smoke-cleanup-lib.sh`에 `prune_blocked_smoke_dirs <project_root> <keep_recent>` helper를 추가했습니다. 이 helper는 blocked-smoke auto-prune의 canonical caller contract(`<project_root>/.pipeline` + `live-blocked-smoke-*` + `protect_tracked=1` + `dry_run=0`)를 한 곳에 고정하고, `keep_recent`가 비어 있거나 비숫자, 또는 0 이하이면 no-op으로 조기 return합니다. 진단 출력은 기존대로 `>/dev/null`에서 삼켜 caller 쪽 stdout 계약을 바꾸지 않습니다.
- `.pipeline/smoke-implement-blocked-auto-triage.sh`의 `prune_old_smoke_dirs`는 이제 내부에 상수를 복제하지 않고 `prune_blocked_smoke_dirs "$PROJECT_ROOT" "$keep_recent"`로 위임합니다. 호출 지점(`prune_old_smoke_dirs "$KEEP_RECENT_SMOKES"`)과 환경변수 계약은 그대로이므로 실제 smoke 실행 경로의 관찰 가능한 동작은 변하지 않습니다. 주석에는 이 경로가 shared helper로 커버된다는 사실을 남겼습니다.
- `tests/test_pipeline_smoke_cleanup.py`에 세 개의 focused regression을 추가했습니다.
  - `test_blocked_auto_triage_caller_protects_tracked_and_prunes_generated`: tracked `live-blocked-smoke-TRACKED` 하나 + 이보다 새로운 untracked 3개(`old1`/`old2`/`new`)를 `_make_temp_repo` 기반 임시 git tree 아래 배치하고, `keep_recent=1`로 `prune_blocked_smoke_dirs`를 직접 호출해 tracked 디렉터리와 최신 untracked 하나는 살아남고 나머지 untracked 두 개는 실제로 삭제되는지 확인합니다.
  - `test_blocked_auto_triage_caller_noop_when_keep_recent_invalid`: 빈 문자열, `0`, 음수, 비숫자 값 각각에 대해 caller가 아무 것도 지우지 않는 no-op임을 확인합니다. 이번 슬라이스에서 추가한 `keep_recent` 가드가 회귀 없이 유지되는지를 좁게 잠급니다.
  - `test_blocked_auto_triage_script_delegates_to_shared_helper`: 실제 `.pipeline/smoke-implement-blocked-auto-triage.sh`가 `prune_blocked_smoke_dirs`로 위임하는 문자열을 포함하는지 확인해, 누군가 caller를 다시 인라인으로 되돌리면 즉시 실패하도록 잡았습니다. 전체 tmux 구동 경로는 이 테스트에서 재실행하지 않습니다. 이유는 `## 검증`에 적었습니다.
- README 쪽 계약 문장은 손대지 않았습니다. caller가 shared lib로 위임하게 된 것은 문서 계약의 외부 표면을 바꾸지 않기 때문입니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 8 tests`, `OK` (기존 5 + 신규 3). 기존 `test_blocked_smoke_protects_tracked_fixture_dir`, `test_blocked_smoke_deletes_untracked_older_dirs`, `test_live_arb_cleanup_keeps_newest_keep_recent_dirs`, `test_manual_cleanup_script_protects_tracked_under_pattern_override`, `test_prune_smoke_dirs_fails_closed_outside_git_repo`도 그대로 통과했습니다.
- `bash -n .pipeline/smoke-implement-blocked-auto-triage.sh .pipeline/smoke-cleanup-lib.sh` → 통과
- `git diff --check -- .pipeline/smoke-implement-blocked-auto-triage.sh tests/test_pipeline_smoke_cleanup.py` → 출력 없음
  - 참고: `.pipeline/smoke-cleanup-lib.sh`와 `tests/test_pipeline_smoke_cleanup.py`는 현재 repo에서 untracked 상태라 git diff 관점의 whitespace check 대상에는 포함되지 않습니다. 두 파일의 최종 내용은 위 unit test 재실행과 직접 편집으로 확인했습니다.
- 실제 tmux 기반 `smoke-implement-blocked-auto-triage.sh` 실행은 이번 라운드에서 돌리지 않았습니다. 이번 변경은 caller의 내부 호출 본체만 shared helper 호출로 교체했고(환경변수/인자/리다이렉션/관찰 가능 출력 계약은 동일), live tmux smoke는 현재 스크립트 어디에서도 unit test에서 스폰되지 않기 때문에 caller 경계는 shared helper 계약 + "script가 helper에 위임한다"는 문자열 regression으로 닫는 편이 동일 family current-risk reduction에 더 맞습니다.

## 남은 리스크
- `prune_blocked_smoke_dirs`는 pattern과 protect_tracked 값을 caller 쪽에서 뒤집지 못하게 의도적으로 고정했습니다. 다른 smoke family(`live-arb-smoke-*`)는 여전히 `prune_smoke_dirs`를 직접 호출하고, 이 경로에는 이번처럼 caller 전용 wrapper가 없습니다. 새 auto-prune caller가 생긴다면 같은 패턴(전용 wrapper + focused regression)으로 확장하는 편이 맞습니다.
- `test_blocked_auto_triage_script_delegates_to_shared_helper`는 실제 스크립트 경로를 텍스트로 grep하는 가벼운 regression입니다. 이 문자열은 shared helper 이름과 결합되어 있어 refactor로 이름이 바뀌면 한 번에 두 곳을 같이 고쳐야 합니다. tmux 전체 경로 재실행은 이번 slice 밖입니다.
- fail-closed 진단과 `KEEP_RECENT_SMOKES` 환경 변수 계약은 이번에도 사람 읽기용 문자열 한 줄에 기대고 있습니다. 자동화 consumer가 문구를 파싱하려 하면 여전히 exit code를 먼저 신뢰하는 편이 맞습니다.
- 체크인된 `.pipeline/live-blocked-smoke-*` fixture 디렉터리의 위치/크기 재정리는 이번 scope가 아닙니다. 관련 slice는 별도 라운드로 유지합니다.
