STATUS: verified
CONTROL_SEQ: 1228
BASED_ON_WORK: work/4/28/2026-04-28-m66-axis1-correction-pattern-dismiss.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1227
VERIFIED_BY: Claude
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1228

---

# 2026-04-28 M66 Axis 1 — Correction Pattern Dismiss 검증

## 이번 라운드 범위

`contracts.py` RECORDED→STOPPED 전이 + JSON/SQLite `dismiss_by_fingerprint()` +
`POST /api/corrections/dismiss-pattern` + frontend 무시 버튼 + 단위 테스트 + `docs/MILESTONES.md`.
dist 재빌드 / E2E 변경 없음 (Axis 2 대상).

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile <5개 backend 파일>` | **PASS** (exit 0) |
| `python3 -m unittest tests.test_correction_store tests.test_sqlite_store` | **62 tests OK** |
| `tsc --noEmit --project app/frontend/tsconfig.json` | **PASS** (exit 0) |
| `git diff --check -- <10개 파일>` | **PASS** (exit 0) |

## 구현 클레임 확인

| 클레임 | 위치 | 확인 결과 |
|--------|------|---------|
| `CORRECTION_STATUS_TRANSITIONS[RECORDED]` STOPPED 추가 | `contracts.py:415` | ✓ |
| `CorrectionStore.dismiss_by_fingerprint()` | `correction_store.py:138` | ✓ |
| `SQLiteCorrectionStore.dismiss_by_fingerprint()` | `sqlite_store.py:926` | ✓ |
| `dismiss_correction_pattern()` 핸들러 | `aggregate.py:77` | ✓ |
| `"/api/corrections/dismiss-pattern"` POST 허용 + 라우팅 | `web.py:403, 421–422` | ✓ |
| `dismissCorrectionPattern()` fetch 함수 | `client.ts:347` | ✓ |
| `data-testid="correction-dismiss-pattern"` 버튼 | `PreferencePanel.tsx:327` | ✓ |
| `test_dismiss_by_fingerprint` (JSON) | `test_correction_store.py:257` | ✓ |
| `test_dismiss_by_fingerprint_batch` (SQLite) | `test_sqlite_store.py:699` | ✓ |
| dist / E2E 미수정 | — | ✓ |
| commit / push 미실행 | — | ✓ |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `core/contracts.py` | 수정됨, 미커밋 | M66 Axis 1 |
| `storage/correction_store.py` | 수정됨, 미커밋 | M66 Axis 1 |
| `storage/sqlite_store.py` | 수정됨, 미커밋 | M66 Axis 1 |
| `app/handlers/aggregate.py` | 수정됨, 미커밋 | M66 Axis 1 |
| `app/web.py` | 수정됨, 미커밋 | M66 Axis 1 |
| `app/frontend/src/api/client.ts` | 수정됨, 미커밋 | M66 Axis 1 |
| `app/frontend/src/components/PreferencePanel.tsx` | 수정됨, 미커밋 | M66 Axis 1 |
| `tests/test_correction_store.py` | 수정됨, 미커밋 | M66 Axis 1 |
| `tests/test_sqlite_store.py` | 수정됨, 미커밋 | M66 Axis 1 |
| `docs/MILESTONES.md` | 수정됨, 미커밋 | M66 Axis 1 |

현재 브랜치: `feat/m50-axis1-axis2-pref-visibility` (PR #52 OPEN)
HEAD: `7054fa3` (M65 Axis 1)

## 남은 리스크

- `app/static/dist/` 재빌드 미실행 — browser 무시 버튼 표시 미확인
- `data-testid="correction-dismiss-pattern"` Playwright 미검증 — Axis 2 대상
- 전체 unittest / E2E 미실행 (좁은 scope 정책대로)

## 다음 행동

M66 Axis 1 완료. 10개 파일 커밋+푸시 → M66 Axis 2 (dist 재빌드 + E2E 격리).
→ `implement_handoff.md` CONTROL_SEQ 1228.
