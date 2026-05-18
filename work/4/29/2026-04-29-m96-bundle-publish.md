# 2026-04-29 M96 번들 커밋/Push/PR 퍼블리시

## PR #86 — feat/m96-bundle (base: feat/m95-bundle / parent: PR #85)

커밋 1 (`32485b2`): fix(M96 Axis 1): add data-testid to pref-navigate-to-card link
- `app/frontend/src/components/MessageBubble.tsx`

커밋 2 (`b9705bf`): feat(M96 Axis 2): dist rebuild reflecting M96 Axis 1 testid addition
- `app/static/dist/assets/index.js` (git add -f)

커밋 3 (`31d4aa5`): docs(M96): sync MILESTONES + TASK_BACKLOG for M96 Axis 1-2 completion
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 실행 결과

| 단계 | 결과 |
|------|------|
| `git switch -c feat/m96-bundle` | ✓ feat/m95-bundle(18a246e) 기준 |
| 커밋 1 (32485b2) | ✓ 1 file, 1 ins |
| 커밋 2 (b9705bf) | ✓ 1 file (dist -f) |
| 커밋 3 (31d4aa5) | ✓ 2 files, 14 ins |
| `git push origin feat/m96-bundle` | ✓ |
| PR #86 생성 (base: feat/m95-bundle) | ✓ https://github.com/hsnasforum/projectH/pull/86 |

## 남은 리스크

- PR #71-#86 전체 머지: operator 결정 대기.
- PR #86은 feat/m95-bundle (PR #85)에 스택됨. #85 머지 후 base를 main으로 retarget 필요.
- M97 방향: main 머지 후 fresh advisory 결정.
