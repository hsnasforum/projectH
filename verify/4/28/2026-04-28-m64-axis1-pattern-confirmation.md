STATUS: verified
CONTROL_SEQ: 1222
BASED_ON_WORK: work/4/28/2026-04-28-m64-axis1-pattern-confirmation.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1221
VERIFIED_BY: Claude
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1222

---

# 2026-04-28 M64 Axis 1 — Pattern Confirmation 검증

## 이번 라운드 범위

`CorrectionStore.confirm_by_fingerprint()` + 단위 테스트 + `confirm_correction_pattern()` 핸들러 +
`POST /api/corrections/confirm-pattern` 라우트 + `confirmCorrectionPattern()` 클라이언트 함수 +
`PreferencePanel.tsx` 승인 버튼 + `docs/MILESTONES.md`.
dist 재빌드 / E2E 변경 없음 (Axis 2 대상).

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile correction_store.py aggregate.py web.py` | **PASS** (exit 0) |
| `python3 -m unittest -v tests.test_correction_store` | **28 tests OK** |
| `tsc --noEmit --project app/frontend/tsconfig.json` | **PASS** (exit 0) |
| `git diff --check -- <7개 파일>` | **PASS** (exit 0) |

## 구현 클레임 확인

| 클레임 | 위치 | 확인 결과 |
|--------|------|---------|
| `confirm_by_fingerprint()` | `correction_store.py:138` | ✓ |
| `test_confirm_by_fingerprint` | `test_correction_store.py:230` | ✓ |
| `confirm_correction_pattern()` 핸들러 | `aggregate.py:70` | ✓ |
| `"/api/corrections/confirm-pattern"` POST 허용 + 라우팅 | `web.py:402, 416–417` | ✓ |
| `confirmCorrectionPattern()` fetch 함수 | `client.ts:335` | ✓ |
| `data-testid="correction-confirm-pattern"` 버튼 | `PreferencePanel.tsx:315` | ✓ |
| `onClick` → `confirmCorrectionPattern(fp)` + `load()` | `PreferencePanel.tsx:319` | ✓ |
| M64 Axis 1 MILESTONES.md 항목 | confirmed | ✓ |
| `CORRECTION_STATUS_TRANSITIONS` / dist / E2E 미수정 | — | ✓ |
| commit / push 미실행 | — | ✓ |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `storage/correction_store.py` | 수정됨, 미커밋 | M64 Axis 1 |
| `tests/test_correction_store.py` | 수정됨, 미커밋 | M64 Axis 1 |
| `app/handlers/aggregate.py` | 수정됨, 미커밋 | M64 Axis 1 |
| `app/web.py` | 수정됨, 미커밋 | M64 Axis 1 |
| `app/frontend/src/api/client.ts` | 수정됨, 미커밋 | M64 Axis 1 |
| `app/frontend/src/components/PreferencePanel.tsx` | 수정됨, 미커밋 | M64 Axis 1 |
| `docs/MILESTONES.md` | 수정됨, 미커밋 | M64 Axis 1 |

현재 브랜치: `feat/m50-axis1-axis2-pref-visibility` (PR #52 OPEN)
HEAD: `b9adb33` (M63 Axis 2)

## 남은 리스크

- `app/static/dist/` 재빌드 미실행 — browser 실제 버튼 표시 미확인
- `data-testid="correction-confirm-pattern"` Playwright 미검증 — Axis 2 대상
- `storage/sqlite_store.py` parity 미포함 — handoff 경계대로
- 전체 unittest / E2E 미실행 (좁은 scope 정책대로)

## 다음 행동

M64 Axis 1 완료. 7개 파일 커밋+푸시 → M64 Axis 2 (dist 재빌드 + 승인 버튼 E2E 격리).
→ `implement_handoff.md` CONTROL_SEQ 1222.
