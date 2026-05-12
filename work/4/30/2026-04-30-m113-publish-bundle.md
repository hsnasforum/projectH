# 2026-04-30 M113 review queue 액션 인라인 이동 번들 publish

## 변경 파일

- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `app/static/dist/assets/index.js`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/PRODUCT_SPEC.md`
- `work/4/30/2026-04-30-m113-publish-bundle.md`

## 실행 내용

- `operator_request.md` CONTROL_SEQ 1507 처리 (operator_retriage 인라인).
- 3+ docs-only 규칙: docs 4개를 인라인 편집 후 코드와 함께 단일 커밋.
- 브랜치 `feat/m113-review-queue-inline-actions` (base: `feat/m112-review-queue-badges`) 생성.

## 결과

| 항목 | 결과 |
|------|------|
| 커밋 SHA | `e49d6fb` |
| 브랜치 | `feat/m113-review-queue-inline-actions` |
| push | ✓ `origin/feat/m113-review-queue-inline-actions` |
| PR 생성 | ✓ [#106](https://github.com/hsnasforum/projectH/pull/106) — draft, base: `feat/m112-review-queue-badges` |
| 변경 통계 | 7 files changed, 234 insertions(+), 63 deletions(-) |

## 스태킹 링크

PR #91–#105 ← #106 (`feat/m113-review-queue-inline-actions`) — 모두 draft.

## Review Queue UX 아크 현황

| 마일스톤 | 완료 기능 |
|----------|----------|
| M110 | 텍스트 검색 필터 (`review-queue-search-input`) ✓ |
| M111 | 항목 수 헤더 (`review-queue-item-count`) ✓ |
| M112 | 항목 배지 Age/Family/Quality ✓ |
| M113 | 액션 버튼 인라인 이동 (evidence 직후, context 이전) ✓ |

## 남은 리스크

- PR #91–#106 모두 draft, `pr_merge_gate` operator 대기
- Playwright E2E CI 위임
- M114 다음 방향 advisory 대기
