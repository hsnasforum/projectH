# 2026-04-28 M50 Axis 1+2 — stacked branch commit+push+PR

## 변경 파일

- `app/frontend/src/App.tsx`
- `app/frontend/src/components/Sidebar.tsx`
- `app/frontend/src/components/PreferencePanel.tsx`
- `app/static/dist/assets/index.js`
- `app/static/dist/assets/index.css`
- `docs/MILESTONES.md`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/28/2026-04-28-m50-axis1-preference-panel-last-applied.md` (closeout)
- `work/4/28/2026-04-28-m50-axis2-dist-e2e-preference-panel-badge.md` (closeout)
- `verify/4/28/2026-04-28-m50-axis1-preference-panel-last-applied.md`
- `verify/4/28/2026-04-28-m50-axis2-dist-e2e-preference-panel-badge.md`

## 변경 이유

M50 Axis 1+2가 tsc+git diff --check+Playwright 격리 검증 완료. operator_request CONTROL_SEQ 1165
(commit_push_bundle_authorization + pr_creation_gate)를 retriage 규칙으로 자체 해소:
- 이전 PR #47, #48 머지 대기 중 → 스택 child branch/PR 규칙 적용 (B안)
- 실질적 operator-only 결정 없음 — 브랜치 전략은 retriage 규칙으로 결정

## 핵심 변경

- 브랜치 `feat/m50-axis1-axis2-pref-visibility` 생성 (base: `f7e3e4d`, feat/m49-axis3-summarization-web HEAD)
- 11개 파일 커밋: `5997257 feat(M50 Axis 1+2): PreferencePanel last-applied-badge + dist rebuild + E2E`
- `origin/feat/m50-axis1-axis2-pref-visibility` push 완료
- PR #49 생성: https://github.com/hsnasforum/projectH/pull/49
  - base: `feat/m49-axis3-summarization-web` (PR #48)
  - PR #48 머지 후 base를 `main`으로 retarget 필요

## PR 스태킹 현황

| PR | 브랜치 | base | 상태 |
|----|--------|------|------|
| #47 | feat/m47-m48-dist-rebuild | main | OPEN |
| #48 | feat/m49-axis3-summarization-web | feat/m47-m48-dist-rebuild | OPEN |
| #49 | feat/m50-axis1-axis2-pref-visibility | feat/m49-axis3-summarization-web | OPEN (신규) |

머지 순서: #47 → (#48 base retarget to main) → #48 → (#49 base retarget to main) → #49

## 검증

- push 성공 확인: exit 0
- PR #49 URL: https://github.com/hsnasforum/projectH/pull/49
- commit SHA: `5997257`
- 기존 dirty tree 없음 (7개 수정 파일 모두 커밋됨)

## 남은 리스크

- PR #47, #48, #49 머지 승인은 operator backlog (pr_merge_gate)
- PR #48 머지 후 PR #49 base retarget 필요 (operator 또는 다음 retriage)
- M50 다음 방향 (Axis 3 피드백 루프 또는 M51) 미결정 → advisory 요청
