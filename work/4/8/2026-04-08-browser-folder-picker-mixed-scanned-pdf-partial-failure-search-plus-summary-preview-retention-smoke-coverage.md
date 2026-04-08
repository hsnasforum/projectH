# browser folder picker mixed scanned-PDF partial-failure search-plus-summary preview retention smoke coverage

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (search-plus-summary variant scenario 1개 추가)
- `README.md` (79번 smoke coverage bullet 추가)
- `docs/MILESTONES.md` (browser folder picker search-plus-summary smoke 추가)
- `docs/TASK_BACKLOG.md` (85번 task 추가)
- `docs/ACCEPTANCE_CRITERIA.md` (browser folder picker search-plus-summary acceptance 1줄 추가)

## 사용 skill

- 없음

## 변경 이유

- 기존 mixed-folder scenario는 search-only variant만 검증하고, search-plus-summary variant는 없었음
- shipped contract (README:47/67, ACCEPTANCE:35-36)는 search-plus-summary에서도 unreadable file이 섞여 있을 때 successful result retention과 preview panel 유지를 약속
- 기존 fixture와 selector를 재사용하여 search-plus-summary variant를 1개 scenario로 고정

## 핵심 변경

- search-plus-summary (search-only 미체크) variant: partial-failure notice + visible response-text + search preview에 `notes.txt`/`budget` snippet 유지 확인
- docs 4곳에 coverage bullet truth-sync

## 검증

- `npx playwright test -g "검색.요약하면 partial-failure"` → 1 passed (6.8s)
- `git diff --check` → clean

## 남은 리스크

- 없음. search-plus-summary variant 1개 추가만, runtime/OCR/parser 무변경.
