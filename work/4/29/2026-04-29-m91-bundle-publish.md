# 2026-04-29 M91 번들 커밋/Push/PR 퍼블리시

## PR #81 — feat/m91-bundle (base: feat/m90-bundle / parent: PR #80)

커밋 1 (`583d9a6`): feat(M91 Axis 1): use candidatePreferences for candidate tab filteredPreferences
- `app/frontend/src/components/PreferencePanel.tsx`

커밋 2 (`649c0ab`): feat(M91 Axis 2): dist rebuild reflecting M91 Axis 1 candidate tab wiring
- `app/static/dist/assets/index.js` (git add -f)

커밋 3 (`a96eecf`): docs(M91): sync MILESTONES + TASK_BACKLOG for M91 Axis 1-2 completion
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 실행 결과

| 단계 | 결과 |
|------|------|
| `git switch -c feat/m91-bundle` | ✓ feat/m90-bundle(6f4d423) 기준 |
| 커밋 1 (583d9a6) | ✓ 1 file, 2 ins |
| 커밋 2 (649c0ab) | ✓ 1 file (dist -f) |
| 커밋 3 (a96eecf) | ✓ 2 files, 13 ins |
| `git push origin feat/m91-bundle` | ✓ |
| PR #81 생성 (base: feat/m90-bundle) | ✓ https://github.com/hsnasforum/projectH/pull/81 |

## 남은 리스크

- PR #71-#81 전체 머지: operator 결정 대기.
- PR #81은 feat/m90-bundle (PR #80)에 스택됨. #80 머지 후 base를 main으로 retarget 필요.
- M92 방향: main 머지 후 fresh advisory 결정.
