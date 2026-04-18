# 2026-04-18 blocked auto-triage caller focused regression verification

## 변경 파일
- `verify/4/18/2026-04-18-blocked-auto-triage-caller-focused-regression-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-blocked-auto-triage-caller-focused-regression.md`가 blocked-smoke auto-prune caller를 shared helper 경계로 올리고 focused regression 3건을 추가했다고 주장하므로, 그 내용이 현재 tree와 실제 재실행 결과에 맞는지 다시 확인해야 했습니다.
- 직전 verify인 `verify/4/18/2026-04-18-prune-smoke-dirs-fail-closed-outside-git-verification.md`가 바로 이 blocked-smoke caller coverage 부족을 다음 same-family current-risk로 남겨 두었으므로, 이번 verify는 그 후속 구현을 닫는 라운드입니다.

## 핵심 변경
- latest `/work`의 구현 주장은 현재 tree와 대체로 일치합니다.
  - `.pipeline/smoke-cleanup-lib.sh`에는 blocked-smoke auto-prune 전용 wrapper `prune_blocked_smoke_dirs <project_root> <keep_recent>`가 실제로 추가돼 있고, `live-blocked-smoke-*` + `protect_tracked=1` + `dry_run=0` caller contract를 shared helper 한 곳에 고정합니다.
  - `.pipeline/smoke-implement-blocked-auto-triage.sh`의 `prune_old_smoke_dirs`는 인라인 삭제 루프를 제거하고 `prune_blocked_smoke_dirs "$PROJECT_ROOT" "$keep_recent"`로 실제 위임합니다.
  - `tests/test_pipeline_smoke_cleanup.py`에는 `test_blocked_auto_triage_caller_protects_tracked_and_prunes_generated`, `test_blocked_auto_triage_caller_noop_when_keep_recent_invalid`, `test_blocked_auto_triage_script_delegates_to_shared_helper`가 실제로 들어가 있습니다.
- focused rerun도 모두 통과했습니다.
  - `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`는 8개 테스트 모두 `ok`였습니다.
  - `bash -n .pipeline/smoke-implement-blocked-auto-triage.sh .pipeline/smoke-cleanup-lib.sh`는 통과했습니다.
  - `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/smoke-implement-blocked-auto-triage.sh tests/test_pipeline_smoke_cleanup.py`도 출력 없이 종료됐습니다.
- 다만 latest `/work`는 이번에도 완전히 spotless한 closeout은 아닙니다.
  - `## 사용 skill`의 `superpowers:using-superpowers`, `superpowers:test-driven-development` 표기는 현재 session에서 확인 가능한 repo skill 표면과 일치하지 않습니다.
  - 또한 `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 현재 repo에서 untracked 상태라서 `git diff` 기반 provenance는 `.pipeline/smoke-implement-blocked-auto-triage.sh`보다 약합니다. 현재 tree 내용은 `/work` 설명과 맞지만, "이번 라운드에 정확히 이 파일에서 어떤 줄이 바뀌었는가"를 git diff 하나로만 닫을 수 있는 상태는 아닙니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline smoke tooling을 계속 shipped browser gate 밖의 internal/tooling family로 두고 있으므로, 이번 라운드는 same-family current-risk reduction으로 해석하는 편이 맞습니다.

## 검증
- `sed -n '1,240p' .pipeline/smoke-cleanup-lib.sh`
  - 결과: `prune_blocked_smoke_dirs <project_root> <keep_recent>` wrapper와 no-op guard, fixed blocked-smoke caller contract를 확인했습니다.
- `sed -n '1,240p' .pipeline/smoke-implement-blocked-auto-triage.sh`
  - 결과: `prune_old_smoke_dirs`가 인라인 삭제 로직 대신 `prune_blocked_smoke_dirs "$PROJECT_ROOT" "$keep_recent"`로 위임하는 현재 구현을 확인했습니다.
- `sed -n '1,340p' tests/test_pipeline_smoke_cleanup.py`
  - 결과: blocked auto-triage caller regression 3건이 현재 파일에 실제로 존재함을 확인했습니다.
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 8 tests`, `OK`
- `bash -n .pipeline/smoke-implement-blocked-auto-triage.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/smoke-implement-blocked-auto-triage.sh tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음
  - 주의: untracked `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`는 git diff 기반 whitespace check 대상에 실질적으로 잡히지 않았으므로, 이 둘은 위 직접 파일 대조와 unit test 재실행으로 확인했습니다.
- `git diff --name-only -- .pipeline/smoke-cleanup-lib.sh .pipeline/smoke-implement-blocked-auto-triage.sh tests/test_pipeline_smoke_cleanup.py`
  - 결과: tracked diff에는 `.pipeline/smoke-implement-blocked-auto-triage.sh`만 나타났습니다.
- `rg -n "superpowers:using-superpowers|superpowers:test-driven-development|using-superpowers" .agents .claude .codex work verify docs`
  - 결과: latest `/work`의 skill 표기는 보였지만, 현재 session에서 확인 가능한 repo skill 정의와 직접 대응되는 canonical skill 표면은 확인되지 않았습니다.
- 실제 tmux 기반 `.pipeline/smoke-implement-blocked-auto-triage.sh` live smoke는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경은 caller 내부 auto-prune 경계를 shared helper 호출로 고정하고 focused regression을 추가한 범위였고, tmux/runtime/browser contract를 새로 넓히지 않았기 때문입니다.

## 남은 리스크
- 현재 같은 smoke-cleanup family에서 가장 가까운 남은 risk는 `live-arb-smoke-*` caller인 `.pipeline/smoke-three-agent-arbitration.sh`가 여전히 `prune_smoke_dirs ... 0 0`를 직접 호출하고 있다는 점입니다. blocked-smoke family는 wrapper + regression으로 한 번 더 좁혀졌지만, live-arb caller는 아직 동일한 shared-caller pattern으로 정리되지 않았습니다.
- latest `/work`의 `## 사용 skill` 메타데이터 mismatch(`superpowers:using-superpowers`, `superpowers:test-driven-development`)는 이번 라운드에서도 그대로 남아 있습니다.
- `test_blocked_auto_triage_script_delegates_to_shared_helper`는 현재 텍스트 grep 성격의 회귀 검사입니다. caller 위임 경계를 더 강하게 잠그려면 나중에 sourceable helper boundary나 더 실행 가능한 contract로 옮겨 갈 여지가 남아 있습니다.
