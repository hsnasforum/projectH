# 2026-04-27 M47/M48 A2 E2E 커버리지 + dist rebuild

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (E2E 테스트 2개 추가)
- `app/static/dist/assets/index.css` (재빌드)
- `app/static/dist/assets/index.js` (재빌드)
- `work/4/27/2026-04-27-m47-m48-e2e-dist-rebuild.md`

## 변경 이유
- PR #42-#45 merge 완료(2026-04-27) 후 `app/static/dist`가 M44 A3/A4 + M47 + M48 A2 코드를 반영하지 않은 상태.
- M47 `신뢰도 높음 N개` 헤더와 M48 A2 `충돌 위험 N건` 헤더(`data-testid="high-severity-conflict-count"`)에 대한 E2E 커버리지 없었음.
- TASK_BACKLOG에 post-merge 작업으로 기록된 E2E 갭 해소.

## 수행 작업
1. `npx vite build` — `app/static/dist` 재빌드 성공 (index.js 310.78kB, index.css 32.52kB)
2. E2E 테스트 추가 (mock-route 패턴, 기존 패턴 일관):
   - `PreferencePanel 헤더에 충돌 위험 N건이 표시됩니다 (M48 A2 high_severity_conflict_count)` — `data-testid="high-severity-conflict-count"` 확인
   - `PreferencePanel 헤더에 신뢰도 높음 N개가 표시됩니다 (M47 highly_reliable_active_count)` — 텍스트 확인

## 검증
- M48 A2 E2E: 1 passed (12.9s)
- M47 E2E: 1 passed (8.7s)

## push / PR
- 브랜치: `feat/m47-m48-dist-rebuild`
- commit: `cfc09df`
- PR: https://github.com/hsnasforum/projectH/pull/46

## 남은 리스크
- PR #46 merge는 operator boundary.
- dist 재빌드는 로컬 전용 (`dist/` gitignore 하위이지만 기존 파일은 tracked 상태).
