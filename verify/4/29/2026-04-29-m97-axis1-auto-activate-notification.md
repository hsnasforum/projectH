STATUS: verified
CONTROL_SEQ: 1434
BASED_ON_WORK: work/4/29/2026-04-29-m97-axis1-auto-activate-notification.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1434

---

# 2026-04-29 M97 Axis 1 자동 활성화 알림 UX — verify

## 이번 라운드 범위

`submit_correction()` 자동 활성화 감지 + `auto_activated` 응답 페이로드.
`PreferencePanel.tsx` 알림 UI (`data-testid` 2개).
`App.tsx` 상태/핸들러 연결.
E2E 시나리오 파일 추가. docs 최소 동기화.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `py_compile app/handlers/feedback.py` | **PASS** |
| `tsc --noEmit --project app/frontend/tsconfig.json` | **PASS** |
| `git diff --check` (11개 파일) | **PASS** |
| Playwright E2E smoke | **미실행** — sandbox socket 제한 (PermissionError: [Errno 1]) |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `feedback.py` `auto_activated_preference_id` + 응답 페이로드 포함 | ✓ L183,230,234 |
| `PreferencePanel.tsx` `data-testid="preference-auto-activated-notice"` | ✓ L299 |
| `PreferencePanel.tsx` `data-testid="preference-auto-activated-link"` | ✓ L305 |
| `App.tsx` `autoActivatedPreferenceNotice` 상태 + 핸들러 연결 | ✓ L24,44,162 |
| `web-smoke.spec.mjs` auto activation E2E 시나리오 추가 | ✓ L12701 |

## Dirty Tree (브랜치: fix/advisory-recovery-pane-busy-age, HEAD 939dcf8)

| 파일 | 상태 |
|------|------|
| `app/handlers/feedback.py` | M (uncommitted) |
| `app/frontend/src/App.tsx` | M (uncommitted) |
| `app/frontend/src/api/client.ts` | M (uncommitted) |
| `app/frontend/src/components/PreferencePanel.tsx` | M (uncommitted) |
| `app/frontend/src/components/Sidebar.tsx` | M (uncommitted) |
| `e2e/tests/web-smoke.spec.mjs` | M (uncommitted) |
| `README.md` | M (uncommitted) |
| `docs/PRODUCT_SPEC.md` | M (uncommitted) |
| `docs/ACCEPTANCE_CRITERIA.md` | M (uncommitted) |
| `docs/MILESTONES.md` | M (uncommitted) |
| `docs/TASK_BACKLOG.md` | M (uncommitted) |

## 남은 리스크

- Playwright E2E 미실행: sandbox socket 제한. CI 환경에서 실행 필요.
- `app/static/dist/` 미재빌드: Axis 2 처리.
- 브랜치 기반 불일치: 로컬에 `main`이 없어 handoff의 "fresh branch from main" 미확인. commit/push는 verify/handoff 레인에서 처리.
