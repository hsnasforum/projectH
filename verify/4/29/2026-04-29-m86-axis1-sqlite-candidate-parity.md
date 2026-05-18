STATUS: verified
CONTROL_SEQ: 1321
BASED_ON_WORK: work/4/29/2026-04-29-m86-axis1-sqlite-candidate-parity.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1321

---

# 2026-04-29 M86 Axis 1 — SQLitePreferenceStore 후보 조회 parity — verify

## 이번 라운드 범위

`SQLitePreferenceStore`에 JSON `PreferenceStore`와 대칭되는 `get_candidates()` 및
`find_by_fingerprint()` 공개 메서드 추가. 핸드오프 명세 대비 추가 개선:
- `_record_from_row()` private helper 추출로 row→PreferenceRecord 변환 로직 중복 제거
- 기존 `list_all()`도 동일 helper로 통일

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `py_compile storage/sqlite/preference.py tests/test_sqlite_store.py` | **PASS** |
| `python3 -m unittest -v tests.test_sqlite_store` | **45 tests OK** — 신규 2건 포함 |
| `python3 -m unittest -v tests.test_preference_store` | **34 tests OK** — 회귀 없음 |
| `git diff --check -- storage/sqlite/preference.py tests/test_sqlite_store.py` | **PASS** |
| `git diff --name-only -- app app/static/dist e2e` | **출력 없음** — dist/E2E 미변경 |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `get_candidates(limit=50)` 추가 — `status='candidate'`, `updated_at DESC` | ✓ `preference.py:67` |
| `find_by_fingerprint(delta_fingerprint)` 추가 — hit/None | ✓ `preference.py:80` |
| `_record_from_row()` helper 추출 — 유효성 검사 포함 | ✓ `preference.py:54` |
| `list_all()` 동일 helper 사용 — 변환 방식 통일 | ✓ `preference.py:90` |
| `test_sqlite_get_candidates_returns_only_candidate_status` 신규 | ✓ `test_sqlite_store.py` |
| `test_sqlite_find_by_fingerprint_returns_record_and_none` 신규 | ✓ `test_sqlite_store.py` |

## Dirty Tree (브랜치: feat/m85-axis3-dist-e2e)

| 파일 | 상태 |
|------|------|
| `storage/sqlite/preference.py` | M (uncommitted) |
| `tests/test_sqlite_store.py` | M (uncommitted) |

app/dist/e2e 변경 없음.

## 남은 리스크

- 브랜치 생성은 `.git/refs` 쓰기 제한으로 수행하지 못했다. 변경은 feat/m85-axis3-dist-e2e 작업트리에 uncommitted 상태.
- PR #71-#75 + M85/M86: operator 머지 대기.
- `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`에 M85·M86 Axis 1 미반영. doc sync 별도 라운드 대상.
- broad unittest / browser E2E: backend-only 변경 범위라 실행하지 않았음.
