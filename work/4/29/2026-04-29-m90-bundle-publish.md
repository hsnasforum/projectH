# 2026-04-29 M90 번들 커밋/Push/PR 퍼블리시

## 변경 파일 (이번 라운드 직접 실행)

commit/push/PR 생성 + docs 업데이트 수행.

### PR #80 — feat/m90-bundle (base: feat/m89-bundle / parent: PR #79)

커밋 1 (`3307705`): feat(M90 Axis 1): wire candidate_preferences state into PreferencePanel
- `app/frontend/src/components/PreferencePanel.tsx`

커밋 2 (`5ad04d9`): feat(M90 Axis 2): dist rebuild + E2E preference-not-applied-btn stabilization
- `app/static/dist/assets/index.js` (git add -f — dist는 tracked이지만 .gitignore에 포함)
- `e2e/tests/web-smoke.spec.mjs`

커밋 3 (`6f4d423`): docs(M90): sync MILESTONES + TASK_BACKLOG for M90 Axis 1-2 completion
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 실행 결과

| 단계 | 결과 |
|------|------|
| `git switch -c feat/m90-bundle` | ✓ feat/m89-bundle(093a1ff) 기준 새 브랜치 |
| 커밋 1 (M90 Axis 1, 3307705) | ✓ 1 file, 5 ins |
| 커밋 2 (M90 Axis 2, 5ad04d9) | ✓ 2 files, 67 ins / 56 del (dist -f 포함) |
| 커밋 3 (docs, 6f4d423) | ✓ 2 files, 15 ins / 3 del |
| `git push origin feat/m90-bundle` | ✓ |
| PR #80 생성 (base: feat/m89-bundle) | ✓ https://github.com/hsnasforum/projectH/pull/80 |

## 남은 리스크

- PR #71-#80 전체 머지: operator 결정 대기.
- PR #80은 feat/m89-bundle (PR #79)에 스택됨. #79 머지 후 base를 main으로 retarget 필요.
- M91 방향: M90 완료 후 다음 기능 축은 main 머지 후 fresh advisory 결정.
