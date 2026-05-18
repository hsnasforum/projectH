STATUS: verified
CONTROL_SEQ: 1425
BASED_ON_WORK: work/4/29/2026-04-29-gemini-active-advisory-recovery.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1425

---

# 2026-04-29 Gemini Active Advisory Stuck Recovery — verify

## 이번 라운드 범위

`pane_text_busy_age_seconds()` 파서 추가 (`pipeline_runtime/lane_surface.py`).
`_stale_advisory_recovery_marker()` 업데이트 — request age + pane visible busy age 이중 판정 (`watcher_core.py`).
실제 busy Gemini pane에 Escape를 보내 stuck thinking을 취소하는 회복 경로 추가.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `py_compile watcher_core.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py` | **PASS** |
| 3건 targeted regression tests | **OK** |
| `git diff --check` (3개 파일) | **PASS** |
| `pane_text_busy_age_seconds` 파서 존재 | ✓ `lane_surface.py:191` |
| `_stale_advisory_recovery_marker` 업데이트 | ✓ `watcher_core.py:2114,2154` |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `pane_text_busy_age_seconds()` 추가 | ✓ |
| `_stale_advisory_recovery_marker()` pane busy age 활용 | ✓ |
| regression: `36m 33s` busy age → recovery 조건 만족 | ✓ |
| regression: current advice 있을 때 skip | ✓ |

## Dirty Tree (브랜치: feat/m96-bundle, HEAD 31d4aa5)

| 파일 | 출처 | 상태 |
|------|------|------|
| `pipeline_runtime/lane_surface.py` | advisory recovery fix | M (uncommitted) |
| `watcher_core.py` | advisory recovery fix | M (uncommitted) |
| `tests/test_watcher_core.py` | advisory recovery fix | M (uncommitted) |

## 남은 리스크

- 전체 watcher unittest 미실행 (타겟 3건만).
- 신규 bundle 커밋/push/PR 승인 필요.
- M96 머지 게이트 (operator_request CONTROL_SEQ 1423)는 병렬 유지.
