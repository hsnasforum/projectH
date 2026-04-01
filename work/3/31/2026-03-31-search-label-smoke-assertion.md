# 2026-03-31 folder-search `선택 결과 요약` label Playwright smoke assertion 추가

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — 기존 folder-search 시나리오에 quick-meta, transcript meta `선택 결과 요약` assertion 추가

## 사용 skill
- 없음

## 변경 이유
- `문서 요약` label은 직전 라운드에서 smoke로 고정했으나, `선택 결과 요약` label은 아직 browser smoke에서 직접 보호되지 않았음
- `.pipeline/codex_feedback.md` (`STATUS: implement`) 지시에 따라 기존 folder-search 시나리오를 재사용해 최소 비용으로 고정

## 핵심 변경

### `e2e/tests/web-smoke.spec.mjs`
- "브라우저 폴더 선택으로도 문서 검색이 됩니다" 시나리오에 두 줄 추가:
  - `await expect(page.locator("#response-quick-meta-text")).toContainText("선택 결과 요약");` — quick-meta bar에 search label 확인
  - `await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("선택 결과 요약");` — transcript message meta에 search label 확인

### 변경하지 않은 것
- `app/templates/index.html` 변경 없음 (기존 `data-testid="transcript-meta"` hook 재사용)
- backend field, prompt, summary behavior 변경 없음
- docs wording 변경 없음
- unrelated dirty file 정리 없음

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — `12 passed (2.7m)`

## 남은 리스크
- evidence-bearing non-document 케이스의 negative assertion (label이 없어야 한다는 검증)은 해당 조건을 만드는 fixture가 없어 현재 mock으로는 불가
- dirty worktree에 unrelated 변경이 넓게 섞여 있어, 커밋 시 선별 staging 필요
