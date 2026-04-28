STATUS: verified
CONTROL_SEQ: 1215
BASED_ON_WORK: work/4/28/2026-04-28-m62-axis1-correction-summary-frontend.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1214
VERIFIED_BY: Claude
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1215

---

# 2026-04-28 M62 Axis 1 — Correction Summary Frontend 표시 검증

## 이번 라운드 범위

`app/frontend/src/api/client.ts` + `app/frontend/src/components/PreferencePanel.tsx` + `docs/MILESTONES.md`.
dist 재빌드 / E2E / backend 변경 없음 (Axis 2 대상).

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `tsc --noEmit --project app/frontend/tsconfig.json` | **PASS** (exit 0) |
| `git diff --check -- client.ts PreferencePanel.tsx MILESTONES.md` | **PASS** (exit 0) |

## 구현 클레임 확인

| 클레임 | 위치 | 확인 결과 |
|--------|------|---------|
| `CorrectionSummary` interface | `client.ts:312` | ✓ |
| `fetchCorrectionSummary()` 함수 | `client.ts:324` | ✓ |
| `correctionSummary` state | `PreferencePanel.tsx:67` | ✓ |
| 병렬 fetch `.catch(() => null)` | `PreferencePanel.tsx:91` | ✓ |
| `setCorrectionSummary(summary)` | `PreferencePanel.tsx:137` | ✓ |
| 컴팩트 교정 통계 렌더 | `PreferencePanel.tsx:293–297` | ✓ |
| M62 Axis 1 ACTIVE 항목 | `docs/MILESTONES.md:1218` | ✓ |
| commit / push / dist 재빌드 미실행 | — | ✓ |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `app/frontend/src/api/client.ts` | 수정됨, 미커밋 | M62 Axis 1 |
| `app/frontend/src/components/PreferencePanel.tsx` | 수정됨, 미커밋 | M62 Axis 1 |
| `docs/MILESTONES.md` | 수정됨, 미커밋 | M62 Axis 1 |

현재 브랜치: `feat/m49-axis3-summarization-web` (PR #52 OPEN)

## 남은 리스크

- `app/static/dist/` 재빌드 미실행 — browser 실제 표시 미확인
- `data-testid` 미부착 — Playwright selector 미고정
- `by_status["active"]` null 분기만 처리; 다른 status 값은 표시 안 됨 (handoff 설계대로)

## 다음 행동

M62 Axis 1 완료. 3개 파일 커밋+푸시 → M62 Axis 2 (dist 재빌드 + data-testid + E2E).
→ `implement_handoff.md` CONTROL_SEQ 1215.
