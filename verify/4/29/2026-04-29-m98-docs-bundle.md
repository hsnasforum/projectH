STATUS: verified
CONTROL_SEQ: 1443
BASED_ON_WORK: work/4/29/2026-04-29-m98-docs-bundle.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1444

---

# 2026-04-29 M98 docs 번들 — verify

## 이번 라운드 범위

CONTROL_SEQ 1443 handoff에 따라 docs-only 5개 파일 동기화:
`README.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`,
`docs/ACCEPTANCE_CRITERIA.md`, `docs/PRODUCT_SPEC.md`.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `git diff --check -- (5개 docs 파일)` | **PASS** |
| `correction-detail-panel` docs 내 존재 | ✓ ACCEPTANCE_CRITERIA.md ×3, PRODUCT_SPEC.md ×2 |
| `fetchCorrectionDetail` docs 내 존재 | ✓ ACCEPTANCE_CRITERIA.md ×3, PRODUCT_SPEC.md ×2 |
| `GET /api/corrections/<correction_id>` docs 내 존재 | ✓ README.md, MILESTONES.md, ACCEPTANCE_CRITERIA.md, PRODUCT_SPEC.md |
| M98 Axis 1-2 완료 TASK_BACKLOG 반영 | ✓ TASK_BACKLOG.md 9행 |
| 코드·dist·E2E 추가 수정 없음 | ✓ (docs-only 범위 준수) |

## 전체 M98 Dirty Tree (브랜치: feat/m97-axis1-bundle)

tracked 수정 파일 정확히 12개 — 모두 `origin/feat/m96-bundle` 기준 변경됨:

| 파일 | 라운드 |
|------|-------|
| `app/handlers/corrections.py` | Axis 1 |
| `app/web.py` | Axis 1 |
| `app/frontend/src/api/client.ts` | Axis 1 |
| `app/frontend/src/components/PreferencePanel.tsx` | Axis 1 |
| `e2e/tests/web-smoke.spec.mjs` | Axis 1 |
| `app/static/dist/assets/index.js` | Axis 2 |
| `app/static/dist/assets/index.css` | Axis 2 |
| `README.md` | docs |
| `docs/MILESTONES.md` | docs |
| `docs/TASK_BACKLOG.md` | docs |
| `docs/ACCEPTANCE_CRITERIA.md` | docs |
| `docs/PRODUCT_SPEC.md` | docs |

다른 tracked 수정 파일 없음. untracked 파일(`work/`, `verify/`, `report/`) 은 커밋 대상 아님.

## 남은 리스크

- Playwright E2E `correction list item click shows correction detail panel` CI 첫 실행.
- 브랜치 생성 + commit/push/PR: `.git` 쓰기 제한으로 implement lane에서 미처리 — operator gate 대상.
- PR 대상 브랜치: `feat/m96-bundle` (PR #90과 동일 패턴).
