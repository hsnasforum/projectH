# 2026-03-31 source-type label smoke coverage 문서 동기화

## 변경 파일
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- 직전 두 라운드에서 `문서 요약` (scenario 1)과 `선택 결과 요약` (folder-search) source-type label assertion을 Playwright smoke에 추가했으나, smoke coverage 문서가 이 truth를 반영하지 않아 verify에서 `not ready` 판정을 받았음
- `.pipeline/codex_feedback.md` (`STATUS: implement`) 지시에 따라 docs-only sync 수행

## 핵심 변경

### `README.md` — Playwright Smoke Coverage 섹션
- scenario 1 설명에 `문서 요약` source-type label in both quick-meta and transcript meta 추가
- scenario 3 (folder picker) 설명에 `선택 결과 요약` source-type label in both quick-meta and transcript meta 추가

### `docs/ACCEPTANCE_CRITERIA.md` — Playwright smoke list
- file summary 항목에 `문서 요약` source-type label assertion in both quick-meta and transcript meta 추가
- browser folder picker 항목에 `선택 결과 요약` source-type label assertion in both quick-meta and transcript meta 추가

### `docs/MILESTONES.md` — Milestone 3 smoke suite 설명
- scenario 1 괄호 안에 `문서 요약` label coverage 추가
- folder-search scenario에 `선택 결과 요약` label coverage 추가

### `docs/TASK_BACKLOG.md` — 항목 12 smoke coverage 설명
- scenario 1 괄호 안에 `문서 요약` label coverage 추가
- folder-search scenario에 `선택 결과 요약` label coverage 추가

### 변경하지 않은 것
- `e2e/tests/web-smoke.spec.mjs` 변경 없음
- `app/templates/index.html` 변경 없음
- backend, prompt, summary behavior 변경 없음
- unrelated dirty file 정리 없음

## 검증
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과

## 남은 리스크
- docs-only 변경이므로 기능 리스크 없음
- dirty worktree에 unrelated 변경이 넓게 섞여 있어, 커밋 시 선별 staging 필요
