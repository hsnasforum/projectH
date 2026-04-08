# browser folder picker mixed scanned-PDF partial-failure search-plus-summary preview exact-field assertion tightening

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (mixed-folder search-plus-summary scenario에 exact-field assertion 강화)

## 사용 skill

- 없음

## 변경 이유

- 기존 assertions는 `toContainText("notes.txt")`/`toContainText("budget")`만 확인하고, ordered label exact text, title attribute, match badge는 검증하지 않았음
- generic search-plus-summary assertions (line 245-256)는 이미 `toHaveText`, `toHaveAttribute("title")`, match badge까지 직접 고정하는 패턴 사용
- same scenario에 동일한 exact-field assertions를 적용하여 preview card contract를 완전히 고정

## 핵심 변경

- response-detail preview: ordered label `"1. notes.txt"`, title `"mixed-search-folder/notes.txt"`, match badge `"내용 일치"`, snippet visible + `budget` 포함
- transcript preview: 동일한 exact-field assertions

## 검증

- `npx playwright test -g "검색.요약하면 partial-failure"` → 1 passed (7.5s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean

## 남은 리스크

- 없음. same scenario tightening만, docs/runtime 무변경.
