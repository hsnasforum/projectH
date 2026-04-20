# 2026-04-18 manual smoke-cleanup `KEEP_RECENT=0` fail-safe 경계 정합

## 변경 파일
- `.pipeline/smoke-cleanup-lib.sh`
- `.pipeline/README.md`
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- 없음

## 변경 이유
- 직전 `/work`인 `work/4/18/2026-04-18-live-arb-caller-focused-regression.md`와 그 verify(`verify/4/18/2026-04-18-live-arb-caller-focused-regression-verification.md`)가 live-arb auto-prune caller를 shared `prune_live_arb_smoke_dirs` helper로 올린 뒤, 같은 smoke-cleanup family에서 남은 가장 작은 current-risk로 `.pipeline/cleanup-old-smoke-dirs.sh` + `prune_manual_smoke_dirs`가 `keep_recent <= 0`을 blocked/live-arb wrapper와 동일하게 fail-safe no-op으로 막아 주는지 아직 regression으로 좁게 고정되지 않은 점을 남겨 두었습니다.
- `.pipeline/README.md`의 `PIPELINE_SMOKE_KEEP_RECENT=0` 계약은 auto-prune에만 명시돼 있고 수동 cleanup 경로에는 같은 문장이 없어, "manual path도 0이면 no-op이다"라는 truth를 docs-only로도 읽을 수 있는 상태가 아니었습니다.
- `prune_manual_smoke_dirs` 본체는 `keep_recent=0`에서도 `prune_smoke_dirs`를 그대로 호출했기 때문에, 매칭 디렉터리가 `keep_recent`를 초과하기만 하면 전부 DELETE 로그와 함께 지워지는 경계가 열려 있었습니다. 이번 slice는 이 경계를 wrapper 한 곳에서 닫고 focused regression으로 잠그는 것이 목표입니다.

## 핵심 변경
- `.pipeline/smoke-cleanup-lib.sh`의 `prune_manual_smoke_dirs`에 `keep_recent <= 0`이면 바로 `return 0`하는 fail-safe 경계를 추가했습니다. 주석에도 blocked/live-arb wrapper와 `PIPELINE_SMOKE_KEEP_RECENT=0 disables cleanup` README 계약을 따른다는 이유를 같이 남겨, 다음에 이 경계를 수정할 사람이 "0을 정말 삭제로 쓰고 싶다면 README 계약도 같이 바꿔야 한다"는 것을 바로 읽을 수 있게 했습니다. 빈 문자열/음수/비숫자 입력은 기존 가드가 계속 잡습니다.
- `.pipeline/cleanup-old-smoke-dirs.sh`는 이미 `prune_manual_smoke_dirs "$SMOKE_ROOT" "$PATTERN" "$KEEP_RECENT" "$DRY_RUN"`로 위임하고 있어 이번 라운드에서는 수정하지 않았습니다. 상단의 "Nothing to clean" early-exit은 `KEEP_RECENT >= SMOKE_DIRS` 구간에만 해당하므로 `KEEP_RECENT=0` + 실제 매칭 디렉터리가 있는 경우에는 helper의 새 fail-safe 경계에 정확히 도달합니다.
- `tests/test_pipeline_smoke_cleanup.py`에 이번 slice를 직접 좁히는 regression 2건을 추가했습니다.
  - `test_manual_cleanup_caller_noop_when_keep_recent_is_zero`: `live-arb-smoke-1~3`을 만든 뒤 `prune_manual_smoke_dirs` helper를 `keep_recent=0`, `dry_run=0`으로 직접 호출해 세 디렉터리가 모두 그대로 남고 stdout이 빈 문자열인지 확인합니다. 이 테스트는 README 계약("0이면 정리를 끈다")과 wrapper 동작이 정확히 같은지 고정합니다.
  - `test_manual_cleanup_script_keep_recent_zero_preserves_dirs`: 실제 `.pipeline/cleanup-old-smoke-dirs.sh`를 `PIPELINE_SMOKE_PATTERN=live-arb-smoke-*`, `PIPELINE_SMOKE_KEEP_RECENT=0`, `PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`으로 실행해 매칭되는 세 디렉터리가 모두 보존되는지 확인합니다. script → helper 경계까지 포함한 end-to-end fail-safe가 깨지면 바로 실패합니다.
- `.pipeline/README.md`의 "오래된 smoke 디렉터리만 수동으로 정리하려면 ..." 블록 바로 아래에 한 줄을 추가해, 수동 cleanup도 `PIPELINE_SMOKE_KEEP_RECENT=0`이면 fail-safe no-op으로 동작한다는 사실을 명시했습니다. 수동 경로 계약과 자동 prune 계약이 같은 문장으로 읽히도록 하고, docs-only drift 없이 이번 code 변경을 설명하는 범위로만 제한했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup`
  - 결과: `Ran 18 tests`, `OK` (기존 12 + 신규 2 + 이전 라운드에서 이미 합류한 manual-path 관련 기존 테스트들 포함). `test_manual_cleanup_caller_noop_when_keep_recent_is_zero`와 `test_manual_cleanup_script_keep_recent_zero_preserves_dirs`가 현재 tree에서 실제로 녹색이며, 기존 manual/live-arb/blocked/fail-closed regression은 전부 그대로 통과했습니다.
- `bash -n .pipeline/cleanup-old-smoke-dirs.sh .pipeline/smoke-cleanup-lib.sh`
  - 결과: 통과.
- `git diff --check -- .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`
  - 결과: 출력 없음, exit code 0. `.pipeline/smoke-cleanup-lib.sh`와 `tests/test_pipeline_smoke_cleanup.py`는 여전히 repo에서 untracked 상태라 whitespace check가 실질적으로 잡는 범위는 이전 라운드와 같습니다. 두 파일의 최종 내용은 위 unit test 재실행과 직접 diff 확인으로 대조했습니다.
- 실제 tmux 기반 live smoke 재실행은 이번 라운드에서 돌리지 않았습니다. 이번 변경은 manual cleanup caller boundary 안에서만 움직였고 helper 호출 인자 계약과 관찰 가능 출력만 좁혀 축소 방향으로 바꾼 범위라, same-family current-risk reduction은 unit test + bash syntax check + docs truth-sync로 닫는 편이 scope에 맞습니다.

## 이미 dirty였던 edits에 대한 truthful 메모
- 이 라운드 시작 시점에 `git status`는 이미 `.pipeline/README.md`, `.pipeline/smoke-cleanup-lib.sh`, `tests/test_pipeline_smoke_cleanup.py`가 modified로 잡혀 있었습니다. 그 세 파일에는 이번 slice와 일치하는 방향의 edit(`prune_manual_smoke_dirs`의 `keep_recent <= 0` early-return, README 한 줄 추가, 매뉴얼 path용 regression 2건)이 이미 들어와 있었고, 이번 라운드에서 추가로 code를 바꾸지는 않았습니다. 대신 handoff가 요구한 대로 현재 tree의 상태가 slice 설명과 실제로 일치하는지, regression이 녹색인지, docs가 behavior와 맞는지를 직접 확인하고 `/work` closeout으로 이 사실을 남깁니다.
- unrelated untracked `tmp/`는 그대로 두었고, 이 라운드에서 건드리지 않았습니다.

## 남은 리스크
- `prune_manual_smoke_dirs`의 `keep_recent=0` fail-safe는 의도적으로 "정리를 끄는 의미"로 고정했습니다. 만약 나중에 "0 = 모두 삭제"로 계약을 바꾸고 싶다면, 이 wrapper뿐 아니라 `.pipeline/README.md`의 `PIPELINE_SMOKE_KEEP_RECENT=0` 문장과 blocked/live-arb wrapper의 대칭 가드까지 같이 수정해야 합니다. 이번 라운드는 현재 문서화된 계약을 그대로 code에 고정했을 뿐이라 방향성 자체는 다음 라운드 결정 사항입니다.
- `.pipeline/smoke-cleanup-lib.sh`와 `tests/test_pipeline_smoke_cleanup.py`는 여전히 untracked 상태입니다. 이번 라운드 역시 tracked diff 기반 provenance는 `.pipeline/README.md`만 나타나므로, 두 파일의 최종 내용을 verify 라운드에서도 직접 대조하는 편이 맞습니다.
- `test_manual_cleanup_script_keep_recent_zero_preserves_dirs`는 `PIPELINE_SMOKE_CLEANUP_DRY_RUN=0`에서도 디렉터리가 남는지만 확인합니다. stdout prefix("Smoke root:", "Pattern:" 등)까지 고정하지는 않았으므로, 스크립트 상단 진단 출력을 리팩터링하면 이 테스트와 별도로 README 계약을 다시 대조해야 합니다.
- archive policy, fixture 재배치, 다른 smoke family의 wrapper boundary, tmux 기반 live smoke 재실행은 이번 scope 밖입니다. 다음 same-family risk로 남아 있는 것은 manual cleanup script 상단 진단 출력과 stdout 계약 회귀, 그리고 `.pipeline/smoke-cleanup-lib.sh` / `tests/test_pipeline_smoke_cleanup.py`의 tracked 상태 정리 정도입니다.
