# 2026-04-30 M105 correction history status filter 번들 publish

## 변경 파일

- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_correction_summary.py`
- `app/static/dist/assets/index.js`
- `app/static/dist/assets/index.css`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/PRODUCT_SPEC.md`
- `work/4/30/2026-04-30-m105-publish-bundle.md`

## 실행 내용

- `operator_request.md` CONTROL_SEQ 1470 (`commit_push_bundle_authorization + internal_only + pr_creation_gate`)를
  operator_retriage 라운드에서 직접 처리했다.
- 오늘 3+ docs-only 규칙 적용: docs 4개를 operator_retriage 인라인 편집 후 코드와 함께 단일 커밋.
- PR #96 (`fix/m104-preference-text-edit`)이 draft 대기 중이므로 `fix/m104-preference-text-edit`를 base로 사용.

## 결과

| 항목 | 결과 |
|------|------|
| 커밋 SHA | `3077b17` |
| 브랜치 | `fix/m105-correction-status-filter` |
| push | ✓ `origin/fix/m105-correction-status-filter` |
| PR 생성 | ✓ [#97](https://github.com/hsnasforum/projectH/pull/97) — draft, base: `fix/m104-preference-text-edit` |
| 변경 통계 | 9 files changed, 254 insertions(+), 68 deletions(-) |

## 스태킹 링크

| PR | 브랜치 | base | 상태 |
|----|--------|------|------|
| #91–#96 | 이전 스택 | — | draft |
| #97 | `fix/m105-correction-status-filter` | `fix/m104-preference-text-edit` | draft |

## 남은 리스크

- PR #91–#97 모두 draft, `pr_merge_gate` operator 대기
- Playwright E2E 4개 시나리오 CI 위임
- M106 다음 슬라이스 advisory 대기
