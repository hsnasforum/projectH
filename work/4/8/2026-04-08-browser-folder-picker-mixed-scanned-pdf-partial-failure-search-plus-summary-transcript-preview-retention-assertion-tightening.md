# browser folder picker mixed scanned-PDF partial-failure search-plus-summary transcript preview retention assertion tightening

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (mixed-folder search-plus-summary scenario에 transcript preview assertion 4줄 추가)

## 사용 skill

- 없음

## 변경 이유

- 기존 mixed-folder search-plus-summary scenario는 response-detail preview만 검증하고, transcript preview retention은 검증하지 않았음
- generic search-plus-summary coverage (line 243-256)는 transcript preview panel까지 직접 고정하는 패턴이 이미 있음
- same scenario에 동일한 transcript preview assertions를 추가하여 partial-failure에도 transcript preview가 유지됨을 보장

## 핵심 변경

- transcript 마지막 assistant message의 `.search-preview-panel` visible 확인
- `.search-preview-item` count 1개 확인
- `.search-preview-name`에 `notes.txt` 포함 확인
- `.search-preview-snippet`에 `budget` 포함 확인

## 검증

- `npx playwright test -g "검색.요약하면 partial-failure"` → 1 passed (8.0s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean

## 남은 리스크

- 없음. same scenario tightening만, docs/runtime 무변경.
