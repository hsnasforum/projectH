STATUS: verified
CONTROL_SEQ: 1211
BASED_ON_WORK: work/4/28/2026-04-28-m61-axis2-correction-summary-e2e-smoke.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1211
VERIFIED_BY: Claude
NEXT_CONTROL: advisory_request.md CONTROL_SEQ 1212

---

# 2026-04-28 M61 Axis 2 — /api/corrections/summary E2E smoke 검증

## 이번 라운드 범위

E2E 격리 시나리오 — `e2e/tests/web-smoke.spec.mjs` (1개 시나리오 추가).
backend / frontend / dist 변경 없음.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `git diff --check -- e2e/tests/web-smoke.spec.mjs` | **PASS** (exit 0) |
| Playwright 격리 실행 (구현자 보고) | **1 passed (12.4s)** |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `e2e/tests/web-smoke.spec.mjs:12009` 신규 시나리오 | ✓ |
| `page.route(/\/api\/corrections\/summary$/, ...)` mock (GET method 확인 포함) | ✓ |
| `page.goto("/app-preview")` → `page.evaluate()` → `fetch("/api/corrections/summary")` | ✓ |
| 어서션 4개: `result.ok`, `data.ok`, `data.total`, `data.by_status`, `data.top_recurring_fingerprints` | ✓ |
| 기존 E2E 시나리오 미수정 (다음 시나리오 `reviewed-memory loop` 확인) | ✓ |
| commit / push / PR 미실행 | ✓ |

## M61 완성 상태

| Axis | 내용 | 상태 |
|------|------|------|
| 1 | GET /api/corrections/summary backend + 단위 테스트 | ✓ |
| 2 | E2E 격리 시나리오 (응답 shape 계약 고정) | ✓ 이번 라운드 |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `e2e/tests/web-smoke.spec.mjs` | 수정됨, 미커밋 | M61 Axis 2 |
| `docs/MILESTONES.md` | 수정됨, 미커밋 | M61 Axis 2 (verify inline) |

현재 브랜치: `feat/m50-axis1-axis2-pref-visibility` (PR #52 OPEN)
HEAD: `b2a51e9` (M61 Axis 1)

## 다음 행동

M61 전체 완료. 2개 파일 커밋+푸시 → PR #52 scope 확장 (M61 Axis 1+2).
M62 방향 advisory.
→ `advisory_request.md` CONTROL_SEQ 1212.
