# 2026-04-18 manual smoke cleanup override tracked-safe 고정 verification

## 변경 파일
- `verify/4/18/2026-04-18-manual-smoke-cleanup-protect-tracked-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-manual-smoke-cleanup-protect-tracked.md`가 수동 smoke cleanup override 경로까지 tracked-safe로 닫았다고 주장하므로, 직전 verify에서 남겨 둔 same-family destructive risk가 실제로 해소됐는지 다시 확인해야 했습니다.
- 같은 날짜의 기존 latest `/verify`는 `verify/4/18/2026-04-18-smoke-blocked-cleanup-protect-tracked-verification.md`였고, 그 note가 정확히 manual override path를 다음 current-risk로 남겨 두었으므로, 이번 라운드는 그 후속 구현을 닫는 별도 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 tree와 실제로 일치합니다.
  - `.pipeline/cleanup-old-smoke-dirs.sh`는 이제 manual cleanup에서 `prune_smoke_dirs "$SMOKE_ROOT" "$PATTERN" "$KEEP_RECENT" 1 "$DRY_RUN"`를 호출합니다. 즉 pattern override 여부와 무관하게 `protect_tracked=1`이 항상 켜집니다.
  - 같은 스크립트에는 "manual cleanup은 pattern override가 `live-blocked-smoke-*`를 가리켜도 checked-in fixture를 지우지 않아야 한다"는 취지의 짧은 주석이 실제로 추가돼 있습니다.
  - `.pipeline/README.md`의 smoke directory cleanup 규약도 manual cleanup 항목을 현재 구현 truth에 맞게 갱신해, `PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*'` override에서도 tracked fixture는 `PROTECT`로 건너뛰고 generated workspace만 삭제한다고 적고 있습니다.
  - `tests/test_pipeline_smoke_cleanup.py`에는 새 `test_manual_cleanup_script_protects_tracked_under_pattern_override`가 실제로 들어가 있으며, dry-run과 live 실행에서 모두 tracked fixture 보호 / newest untracked 유지 / 나머지 untracked 삭제를 검증합니다.
- 이번 라운드에서 다시 실행한 좁은 검증은 모두 통과했고, 직전 verify가 남긴 재현 경로도 실제로 뒤집혔습니다.
  - `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`는 `Ran 4 tests`, `OK`였습니다.
  - `bash -n .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh`는 통과했습니다.
  - `git diff --check -- .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`도 통과했습니다.
  - 임시 git repo에서 tracked `.pipeline/live-blocked-smoke-TRACKED` + untracked 3개를 만든 뒤 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*' PIPELINE_SMOKE_KEEP_RECENT=1`로 manual script를 dry-run/live 모두 실행했을 때, 출력은 `KEEP newest untracked`, `DELETE older untracked`, `PROTECT tracked fixture`로 나왔고 live 실행 후 tracked fixture와 newest untracked만 실제로 남았습니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline operator tooling을 여전히 shipped browser gate 밖의 internal/tooling family로 두고 있으므로, 이번 변경도 browser-visible 기능이 아니라 same-family destructive-risk reduction으로 남습니다.
- 다만 latest `/work`는 **메타데이터까지 포함하면 완전히 truthful하다고 보기는 어렵습니다.**
  - `## 사용 skill`의 `superpowers:using-superpowers` 표기는 현재 session에서 확인 가능한 repo skill 표면과 일치하지 않습니다.
  - 따라서 코드/테스트/README 진술은 이번엔 맞지만, closeout 메타데이터까지 합치면 latest `/work`는 "거의 truthful하지만 skill 항목은 mismatch" 상태입니다.

## 검증
- `git diff --unified=3 -- .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: `/work`가 설명한 `protect_tracked=1` 고정, manual cleanup 주석, README manual contract 강화, 새 focused regression 추가를 확인했습니다.
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 4 tests`, `OK`
- `bash -n .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh`
  - 결과: 통과
- `git diff --check -- .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 통과
- `tmpdir=$(mktemp -d) && cd "$tmpdir" && git init -q && mkdir -p .pipeline/live-blocked-smoke-TRACKED && cp /home/xpdlqj/code/projectH/.pipeline/smoke-cleanup-lib.sh .pipeline/ && cp /home/xpdlqj/code/projectH/.pipeline/cleanup-old-smoke-dirs.sh .pipeline/ && printf 'fixture\n' > .pipeline/live-blocked-smoke-TRACKED/note.txt && git add -f .pipeline/live-blocked-smoke-TRACKED && git -c user.email=t@example.com -c user.name=t commit -q --allow-empty -m init && git add -f .pipeline/live-blocked-smoke-TRACKED && git -c user.email=t@example.com -c user.name=t commit -q -m fixture >/dev/null 2>&1 || true && mkdir -p .pipeline/live-blocked-smoke-old1 .pipeline/live-blocked-smoke-old2 .pipeline/live-blocked-smoke-new && printf a > .pipeline/live-blocked-smoke-old1/note.txt && printf b > .pipeline/live-blocked-smoke-old2/note.txt && printf c > .pipeline/live-blocked-smoke-new/note.txt && touch -t 202604182000 .pipeline/live-blocked-smoke-TRACKED .pipeline/live-blocked-smoke-TRACKED/note.txt && touch -t 202604182100 .pipeline/live-blocked-smoke-old1 .pipeline/live-blocked-smoke-old1/note.txt && touch -t 202604182200 .pipeline/live-blocked-smoke-old2 .pipeline/live-blocked-smoke-old2/note.txt && touch -t 202604182300 .pipeline/live-blocked-smoke-new .pipeline/live-blocked-smoke-new/note.txt && PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*' PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=1 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir" && echo '---LIVE---' && PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*' PIPELINE_SMOKE_KEEP_RECENT=1 PIPELINE_SMOKE_CLEANUP_DRY_RUN=0 bash .pipeline/cleanup-old-smoke-dirs.sh "$tmpdir" && find "$tmpdir/.pipeline" -maxdepth 1 -mindepth 1 -type d | sort`
  - 결과: dry-run과 live 모두 `PROTECT .../live-blocked-smoke-TRACKED`를 출력했고, live 실행 뒤에는 tracked fixture와 newest untracked만 남았습니다.
- `rg -n "superpowers:using-superpowers|using-superpowers" .agents .claude .codex work verify docs`
  - 결과: latest `/work`의 skill 표기는 보였지만 현재 session에서 확인 가능한 repo skill 정의와 직접 대응되는 canonical skill 표면은 확인되지 않았습니다.
- broader runtime gate, live tmux smoke replay, browser/e2e는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경은 manual cleanup script 경계와 README/test sync에 한정됐고, controller/browser/runtime current truth를 넓히지 않았기 때문입니다.

## 남은 리스크
- 현재 같은 family에서 바로 보이는 남은 current-risk는 `protect_tracked=1`이 git repo 바깥 경로에서는 조용히 보호를 잃는다는 점입니다. 지금 caller는 모두 repo 안쪽이라 즉시 문제는 아니지만, 새 외부 caller가 붙으면 fail-open처럼 보일 수 있습니다.
- latest `/work`의 `## 사용 skill` 메타데이터 mismatch(`superpowers:using-superpowers`)는 이번 라운드에서도 그대로 남아 있습니다.
- checked-in `.pipeline/live-blocked-smoke-*` fixture 디렉터리의 실제 위치/크기 정리는 여전히 별도 slice입니다. 이번 라운드는 삭제 방지 경계만 닫았고 fixture relocation이나 archive policy는 건드리지 않았습니다.
