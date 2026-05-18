STATUS: verified
CONTROL_SEQ: 1547
BASED_ON_WORK: work/5/8/2026-05-08-m119-axis2-injection-correction-badge.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1547

---

# 2026-05-08 M119 Axis 2 injection correction badge — verify

## 이번 라운드 범위

CONTROL_SEQ 1546 implement_handoff (m119_axis2_injection_correction_badge) 실행 결과.
work note 변경 범위: `app/frontend/src/api/client.ts`, `app/frontend/src/components/PreferencePanel.tsx`, `app/static/dist/assets/index.js`, `e2e/tests/web-smoke.spec.mjs` 4개 파일.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `cd app/frontend && npx tsc --noEmit` | **PASS** |
| `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "preference injected count badge" --reporter=line` | **PASS — 1개** (8.7s) |
| `git diff --check` (M119 Axis 2 4개 파일) | **PASS** |
| `python3 -m py_compile pipeline_runtime/lane_surface.py` | **PASS** (orphaned) |
| `python3 -m unittest tests.test_watcher_core.PanePromptDetectionTest.test_claude_code_prompt_with_nbsp_counts_as_ready` | **PASS — 1개** (orphaned) |
| `git diff --check` (orphaned 2개 파일) | **PASS** |

## 핵심 변경 확인

- `app/frontend/src/api/client.ts` line 233–234: `injection_correction_count?: number | null`, `injection_correction_rate?: number | null` 추가 — 확인
- `PreferencePanel.tsx` `preferenceInjectedLabel()` (line 81–85): `correctionRate > 0`이면 `N회 주입 (A% 적용 · R% 교정)` 반환 — 확인
- `e2e/tests/web-smoke.spec.mjs` line 15176–15177, 15249: 픽스처에 `injection_correction_rate: 0.25` 추가, 기대 텍스트 `4회 주입 (50% 적용 · 25% 교정)` — 확인
- `app/static/dist/assets/index.js`: sha256 `64333ac0e4b29d68f315f4bf2258cd69f18df45a9b07c59d702e87430251cf96` (work note와 일치)

## dirty tree 현황 (6개 파일) — 미커밋, 브랜치 `feat/m120-injection-correction-reliability-filter`

| 분류 | 파일 | 출처 |
|------|------|------|
| M119 Axis 2 | `app/frontend/src/api/client.ts` | TypeScript 타입 추가 |
| M119 Axis 2 | `app/frontend/src/components/PreferencePanel.tsx` | 배지 로직 수정 |
| M119 Axis 2 | `app/static/dist/assets/index.js` | dist 재빌드 산출물 |
| M119 Axis 2 | `e2e/tests/web-smoke.spec.mjs` | smoke 픽스처·기대값 갱신 |
| **orphaned** | `pipeline_runtime/lane_surface.py` | `\xa0` NBSP → 공백 변환 후 strip — work note 미커버 |
| **orphaned** | `tests/test_watcher_core.py` | NBSP 입력 프롬프트 감지 회귀 테스트 — work note 미커버 |

## orphaned 변경 내용 요약

`pipeline_runtime/lane_surface.py`:
`line_looks_like_input_prompt()` 내 `stripped = line.strip()` → `stripped = line.replace("\xa0", " ").strip()`.
M119 Axis 2 구현 시작 명령 입력 시 프롬프트 문자열에 `\xa0`(NBSP)가 포함돼 watcher가 준비 상태를 인식하지 못한 인시던트에서 유발된 fix.

`tests/test_watcher_core.py`:
`test_claude_code_prompt_with_nbsp_counts_as_ready` — NBSP가 포함된 Claude Code 입력 프롬프트를 ready 상태로 올바르게 인식하는지 검증.

기능상 M119 Axis 2와 독립적이며 py_compile + unittest PASS.

## 주의: dist 빌드 경로 EROFS

`npm run build` 기본 경로 직접 빌드가 실행 환경 `EROFS`로 실패. `/tmp` 우회 빌드 후 `index.js`만 수동 복사. sha256 일치 확인됨. `index.css` / `index.html` 해시 동일로 변경 없음. EROFS 원인 자체는 이번 범위 밖.

## 검증 미실행 항목

- 전체 E2E 미실행 — 지정 단일 시나리오만 실행; CI 위임
- `npm run build` 기본 경로 미성공 (EROFS) — /tmp 빌드로 대체
- commit, push, PR 생성 미수행

## 남은 리스크

- 6개 파일 미커밋 — 신규 브랜치 + PR 필요 (base: `feat/m120-injection-correction-reliability-filter`)
- orphaned NBSP fix 처리 (M119 Axis 2 합산 or 별도 커밋)
- MILESTONES / TASK_BACKLOG M119 Axis 2 완료 미기록 — doc-sync 필요
- EROFS 빌드 환경 문제 미해소
