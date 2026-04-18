# 2026-04-18 blocked-smoke cleanup tracked-fixture 보호 경계 verification

## 변경 파일
- `verify/4/18/2026-04-18-smoke-blocked-cleanup-protect-tracked-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-smoke-blocked-cleanup-protect-tracked.md`가 blocked-smoke cleanup의 destructive risk를 줄이기 위해 공용 smoke cleanup helper, blocked auto-prune의 tracked fixture 보호, live-arb cleanup helper 재사용, `.pipeline/README.md` truth-sync, 새 script test를 추가했다고 주장하므로 현재 tree와 좁은 재실행 결과가 실제로 맞는지 다시 확인해야 했습니다.
- 같은 날짜의 기존 `/verify`는 `verify/4/18/2026-04-18-process-starttime-fingerprint-proc-ctime-third-fallback-verification.md`까지였고, smoke cleanup family에 대한 verification note는 아직 없었으므로 이번 라운드는 별도 verify note로 닫는 편이 맞았습니다.

## 핵심 변경
- latest `/work`의 핵심 코드/문서 변경 자체는 현재 tree에 실제로 존재합니다.
  - 새 `.pipeline/smoke-cleanup-lib.sh`는 `prune_smoke_dirs <smoke_root> <pattern> <keep_recent> [protect_tracked] [dry_run]` helper와 `KEEP` / `PROTECT` / `DELETE` 출력 계약을 정의하고, `protect_tracked=1`일 때 `git ls-files --error-unmatch -- <dir>`로 tracked contents를 보호합니다.
  - `.pipeline/smoke-implement-blocked-auto-triage.sh`는 새 helper를 source하고, blocked-smoke auto-prune 경로를 `prune_smoke_dirs "$PROJECT_ROOT/.pipeline" "live-blocked-smoke-*" "$keep_recent" 1 0 >/dev/null`로 좁혀 tracked fixture 삭제를 피하도록 바뀌었습니다.
  - `.pipeline/smoke-three-agent-arbitration.sh`도 같은 helper를 source해 live-arb cleanup을 `protect_tracked=0`으로 재사용합니다.
  - `.pipeline/cleanup-old-smoke-dirs.sh`는 helper를 source하고 `PIPELINE_SMOKE_PATTERN` override를 추가해 pattern별 수동 정리를 같은 경계로 통일했습니다.
  - `tests/test_pipeline_smoke_cleanup.py`는 helper 기준의 3개 focused regression을 추가했고, `.pipeline/README.md`에는 smoke directory cleanup 규약 섹션이 실제로 들어가 있습니다.
- 다만 latest `/work`는 **완전히 truthful하다고 보기는 어렵습니다.**
  - blocked auto-triage auto-prune 경계는 실제로 보호됐지만, 수동 정리 스크립트 `.pipeline/cleanup-old-smoke-dirs.sh`는 여전히 `prune_smoke_dirs ... 0 "$DRY_RUN"`를 호출하므로 pattern override에서 tracked blocked-smoke fixture를 보호하지 않습니다.
  - 임시 git repo에서 tracked `.pipeline/live-blocked-smoke-TRACKED/` 하나를 만든 뒤 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*' PIPELINE_SMOKE_KEEP_RECENT=0 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh <tmp>`를 실행하자 실제 출력이 `DELETE .../live-blocked-smoke-TRACKED`로 나왔습니다.
  - 따라서 `.pipeline/README.md`와 `/work`의 "checked-in `live-blocked-smoke-*` fixture는 cleanup 경로가 절대 삭제/archvie 하지 않는다"는 취지의 표현은 현재 구현보다 강합니다. 현재 truthful한 경계는 더 좁습니다: `smoke-implement-blocked-auto-triage.sh`의 auto-prune은 보호되지만, `cleanup-old-smoke-dirs.sh`의 pattern override는 아직 보호되지 않습니다.
  - 또한 latest `/work`의 `## 사용 skill` 항목 `superpowers:using-superpowers`는 현재 확인 가능한 repo skill 표면과 일치하지 않습니다. 이 메타데이터 mismatch는 이전 verify note들에서 이미 한 번 지적된 family와 같습니다.
- docs/plan 문맥은 이번 판단과 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline operator tooling을 계속 shipped browser gate 바깥의 internal/tooling family로 두고 있어, 이번 라운드도 browser 계약이 아니라 internal destructive-risk reduction family로 보는 편이 맞습니다.

## 검증
- `git diff --unified=3 -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-three-agent-arbitration.sh .pipeline/smoke-implement-blocked-auto-triage.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: `/work`가 설명한 helper 추가, 3개 shell script의 helper 위임, README smoke cleanup 섹션 추가, 새 focused test 파일 존재를 확인했습니다.
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 3 tests`, `OK`
- `bash -n .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-three-agent-arbitration.sh .pipeline/smoke-implement-blocked-auto-triage.sh`
  - 결과: 통과
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-three-agent-arbitration.sh .pipeline/smoke-implement-blocked-auto-triage.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 통과
- `tmpdir=$(mktemp -d) && cd "$tmpdir" && git init -q && mkdir -p .pipeline/live-blocked-smoke-TRACKED && cp /home/xpdlqj/code/projectH/.pipeline/smoke-cleanup-lib.sh .pipeline/ && cp /home/xpdlqj/code/projectH/.pipeline/cleanup-old-smoke-dirs.sh .pipeline/ && printf 'fixture\n' > .pipeline/live-blocked-smoke-TRACKED/note.txt && git add -f .pipeline/live-blocked-smoke-TRACKED && git -c user.email=t@example.com -c user.name=t commit -q --allow-empty -m init && git add -f .pipeline/live-blocked-smoke-TRACKED && git -c user.email=t@example.com -c user.name=t commit -q -m fixture >/dev/null 2>&1 || true && PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*' PIPELINE_SMOKE_KEEP_RECENT=0 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir"`
  - 결과: `DELETE /tmp/.../.pipeline/live-blocked-smoke-TRACKED`
  - 의미: manual cleanup override path는 아직 tracked blocked-smoke fixture 보호를 보장하지 않습니다.
- `rg -n "superpowers:using-superpowers|using-superpowers" .agents .claude .codex work verify docs`
  - 결과: latest `/work`의 skill 표기는 보였지만, 현재 session에서 확인 가능한 repo skill 표면과 직접 대응되는 canonical skill 정의는 확인되지 않았습니다.
- broader runtime gate, live tmux smoke replay, browser/e2e는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 라운드는 shell cleanup helper와 그 호출 경계, README truth-sync, 새 focused regression만 다시 보면 충분했고, controller/browser/runtime current truth를 넓히는 변경은 없었기 때문입니다.

## 남은 리스크
- 현재 남은 가장 직접적인 same-family risk는 `.pipeline/cleanup-old-smoke-dirs.sh`의 pattern override입니다. 이 경로는 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*'` 같은 수동 호출에서 tracked blocked-smoke fixture를 여전히 `DELETE` 후보로 분류합니다.
- latest `/work`의 `## 사용 skill` 메타데이터 mismatch(`superpowers:using-superpowers`)는 계속 남아 있습니다. 코드/테스트 truth와 별개로 closeout 메타데이터는 완전히 정직하게 닫히지 않았습니다.
- `.pipeline/README.md`는 현재 smoke cleanup 섹션 외에도 unrelated dirty runtime docs hunk를 이미 포함하고 있습니다. 이번 verify는 smoke cleanup 규약 섹션과 관련 shell script 경계만 다시 맞췄고, file-wide authorship 전체를 재판정하지는 않았습니다.
