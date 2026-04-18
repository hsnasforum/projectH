# 2026-04-18 prune_smoke_dirs, git 바깥에서는 fail-closed로 잠그기

## 변경 파일
- `.pipeline/smoke-cleanup-lib.sh`
- `.pipeline/README.md`
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- superpowers:using-superpowers

## 변경 이유
- 직전 라운드(`work/4/18/2026-04-18-manual-smoke-cleanup-protect-tracked.md`)로 repo-local manual override는 이미 tracked-safe로 묶였습니다.
- 같은 family 안에 남아 있던 narrower risk는 `prune_smoke_dirs(protect_tracked=1, ...)`을 smoke_root가 git work tree 바깥인 상황에서 부르면 `_smoke_has_tracked_contents`가 빈 `repo_root`로 항상 false를 돌려줘 조용히 "아무 것도 보호하지 않음" 모드로 degrade한다는 점이었습니다.
- 현재 caller들이 모두 `.pipeline/` 내부라 실제 피해가 발생할 가능성은 낮지만, 이 silent fallback은 추후 새 caller가 smoke_root를 잘못 지정했을 때 동일 destructive path가 다시 열릴 씨앗이므로 fail-closed 경계로 막아 두는 것이 다음 same-family current-risk reduction입니다.

## 핵심 변경
- `.pipeline/smoke-cleanup-lib.sh`의 `prune_smoke_dirs`는 이제 `protect_tracked=1`일 때 enumeration/삭제 전에 `git -C "$smoke_root" rev-parse --show-toplevel`을 먼저 돌리고, 결과가 빈 문자열이면 `prune_smoke_dirs: protect_tracked=1 requires a git-backed smoke root, got <path>` 한 줄을 stderr에 찍고 `return 2`로 fail-closed 합니다. 기존의 늦은 repo_root 조회는 동일 로직을 중복 호출하지 않도록 같이 제거했습니다.
- lib 상단 주석에 이 fail-closed 계약("smoke_root가 git work tree 밖이면 enumeration/delete 전에 non-zero return")을 명시해, 이후 caller를 추가할 때 이 경계가 드러나게 했습니다.
- `.pipeline/README.md`의 smoke 디렉터리 정리 규약에 같은 문장을 추가해, 현재 caller가 모두 `.pipeline/` 내부라서 실제로는 이 fail-closed 경계에 걸리지 않는다는 전제까지 명시했습니다. caller 설명은 변경하지 않았습니다.
- `tests/test_pipeline_smoke_cleanup.py`에 `test_prune_smoke_dirs_fails_closed_outside_git_repo`를 추가했습니다. 이 테스트는:
  - git init을 하지 않은 `tempfile.TemporaryDirectory`를 smoke_root 부모로 쓰고 (`GIT_CEILING_DIRECTORIES`로 상위 repo 탐색까지 차단해 주변 환경에 의존하지 않음),
  - 내부에 `live-blocked-smoke-*` 3개를 미리 만든 뒤,
  - `bash`로 lib을 source해서 `prune_smoke_dirs ... 1 1 0` (protect_tracked=1, dry_run=0) 을 직접 호출하고,
  - 종료 코드가 non-zero이고 stderr에 `protect_tracked=1` 와 문제의 smoke_root 경로가 같이 찍히는지, stdout에는 아무 KEEP/PROTECT/DELETE 도 나오지 않았는지, 세 디렉터리가 모두 그대로 남아 있는지를 검증합니다.
- 기존 4개 테스트(auto/manual tracked protection, live-arb keep window)도 회귀 없이 계속 통과합니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup` → 5/5 pass (기존 4 + 신규 1)
- `bash -n .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh`
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`

## 남은 리스크
- 이번 변경은 `protect_tracked=1` 경로에만 fail-closed를 적용합니다. `protect_tracked=0` 경로(live-arb auto-prune, manual cleanup에서 pattern override를 쓰지 않는 기본 호출)는 여전히 repo 바깥에서도 동작하며, 이 경로는 원래 tracked 파일을 전제로 하지 않습니다. 이 경계가 뒤집혀 non-repo cleanup이 기본 경로에서 강제 실패하는 일은 의도한 바가 아니므로, 새 caller를 추가할 때 "tracked 보호가 필요한가"에 맞춰 두 모드를 구분해 유지해야 합니다.
- 진단 메시지는 사람 읽기용 문자열 한 줄입니다. 자동화 consumer가 이 메시지를 scrape하려 하면 문구가 바뀔 때 깨질 수 있으므로, 필요한 경우 exit code 2 자체를 먼저 신뢰하고 문자열은 evidence로만 쓰는 편이 맞습니다.
- 체크인된 `.pipeline/live-blocked-smoke-*` fixture 디렉터리 자체의 위치/크기 정리는 이번 scope가 아닙니다. 관련 slice는 별도 라운드로 유지합니다.
