# 2026-04-18 manual smoke cleanup override도 tracked-safe로 고정

## 변경 파일
- `.pipeline/cleanup-old-smoke-dirs.sh`
- `.pipeline/README.md`
- `tests/test_pipeline_smoke_cleanup.py`

## 사용 skill
- superpowers:using-superpowers

## 변경 이유
- 직전 라운드(`work/4/18/2026-04-18-smoke-blocked-cleanup-protect-tracked.md`)에서 blocked auto-prune 경로(`.pipeline/smoke-implement-blocked-auto-triage.sh`)는 `protect_tracked=1`로 고정됐지만, 같은 family의 수동 override 경로는 여전히 열려 있었습니다.
- `.pipeline/cleanup-old-smoke-dirs.sh`가 `prune_smoke_dirs "$SMOKE_ROOT" "$PATTERN" "$KEEP_RECENT" 0 "$DRY_RUN"`로 `protect_tracked=0`을 그대로 전달했기 때문에, 운영 중 `PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*'`로 pattern을 override하면 체크인된 fixture 디렉터리도 `DELETE` 후보에 섞여 `rm -rf`될 수 있는 destructive 경로가 남아 있었습니다.
- 이번 라운드는 같은 family 안에서 이 한 줄 짜리 current-risk reduction만 좁게 닫습니다. 새 cleanup axis나 fixture 이동은 이번 scope가 아닙니다.

## 핵심 변경
- `.pipeline/cleanup-old-smoke-dirs.sh`의 `prune_smoke_dirs` 호출을 `protect_tracked=1`로 바꿨습니다. manual cleanup은 pattern 값과 무관하게 항상 tracked-safe 모드로 동작하고, generated workspace만 실제 삭제 대상이 됩니다. 왜 이 경로에서만 `protect_tracked`를 강제하는지 설명하는 짧은 주석을 호출 바로 위에 달아 두었습니다.
- `.pipeline/README.md`의 manual cleanup 계약 문단을 구현에 맞춰 다시 적었습니다. "pattern override를 걸어도 tracked fixture는 `PROTECT`로 건너뛰고 generated workspace만 실제로 삭제한다"는 사실을 명시해, README와 스크립트의 진술이 어긋나지 않게 했습니다. `smoke-three-agent-arbitration.sh` / `smoke-implement-blocked-auto-triage.sh`의 caller 동작 설명은 손대지 않았습니다.
- `tests/test_pipeline_smoke_cleanup.py`에 `test_manual_cleanup_script_protects_tracked_under_pattern_override` 회귀를 추가했습니다. 이 테스트는:
  - 임시 git repo 안에 tracked `live-blocked-smoke-TRACKED` fixture와 untracked `live-blocked-smoke-*` 3개를 mtime 차등으로 심고,
  - 실제 `.pipeline/cleanup-old-smoke-dirs.sh` 스크립트 사본을 `bash <script> <project_root>` 로 그대로 실행하며,
  - `PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*'` + `PIPELINE_SMOKE_KEEP_RECENT=1`로 override했을 때 tracked dir이 `PROTECT`로만 분류되고 `DELETE`로 찍히지 않는다는 것을 dry-run과 live 두 경로 모두에서 확인합니다.
  - live 실행 뒤에도 tracked fixture는 남고, newest untracked 1개는 유지되며, 나머지 untracked 2개는 실제로 삭제된 것을 assertion합니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_smoke_cleanup` → 4/4 pass (기존 3 + 신규 1)
- `bash -n .pipeline/smoke-cleanup-lib.sh .pipeline/cleanup-old-smoke-dirs.sh`
- `git diff --check -- .pipeline/cleanup-old-smoke-dirs.sh .pipeline/README.md tests/test_pipeline_smoke_cleanup.py`

## 남은 리스크
- `prune_smoke_dirs`의 `protect_tracked=1` 경로는 smoke_root가 git repo 안쪽일 때만 의미 있습니다. 지금 manual / auto caller는 모두 `.pipeline/`에서만 쓰이므로 정상이지만, 외부 경로를 받는 새 호출 지점이 생기면 `git ls-files`가 조용히 "아무 것도 보호하지 않음"으로 fallback할 수 있으니 caller를 추가할 때 이 전제를 확인해야 합니다.
- 이번 라운드는 계약 쪽만 닫았습니다. 체크인된 `.pipeline/live-blocked-smoke-*` fixture 디렉터리의 실제 위치/크기 정리는 별도 slice로 남겨 뒀고, scope limit상 이번에 건드리지 않았습니다.
- `protect_tracked=1`은 `DELETE`가 찍힐 후보에만 걸립니다. `KEEP` window 안쪽 디렉터리는 tracked 여부와 무관하게 항상 남기므로, 운영자가 tracked 디렉터리를 포함한 pattern을 잘못 override해도 최소한 `rm -rf`는 발생하지 않습니다.
