# 2026-04-29 M98 번들 publish (commit + push + PR)

## 변경 파일

- `app/handlers/corrections.py`
- `app/web.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `app/static/dist/assets/index.js`
- `app/static/dist/assets/index.css`
- `README.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/PRODUCT_SPEC.md`
- `work/4/29/2026-04-29-m98-publish-bundle.md`

## 실행 내용

- `operator_retriage` CONTROL_SEQ 1444에서 `commit_push_bundle_authorization + internal_only + pr_creation_gate`를 verify/handoff 라운드 내 직접 처리했다.
- `git checkout -b feat/m98-axis1-correction-history origin/feat/m96-bundle`으로 신규 브랜치 생성.
- dist 파일은 `.gitignore`에 `dist/`가 포함돼 있으나 `origin/feat/m96-bundle`에서 tracked 상태이므로 `git add -f` 사용.
- 12개 파일 스테이징 후 단일 커밋.

## 결과

| 항목 | 결과 |
|------|------|
| 커밋 SHA | `0d48d9b` |
| 브랜치 | `feat/m98-axis1-correction-history` |
| push | ✓ `origin/feat/m98-axis1-correction-history` |
| PR | [#91](https://github.com/hsnasforum/projectH/pull/91) — draft, base: `feat/m96-bundle` |
| 변경 통계 | 12 files changed, 384 insertions(+), 63 deletions(-) |

## 남은 리스크

- PR #91은 draft 상태. CI 통과 + `pr_merge_gate` operator 승인 후 머지.
- Playwright E2E `correction list item click shows correction detail panel` CI 첫 실행.
- PR #91 머지 후 `feat/m96-bundle → main` publication은 별도 merge gate.
- M99 다음 슬라이스는 advisory 결정 대기.
