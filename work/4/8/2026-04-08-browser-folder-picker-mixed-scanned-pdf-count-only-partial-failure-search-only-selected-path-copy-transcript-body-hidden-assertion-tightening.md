# browser folder picker mixed scanned-PDF count-only partial-failure search-only selected-path/copy + transcript-body-hidden assertion tightening

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (mixed-folder search-only scenario에 selected-path/copy + transcript-hidden assertions 추가)

## 사용 skill

- 없음

## 변경 이유

- 기존 scenario는 preview exact-fields와 hidden response body만 확인하고, selected path list, selected-copy button/clipboard, transcript body hidden은 검증하지 않았음
- generic search-only scenario (line 289-315)는 이미 이러한 assertions를 직접 고정
- same scenario에 동일한 contract를 적용하여 search-only primary-surface를 완전히 닫음

## 핵심 변경

- `#selected-text`에 `"mixed-search-folder/notes.txt"` 유지 확인
- `selected-copy` visible → click → notice `"선택 경로를 복사했습니다."` → clipboard `"mixed-search-folder/notes.txt"` 확인
- transcript body `pre` hidden (count 0) 확인

## 검증

- `npx playwright test -g "count-only partial-failure notice"` → 1 passed (9.1s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean

## 남은 리스크

- 없음. same scenario tightening만, docs/runtime 무변경.
