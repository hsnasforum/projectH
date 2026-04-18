# 2026-04-18 prune_smoke_dirs outside-git fail-closed verification

## 변경 파일
- `verify/4/18/2026-04-18-prune-smoke-dirs-fail-closed-outside-git-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-prune-smoke-dirs-fail-closed-outside-git.md`가 `protect_tracked=1` 경로의 outside-git silent degradation을 fail-closed로 막았다고 주장하므로, 코드/README/test와 실제 재실행 결과가 그 설명과 맞는지 다시 확인해야 했습니다.
- 직전 same-family verify인 `verify/4/18/2026-04-18-manual-smoke-cleanup-protect-tracked-verification.md`가 바로 이 outside-git 보호 상실을 다음 current-risk로 남겨 두었으므로, 이번 verify는 그 후속 구현을 닫는 좁은 truth-sync 라운드입니다.

## 핵심 변경
- latest `/work`의 코드/문서/테스트 주장은 현재 tree와 일치합니다.
  - `.pipeline/smoke-cleanup-lib.sh`의 `prune_smoke_dirs`는 이제 `protect_tracked=1`일 때 먼저 `git -C "$smoke_root" rev-parse --show-toplevel`을 확인하고, git-backed root를 얻지 못하면 stderr에 `prune_smoke_dirs: protect_tracked=1 requires a git-backed smoke root, got <path>`를 남긴 뒤 `return 2`로 종료합니다.
  - 같은 파일 상단 주석에도 "outside git work tree면 enumeration/delete 전에 non-zero return" 계약이 실제로 적혀 있습니다.
  - `.pipeline/README.md`의 `smoke 디렉터리 정리 규약`도 이 fail-closed 계약과 "현재 caller는 모두 repo 내부라 실제로는 이 경계에 걸리지 않는다"는 전제를 현재 구현 truth에 맞게 설명합니다.
  - `tests/test_pipeline_smoke_cleanup.py`에는 `test_prune_smoke_dirs_fails_closed_outside_git_repo`가 실제로 추가되어 있고, non-git temp dir에서 stderr 진단, non-zero exit, 빈 stdout, 디렉터리 미삭제를 함께 검증합니다.
- focused rerun 결과도 모두 통과했습니다.
  - `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`는 5개 테스트 모두 `ok`로 통과했습니다.
  - `bash -n .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh`는 통과했습니다.
  - `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`도 출력 없이 종료됐습니다.
- 다만 latest `/work`의 closeout 메타데이터는 이번에도 완전히 truthful하지 않습니다.
  - `## 사용 skill`의 `superpowers:using-superpowers` 표기는 현재 session에서 확인 가능한 repo skill 표면과 일치하지 않습니다.
  - 또한 위 `git diff --check` 명령은 untracked 상태인 `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py` 내용을 실제로 검사하지 않습니다. 이번 verify에서는 이 두 파일을 unit test 재실행과 직접 파일 대조로 확인했으므로 동작 truth 자체는 맞지만, whitespace check 범위는 tracked diff로 좁게 읽는 편이 정확합니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline smoke tooling을 계속 shipped browser gate 밖의 internal/tooling family로 두고 있으므로, 이번 라운드는 same-family current-risk reduction으로 해석하는 편이 맞습니다.

## 검증
- `git diff --unified=3 -- .pipeline/smoke-cleanup-lib.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: latest `/work`가 설명한 fail-closed helper 경계, README smoke cleanup 규약 보강, outside-git focused regression 추가를 확인했습니다.
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 5 tests`, `OK`
- `bash -n .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh`
  - 결과: 통과
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음
  - 주의: git diff 관점에서는 untracked `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`가 실제 check 대상에 포함되지 않았으므로, 이 둘의 truth는 위 unit test/파일 대조로 별도 확인했습니다.
- `rg -n "superpowers:using-superpowers|using-superpowers" .agents .claude .codex work verify docs`
  - 결과: latest `/work`의 skill 표기는 보였지만, 현재 session에서 확인 가능한 repo skill 정의와 직접 대응되는 canonical skill 표면은 확인되지 않았습니다.
- broader runtime smoke, tmux live smoke, browser/e2e는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경은 shell helper 경계, README, focused regression에 한정됐고 shipped browser/runtime contract를 넓히지 않았기 때문입니다.

## 남은 리스크
- 현재 same-family에서 가장 가까운 남은 risk는 실제 blocked-smoke caller인 `.pipeline/smoke-implement-blocked-auto-triage.sh`의 auto-prune 경로에 대한 focused regression이 아직 없다는 점입니다. helper와 manual cleanup 경계는 테스트되지만, 실제 `live-blocked-smoke-*` auto-prune caller contract는 아직 간접 커버에 가깝습니다.
- latest `/work`의 `## 사용 skill` 메타데이터 mismatch(`superpowers:using-superpowers`)는 이번 라운드에서도 그대로 남아 있습니다.
- fail-closed 진단은 여전히 사람 읽기용 문자열 한 줄입니다. 향후 consumer가 이 문자열을 파싱하지 말고 exit code를 우선 신뢰하도록 유지해야 합니다.
