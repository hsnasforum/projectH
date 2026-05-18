STATUS: verified
CONTROL_SEQ: 1239
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1238
BASED_ON_WORK: work/4/28/2026-04-28-m68-axis1-promote-pattern-ui.md
VERIFIED_BY: Claude (verify owner — Playwright run taken over from implement_blocked sentinel)
BLOCK_RECOVERED: BLOCK_ID df0688609f9c4c08f3931453f53a3ec7896a65aae9bbefc181427b229ed3f25f / playwright_socket_denied
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1239

---

# 2026-04-28 M68 Axis 2 — promote-pattern dist 재빌드 + E2E 검증

## 이번 라운드 범위

`app/static/dist/` 재빌드 + `e2e/tests/web-smoke.spec.mjs` 격리 시나리오 추가 + `docs/MILESTONES.md`.
backend / `app/frontend/src/` 변경 없음.

## 블록 복구

implement_blocked BLOCK_ID `df066860...`: `playwright_socket_denied` / M64/M66/M67과 동일한 반복 패턴.
코드 변경(dist 재빌드, 시나리오 추가, MILESTONES) 완료 상태. Playwright 실행만 환경 제약.
verify 소유자가 직접 격리 실행 → PASS.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `git diff --check -- web-smoke.spec.mjs MILESTONES.md` | **PASS** (exit 0) |
| Playwright 격리 (`correction promote pattern button calls promote-pattern endpoint`) | **1 passed (9.2s)** (verify owner 실행) |

## 구현 클레임 확인

| 클레임 | 위치 | 확인 결과 |
|--------|------|---------|
| E2E 격리 시나리오 | `web-smoke.spec.mjs:12377` | ✓ |
| `app/static/dist/assets/index.js` 재빌드 | 318,976 bytes (Apr 28 18:21) | ✓ |
| M68 Axis 2 MILESTONES.md 항목 | `MILESTONES.md:1279` | ✓ |
| backend / `app/frontend/src/` 미수정 (Axis 2 경계 준수) | — | ✓ |
| commit / push 미실행 | git log HEAD: 8ab591f | ✓ |

## Dirty Tree 상태 (M68 전체)

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `storage/correction_store.py` | 미커밋 | M68 Axis 1 |
| `storage/sqlite_store.py` | 미커밋 | M68 Axis 1 |
| `app/handlers/aggregate.py` | 미커밋 | M68 Axis 1 |
| `app/web.py` | 미커밋 | M68 Axis 1 |
| `app/frontend/src/api/client.ts` | 미커밋 | M68 Axis 1 |
| `app/frontend/src/components/PreferencePanel.tsx` | 미커밋 | M68 Axis 1 |
| `tests/test_correction_store.py` | 미커밋 | M68 Axis 1 |
| `tests/test_sqlite_store.py` | 미커밋 | M68 Axis 1 |
| `app/static/dist/assets/index.js` | 미커밋 | M68 Axis 2 |
| `e2e/tests/web-smoke.spec.mjs` | 미커밋 | M68 Axis 2 |
| `docs/MILESTONES.md` | 미커밋 | M68 Axis 2 |

현재 브랜치: `feat/m50-axis1-axis2-pref-visibility` (PR #53 merged, HEAD: 8ab591f)
HEAD 8ab591f = watcher fix (local-only, main에 미반영)

## M68 완성 상태

| Axis | 내용 | 상태 |
|------|------|------|
| 1 | backend + frontend code (promote-pattern) | ✓ (verified CONTROL_SEQ 1238) |
| 2 | dist 재빌드 + E2E 격리 | ✓ 이번 라운드 (verify 소유자 Playwright 실행) |

## playwright_socket_denied 패턴 관찰

M64/M66/M67/M68 Axis 2 모두 동일 블록. future Axis 2 핸드오프에서도 동일 흡수 경로 유효.

## 다음 행동

M68 전체 완료. 11개 파일 + HEAD(8ab591f) watcher fix → 새 브랜치 커밋 + 푸시 + PR 생성.
→ `operator_request.md` CONTROL_SEQ 1239.
