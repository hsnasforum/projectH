# 2026-03-31 일반 채팅 negative source-type label smoke assertion 추가  

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 일반 채팅 시나리오 추가 (scenario 13)
- `README.md` — Playwright Smoke Coverage 목록에 scenario 13 추가
- `docs/ACCEPTANCE_CRITERIA.md` — smoke scenario count 12→13, general chat negative label 항목 추가
- `docs/MILESTONES.md` — smoke suite 설명에 general chat negative label coverage 추가
- `docs/TASK_BACKLOG.md` — smoke coverage 설명에 general chat negative label coverage 추가

## 사용 skill
- 없음

## 변경 이유
- document summary와 folder-search path의 positive label contract는 이미 smoke로 고정되었으나, 일반 채팅처럼 label이 없어야 하는 path는 보호되지 않았음
- `.pipeline/codex_feedback.md` (`STATUS: implement`) 지시에 따라 negative contract를 최소 시나리오로 고정

## 핵심 변경

### `e2e/tests/web-smoke.spec.mjs`
- "일반 채팅 응답에는 source-type label이 붙지 않습니다" 시나리오 추가:
  - chat mode로 전환 (`input[name="request_mode"][value="chat"]`)
  - `#user-text`에 텍스트 입력 후 submit
  - quick-meta에 `문서 요약` / `선택 결과 요약`가 없는지 확인
  - transcript meta에 `문서 요약` / `선택 결과 요약`가 없는지 확인

### docs sync (4개 파일)
- `README.md`: scenario 13 추가
- `docs/ACCEPTANCE_CRITERIA.md`: scenario count 12→13, general chat negative label 항목 추가
- `docs/MILESTONES.md`: smoke suite 괄호 안에 general chat negative label coverage 추가
- `docs/TASK_BACKLOG.md`: smoke coverage 괄호 안에 general chat negative label coverage 추가

### 변경하지 않은 것
- `app/templates/index.html` 변경 없음
- backend, prompt, summary behavior 변경 없음
- unrelated dirty file 정리 없음

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 통과
- `make e2e-test` — `13 passed (3.1m)`

## 남은 리스크
- dirty worktree에 unrelated 변경이 넓게 섞여 있어, 커밋 시 선별 staging 필요
