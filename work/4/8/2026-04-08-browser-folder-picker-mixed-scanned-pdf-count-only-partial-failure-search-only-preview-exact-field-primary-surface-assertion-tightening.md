# browser folder picker mixed scanned-PDF count-only partial-failure search-only preview exact-field primary-surface assertion tightening

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (mixed-folder search-only scenario에 exact-field + transcript + hidden-body assertions 강화)

## 사용 skill

- 없음

## 변경 이유

- 기존 search-only mixed-folder scenario는 visibility/count/containment만 확인하고, ordered label, title attribute, match badge, transcript preview, hidden-body contract는 검증하지 않았음
- generic search-only scenario (line 274-315)는 이미 이러한 exact-field assertions를 직접 고정하는 패턴 사용
- same scenario에 동일한 contract를 적용하여 preview primary-surface를 완전히 고정

## 핵심 변경

- response-detail preview: ordered label `"1. notes.txt"`, title `"mixed-search-folder/notes.txt"`, match badge `"내용 일치"`, snippet visible + `budget`
- search-only hidden-body contract: `response-text` hidden, `response-copy-text` hidden
- transcript preview: 동일한 exact-field assertions (panel visible, count, label, title, match, snippet)

## 검증

- `npx playwright test -g "count-only partial-failure notice"` → 1 passed (8.0s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean

## 남은 리스크

- 없음. same scenario tightening만, docs/runtime 무변경.
