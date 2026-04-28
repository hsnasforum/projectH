STATUS: verified
CONTROL_SEQ: 1232
BASED_ON_WORK: work/4/28/2026-04-28-m67-axis1-correction-list-recent-view.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1231
VERIFIED_BY: Claude
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1232

---

# 2026-04-28 M67 Axis 1 — Correction List Recent View 검증

## 이번 라운드 범위

`get_correction_list()` handler + `GET /api/corrections/list` route +
단위 테스트 2개 + `CorrectionListResponse`/`CorrectionListItem` 타입 + `fetchCorrectionList()` +
`PreferencePanel.tsx` 최근 교정 compact 목록 + `docs/MILESTONES.md`.
dist 재빌드 / E2E 변경 없음 (Axis 2 대상).

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile aggregate.py web.py` | **PASS** (exit 0) |
| `python3 -m unittest -v tests.test_correction_summary` | **4 tests OK** |
| `tsc --noEmit --project app/frontend/tsconfig.json` | **PASS** (exit 0) |
| `git diff --check -- <6개 파일>` | **PASS** (exit 0) |

## 구현 클레임 확인

| 클레임 | 위치 | 확인 결과 |
|--------|------|---------|
| `get_correction_list()` handler | `aggregate.py:70` | ✓ |
| `GET /api/corrections/list` route | `web.py:357–359` | ✓ |
| `test_correction_list_empty_store` | `test_correction_summary.py:64` | ✓ |
| `test_correction_list_returns_recent` | `test_correction_summary.py:73` | ✓ |
| `CorrectionListItem` / `CorrectionListResponse` 타입 | `client.ts:335, 344` | ✓ |
| `fetchCorrectionList()` | `client.ts:349` | ✓ |
| `correctionList` state | `PreferencePanel.tsx:71` | ✓ |
| `fetchCorrectionList().catch(() => null)` load() 추가 | `PreferencePanel.tsx:96` | ✓ |
| `data-testid="correction-list-item"` compact 목록 | `PreferencePanel.tsx:349` | ✓ |
| M67 Axis 1 MILESTONES.md 항목 | confirmed | ✓ |
| storage 파일 / dist / E2E 미수정 | — | ✓ |
| commit / push 미실행 | — | ✓ |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `app/handlers/aggregate.py` | 수정됨, 미커밋 | M67 Axis 1 |
| `app/web.py` | 수정됨, 미커밋 | M67 Axis 1 |
| `tests/test_correction_summary.py` | 수정됨, 미커밋 | M67 Axis 1 |
| `app/frontend/src/api/client.ts` | 수정됨, 미커밋 | M67 Axis 1 |
| `app/frontend/src/components/PreferencePanel.tsx` | 수정됨, 미커밋 | M67 Axis 1 |
| `docs/MILESTONES.md` | 수정됨, 미커밋 | M67 Axis 1 |

현재 브랜치: `feat/m50-axis1-axis2-pref-visibility` (PR #52 OPEN)
HEAD: `5495b30` (M66 Axis 2)

## 남은 리스크

- `app/static/dist/` 재빌드 미실행 — browser 최근 교정 목록 표시 미확인
- `data-testid="correction-list-item"` Playwright 미검증 — Axis 2 대상
- playwright_socket_denied 반복 패턴 — verify 소유자가 Axis 2 E2E 흡수 예정

## 다음 행동

M67 Axis 1 완료. 6개 파일 커밋+푸시 → M67 Axis 2 (dist 재빌드 + E2E 격리).
→ `implement_handoff.md` CONTROL_SEQ 1232.
