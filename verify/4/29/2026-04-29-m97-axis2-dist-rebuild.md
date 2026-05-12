STATUS: verified
CONTROL_SEQ: 1435
BASED_ON_WORK: work/4/29/2026-04-29-m97-axis2-dist-rebuild.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1435

---

# 2026-04-29 M97 Axis 2 dist 재빌드 — verify

## 이번 라운드 범위

`npx vite build` 실행 → `app/static/dist/assets/index.js` + `index.css` 갱신.
M97 Axis 1 source 변경(11개 파일)과 Axis 2 dist(2개 파일), 총 13개 uncommitted 파일로 번들 구성.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `ls -lh app/static/dist/assets/index.js` | **315K** ✓ |
| `grep -c "preference-auto-activated-notice" index.js` | **1** ✓ |
| `git diff --check -- app/static/dist/assets/index.js` | **PASS** |
| Playwright E2E smoke | **미실행** — sandbox socket 제한 (CI 위임) |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `npx vite build` 성공 | ✓ (work 노트 검증, 315K output 일치) |
| `preference-auto-activated-notice` dist에 포함 | ✓ count=1 직접 확인 |
| React source 추가 수정 없음 | ✓ dirty tree 동일 (Axis 1과 동일 11개 source) |

## Dirty Tree (브랜치: fix/advisory-recovery-pane-busy-age, HEAD 939dcf8)

### M97 Axis 1 (uncommitted)

| 파일 | 분류 |
|------|------|
| `app/handlers/feedback.py` | backend |
| `app/frontend/src/App.tsx` | frontend |
| `app/frontend/src/api/client.ts` | frontend |
| `app/frontend/src/components/PreferencePanel.tsx` | frontend |
| `app/frontend/src/components/Sidebar.tsx` | frontend |
| `e2e/tests/web-smoke.spec.mjs` | E2E |
| `README.md` | docs |
| `docs/PRODUCT_SPEC.md` | docs |
| `docs/ACCEPTANCE_CRITERIA.md` | docs |
| `docs/MILESTONES.md` | docs |
| `docs/TASK_BACKLOG.md` | docs |

### M97 Axis 2 (uncommitted)

| 파일 | 분류 |
|------|------|
| `app/static/dist/assets/index.js` | dist |
| `app/static/dist/assets/index.css` | dist |

## 남은 리스크

- Playwright E2E 미실행 (sandbox socket 제한): CI 환경에서 확인 필요.
- 13개 파일 전체 미커밋 — `commit_push_bundle_authorization` 처리 필요.
- M97 브랜치 전략: 현재 HEAD가 `fix/advisory-recovery-pane-busy-age`(939dcf8). `feat/m97-axis1-bundle` 신규 브랜치로 분리 후 PR 생성 (base: `fix/advisory-recovery-pane-busy-age`, parent 머지 후 main으로 리타겟).
