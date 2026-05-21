# verify: 2026-05-22 ArtifactScanner extraction (A3 Step 4)

## 검증 결과: READY — 268개 통과

| 검사 | 결과 |
|---|---|
| `py_compile` watcher_core / watcher_artifact_scanner | PASS |
| `unittest` test_watcher_artifact_scanner 4개 + test_watcher_core 264개 | PASS |
| import smoke | OK |
| `git diff --check` | PASS |

## 주목: schema.py 재사용

`is_canonical_round_note()`, `latest_verify_note_for_work()`,
`same_day_verify_dir_for_work()`, `normalize_repo_artifact_path()` 재사용.
`latest_round_markdown()`은 정렬/반환 계약 차이로 미사용. 올바른 판단.

## watcher_core.py 줄 수 추이

| 슬라이스 | 줄 수 | 감소 |
|---|---|---|
| 원본 | 4498 | — |
| Step 1 모듈 함수 이동 | 4430 | −68 |
| Step 2 ControlSignalReader | 4385 | −45 |
| Step 3 JobStateManager | 4323 | −62 |
| Step 4 ArtifactScanner | 4131 | −192 |
| **누계** | **4131** | **−367 (−8.2%)** |
