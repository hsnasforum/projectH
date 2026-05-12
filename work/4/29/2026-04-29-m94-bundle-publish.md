# 2026-04-29 M94 번들 커밋/Push/PR 퍼블리시

## PR #84 — feat/m94-bundle (base: feat/m93-bundle / parent: PR #83)

커밋 1 (`3ea4b19`): feat(M94 Axis 1): add is_highly_reliable badge to applied preferences popover
- `app/frontend/src/components/MessageBubble.tsx`

커밋 2 (`cb88ed2`): feat(M94 Axis 2): dist rebuild + E2E popover fixture stabilization
- `app/static/dist/assets/index.js` (git add -f)
- `e2e/tests/web-smoke.spec.mjs`

커밋 3 (`03bf213`): docs(M94): sync MILESTONES + TASK_BACKLOG for M94 Axis 1-2 completion
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 실행 결과

| 단계 | 결과 |
|------|------|
| `git switch -c feat/m94-bundle` | ✓ feat/m93-bundle(2b5d2cf) 기준 |
| 커밋 1 (3ea4b19) | ✓ 1 file, 6 ins |
| 커밋 2 (cb88ed2) | ✓ 2 files (dist -f + e2e) |
| 커밋 3 (03bf213) | ✓ 2 files, 15 ins |
| `git push origin feat/m94-bundle` | ✓ |
| PR #84 생성 (base: feat/m93-bundle) | ✓ https://github.com/hsnasforum/projectH/pull/84 |

## 남은 리스크

- PR #71-#84 전체 머지: operator 결정 대기.
- PR #84는 feat/m93-bundle (PR #83)에 스택됨. #83 머지 후 base를 main으로 retarget 필요.
- M95 방향: main 머지 후 fresh advisory 결정.
