# 2026-04-18 blocked-smoke cleanup의 checked-in fixture 보호 경계

## 변경 파일
- `.pipeline/smoke-cleanup-lib.sh` (신규)
- `.pipeline/cleanup-old-smoke-dirs.sh`
- `.pipeline/smoke-three-agent-arbitration.sh`
- `.pipeline/smoke-implement-blocked-auto-triage.sh`
- `.pipeline/README.md`
- `tests/test_pipeline_smoke_cleanup.py` (신규)

## 사용 skill
- superpowers:using-superpowers

## 변경 이유
- `.pipeline/smoke-implement-blocked-auto-triage.sh`의 inline `prune_old_smoke_dirs`가 `live-blocked-smoke-*` 디렉터리를 glob으로 `rm -rf`하고 있었고, 같은 prefix로 repo에 커밋된 fixture 디렉터리(`.pipeline/live-blocked-smoke-9crJXb/`, `.pipeline/live-blocked-smoke-F3RhJR/`, `.pipeline/live-blocked-smoke-y5xUhi/`)가 함께 사라질 수 있는 destructive risk가 있었습니다.
- live arbitration smoke와 blocked smoke가 각자 다른 `find ... | sort | rm -rf` 루프를 복제해 들고 있어, cleanup 경계를 한 군데서 검증하기가 어려웠습니다.
- blocked-smoke cleanup 경계에만 "git-tracked이면 건너뛴다" 규칙을 붙이고, live-arb cleanup은 기존 동작을 그대로 두는 "generated-only prune" boundary를 하나의 공용 helper로 고정합니다.

## 핵심 변경
- 공용 shell lib `.pipeline/smoke-cleanup-lib.sh`를 추가해 `prune_smoke_dirs <smoke_root> <pattern> <keep_recent> [protect_tracked] [dry_run]` 한 함수가 newest-first 선택·keep window·tracked 보호·dry-run을 모두 담당하도록 모았습니다.
  - `protect_tracked=1`이면 삭제 후보마다 `git ls-files --error-unmatch -- <dir>`로 tracked 파일 존재를 확인하고, 존재하면 `PROTECT <path>`만 찍고 건너뜁니다.
  - 출력은 후보별로 한 줄씩 `KEEP` / `PROTECT` / `DELETE`로 통일했습니다.
- `.pipeline/smoke-implement-blocked-auto-triage.sh`의 `prune_old_smoke_dirs`는 이제 `prune_smoke_dirs "$PROJECT_ROOT/.pipeline" "live-blocked-smoke-*" "$keep_recent" 1 0 >/dev/null`로 위임합니다. tracked fixture 디렉터리는 이 경로에서 삭제되지 않고, 이번 smoke run이 방금 만든 untracked workspace만 오래된 순으로 정리됩니다.
- `.pipeline/smoke-three-agent-arbitration.sh`의 `prune_old_smoke_dirs`도 같은 helper로 위임하면서 `protect_tracked=0`으로 live-arb의 기존 "generated-only prune" 계약을 유지합니다.
- 수동 정리 스크립트 `.pipeline/cleanup-old-smoke-dirs.sh`도 inline 루프를 지우고 같은 lib을 source해 enumerate/prune을 수행합니다. 기본 pattern은 `live-arb-smoke-*`이며 필요한 경우 `PIPELINE_SMOKE_PATTERN=...`로 다른 generated pattern을 지정할 수 있게 했습니다.
- `.pipeline/README.md`에 "smoke 디렉터리 정리 규약" 섹션을 추가해 `generated-and-prunable` (`live-arb-smoke-*` 전체 + untracked `live-blocked-smoke-*`) vs `checked-in-and-protected` (git-tracked `live-blocked-smoke-*` fixture) 경계와 각 호출 지점(`smoke-three-agent-arbitration.sh`, `smoke-implement-blocked-auto-triage.sh`, `cleanup-old-smoke-dirs.sh`)이 같은 `prune_smoke_dirs` helper를 공유한다는 사실을 명시했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - `test_blocked_smoke_protects_tracked_fixture_dir`: tracked `live-blocked-smoke-*` fixture가 `PROTECT`로 건너뛰어지고, 더 오래된 untracked 디렉터리는 `DELETE`됨을 확인.
  - `test_blocked_smoke_deletes_untracked_older_dirs`: tracked가 전혀 없을 때 newest `KEEP_RECENT`만 남기고 나머지를 삭제함을 확인.
  - `test_live_arb_cleanup_keeps_newest_keep_recent_dirs`: live-arb 경로의 기존 newest-K 유지 동작이 변하지 않았음을 확인.
- `bash -n .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-three-agent-arbitration.sh .pipeline/smoke-implement-blocked-auto-triage.sh`
- `git diff --check -- .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-three-agent-arbitration.sh .pipeline/smoke-implement-blocked-auto-triage.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`

## 남은 리스크
- 기존 3개의 checked-in `.pipeline/live-blocked-smoke-*` fixture 디렉터리는 이번 slice의 scope 제한에 따라 그대로 두었습니다. 추후 라운드에서 fixture가 너무 커지면 별도 slice로 축소하거나 별도 위치로 옮기는 편을 검토해야 합니다.
- 공용 lib은 `bash` array/`mapfile` 사용이 필요합니다. 새 smoke helper를 추가할 때 `#!/bin/sh`가 아니라 `#!/bin/bash`로 실행해야 `prune_smoke_dirs`가 동작합니다.
- `git ls-files --error-unmatch -- <dir>`는 smoke_root가 git repo 안에 있을 때만 유효합니다. 지금 호출 지점은 모두 repo 안쪽이지만, 외부 경로를 전달하는 상상 호출자가 생기면 `protect_tracked=1`이 조용히 "아무 것도 보호하지 않음"으로 fallback할 수 있으니 새 호출 지점을 추가할 때 이 전제를 유지해야 합니다.
