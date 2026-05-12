STATUS: verified
CONTROL_SEQ: 1553
BASED_ON_WORK: work/5/8/2026-05-08-m120-axis2-injection-demotion-badge.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1553

---

# 2026-05-08 M120 Axis 2 injection demotion badge — verify

## 이번 라운드 범위

CONTROL_SEQ 1552 implement_handoff (m120_axis2_injection_demotion_badge) 실행 결과.
work note 변경 범위: `app/frontend/src/components/PreferencePanel.tsx`, `app/static/dist/assets/index.js`, `e2e/tests/web-smoke.spec.mjs` 3개 파일.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `cd app/frontend && npx tsc --noEmit` | **PASS** |
| `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "preference injected count badge" --reporter=line` | **PASS — 1개** (8.0s) |
| `git diff --check` (3개 파일) | **PASS** |
| `sha256sum app/static/dist/assets/index.js` | **PASS** — `bc2d7078155f67350153cc0e76389918e62eb82eb1a0783b0cabce45be0af60b` (work note 일치) |

## 핵심 변경 확인

| 항목 | 확인 |
|------|------|
| `INJECTION_CORRECTION_DEMOTION_RATE = 0.25` (line 58) | ✓ M120 Axis 1 백엔드 상수(`INJECTION_CORRECTION_THRESHOLD`) 일치 |
| `isDemotedByInjectionCorrection()` (line 95–106): `rate > 0.25 AND injected_count >= 3` | ✓ 백엔드 강등 기준 정확 미러 |
| 주입 배지 강등 시 amber 스타일 + `title="교정률 R% 초과 - 신뢰도 자동 강등됨"` (line ~1093–1098) | ✓ |
| E2E 픽스처: `injection_correction_rate: 0.4, injected_count: 4` (강등 조건 충족) | ✓ |
| E2E 기대값 3중 검증: text `4회 주입 (50% 적용 · 40% 교정)`, title `/신뢰도 자동 강등됨/`, class `/bg-amber-500\/20/` | ✓ |

**E2E 픽스처 변경 이유:** M119 Axis 2에서 사용한 `rate=0.25`는 `> 0.25` 조건을 충족하지 않아 강등이 발생하지 않음. `rate=0.4`로 변경해 amber 배지 + tooltip 경로를 직접 커버. M119 Axis 2 배지 텍스트 표시 동작(교정률을 배지에 포함)은 `40% 교정` 검증으로 함께 커버됨.

## dirty tree 현황 (3개 파일) — 미커밋, 브랜치 `feat/m119-axis2-injection-correction-badge`

| 파일 | 출처 |
|------|------|
| `app/frontend/src/components/PreferencePanel.tsx` | 강등 헬퍼 + 배지 amber/tooltip 로직 |
| `app/static/dist/assets/index.js` | dist 재빌드 (`/tmp` 우회, sha256 확인) |
| `e2e/tests/web-smoke.spec.mjs` | 픽스처 rate 0.4 + 3중 기대값 |

브랜치 현 커밋: `f4c7618` (docs sync), `a1e684a` (M119 Axis 2), `283b92e` (NBSP fix).

## 검증 미실행 항목

- 전체 E2E 미실행 — 지정 단일 시나리오만 실행; CI 위임
- `npm run build` 기본 경로 미성공 (EROFS 환경) — `/tmp` 우회 빌드로 대체
- commit, push, PR 생성 미수행

## 남은 리스크

- 3개 파일 미커밋 — 신규 브랜치 + PR 필요 (base: `feat/m119-axis2-injection-correction-badge`)
- MILESTONES / TASK_BACKLOG M120 Axis 2 완료 미기록 — doc-sync 필요
- PR #113, #114, #115 draft — pr_merge_gate operator 대기
- watcher self-restart supervisor-owned lease TTL 구조 리스크 미해소 (M121 후보 A carry-over)
