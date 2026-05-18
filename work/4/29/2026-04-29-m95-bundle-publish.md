# 2026-04-29 M95 번들 커밋/Push/PR 퍼블리시

## PR #85 — feat/m95-bundle (base: feat/m94-bundle / parent: PR #84)

커밋 1 (`3ae53e5`): feat(M95 Axis 1): add navigate-to-preference link in applied preferences popover
- `app/frontend/src/components/MessageBubble.tsx`
- `app/frontend/src/components/PreferencePanel.tsx`

커밋 2 (`c24c303`): feat(M95 Axis 2): dist rebuild reflecting M95 Axis 1 navigation wiring
- `app/static/dist/assets/index.js` (git add -f)
- `app/static/dist/assets/index.css` (git add -f)

커밋 3 (`18a246e`): docs(M95): sync MILESTONES + TASK_BACKLOG for M95 Axis 1-2 completion
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 실행 결과

| 단계 | 결과 |
|------|------|
| `git switch -c feat/m95-bundle` | ✓ feat/m94-bundle(03bf213) 기준 |
| 커밋 1 (3ae53e5) | ✓ 2 files, 10 ins |
| 커밋 2 (c24c303) | ✓ 2 files (dist -f) |
| 커밋 3 (18a246e) | ✓ 2 files, 16 ins |
| `git push origin feat/m95-bundle` | ✓ |
| PR #85 생성 (base: feat/m94-bundle) | ✓ https://github.com/hsnasforum/projectH/pull/85 |

## 남은 리스크

- PR #71-#85 전체 머지: operator 결정 대기.
- PR #85는 feat/m94-bundle (PR #84)에 스택됨. #84 머지 후 base를 main으로 retarget 필요.
- M96 방향: main 머지 후 fresh advisory 결정.
