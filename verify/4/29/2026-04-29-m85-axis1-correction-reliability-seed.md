STATUS: verified
CONTROL_SEQ: 1309
BASED_ON_WORK: work/4/29/2026-04-29-m85-axis1-correction-reliability-seed.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1309

---

# 2026-04-29 M85 Axis 1 — correction reliability seed — verify

## 이번 라운드 범위

backend-only. `storage/preference_utils.py` 헬퍼 추가 +
`storage/preference_store.py`, `storage/sqlite/preference.py` 파라미터 추가 +
`app/handlers/corrections.py` 호출 변경 + 테스트 2파일.
dist·E2E·frontend 변경 없음.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `py_compile` (변경 6파일 전체) | **PASS** |
| `tests.test_correction_summary + tests.test_preference_store` | **Ran 39 tests — OK** |
| `tests.test_preference_handler` | **Ran 20 tests — OK** |
| `tests.test_sqlite_store` | **Ran 43 tests — OK** |
| `tests.test_watcher_core` (회귀) | **Ran 208 tests — OK** |
| `git diff --check` (변경 6파일) | **PASS** |

> `test_watcher_core` 208건 = 현재 브랜치 기준 정상 (stale cancel guard 7건은
> `fix/stale-advisory-cancel-guard`에 커밋됨, 이 브랜치 미포함).

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `seed_reliability_from_recurrence` 헬퍼 | ✓ `storage/preference_utils.py:16` |
| `initial_reliability_stats` 파라미터 (JSON store) | ✓ `storage/preference_store.py:273` |
| `initial_reliability_stats` 파라미터 (SQLite store) | ✓ `storage/sqlite/preference.py:100` |
| 신규 record 생성 시에만 seed 저장 | ✓ `:319–320`, sqlite `:169–170` |
| idempotent 경로에서 기존 stats 보존 | ✓ |
| `promote_correction_pattern` recurrence_count seed 전달 | ✓ `corrections.py:130` |
| 신규 테스트 1: 승격 시 seed 저장 (`test_promote_pattern_seeds_reliability_from_recurrence`) | ✓ recurrence=3 → applied_count=3 |
| 신규 테스트 2: idempotent 보존 (`test_record_reviewed_candidate_preserves_existing_reliability_stats`) | ✓ 재호출 시 최초 stats 유지 |
| dist·E2E·frontend 미수정 | ✓ |

## Dirty Tree (현재 브랜치: feat/m84-doc-sync-m81-m83)

| 파일 | 라운드 | 상태 |
|------|--------|------|
| `storage/preference_utils.py` | M85 Axis 1 | M (uncommitted) |
| `storage/preference_store.py` | M85 Axis 1 | M (uncommitted) |
| `storage/sqlite/preference.py` | M85 Axis 1 | M (uncommitted) |
| `app/handlers/corrections.py` | M85 Axis 1 | M (uncommitted) |
| `tests/test_correction_summary.py` | M85 Axis 1 | M (uncommitted) |
| `tests/test_preference_store.py` | M85 Axis 1 | M (uncommitted) |

## 남은 리스크

- M85 Axis 2 (PreferencePanel reliability UI): PR #69 머지 후 구현. 현재 미착수.
- 전체 PR 스택 (#62–#72): operator 머지 대기.
- E2E / browser smoke: backend-only 변경 — 불필요.
