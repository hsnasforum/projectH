# 2026-03-31 document-summary source-type label Playwright smoke assertion 추가

## 변경 파일
- `app/templates/index.html` — transcript meta div에 `data-testid="transcript-meta"` hook 추가
- `e2e/tests/web-smoke.spec.mjs` — 기존 문서 요약 시나리오에 quick-meta, transcript meta `문서 요약` assertion 추가

## 사용 skill
- 없음

## 변경 이유
- source-type label contract (`문서 요약` / `선택 결과 요약`)가 browser smoke에서 직접 보호되지 않아, 향후 predicate drift가 다시 숨어들 수 있었음
- `.pipeline/codex_feedback.md` (`STATUS: implement`) 지시에 따라 이미 shipped된 contract를 최소 비용으로 smoke 고정

## 핵심 변경

### `app/templates/index.html`
- `renderTranscript` 내 metaLines div 생성 시 `meta.dataset.testid = "transcript-meta"` 추가
- 기존 동작 변경 없음, selector hook만 추가

### `e2e/tests/web-smoke.spec.mjs`
- "파일 요약 후 근거와 요약 구간이 보입니다" 시나리오에 두 줄 추가:
  - `await expect(page.locator("#response-quick-meta-text")).toContainText("문서 요약");` — quick-meta bar에 label 확인
  - `await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("문서 요약");` — transcript message meta에 label 확인

### 변경하지 않은 것
- backend field, prompt, summary behavior 변경 없음
- search mode assertion 없음 (mock adapter 한계)
- docs wording 변경 없음 (copy/contract 변경 없으므로)
- unrelated dirty file 정리 없음

## 검증
- `git diff --check -- app/templates/index.html e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — `12 passed (2.7m)`

## 남은 리스크
- `선택 결과 요약` (search mode) label은 mock adapter 환경에서 직접 테스트 불가
- evidence-bearing non-document 케이스의 negative assertion은 아직 없음 (해당 조건을 만드는 fixture가 없어 현재 mock으로는 불가)
- dirty worktree에 unrelated 변경이 넓게 섞여 있어, 커밋 시 선별 staging 필요
