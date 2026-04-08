# browser folder picker mixed scanned-PDF partial-failure successful-result retention assertion tightening

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (mixed-folder scenario에 assertion 3줄 추가)

## 사용 skill

- 없음

## 변경 이유

- 기존 mixed-folder scenario는 partial-failure notice만 검증하고, readable file 결과가 실제로 preview에 남아 있는지는 검증하지 않았음
- shipped contract (README:67, ACCEPTANCE:35)는 unreadable file이 섞여 있어도 "successfully read files의 결과는 계속 반환된다"를 약속
- `notes.txt`가 search preview item으로 남아있고 `budget` snippet이 표시되는지 직접 확인하여 successful-result retention을 보장

## 핵심 변경

- `search-preview-item` count 1개 확인
- `search-preview-name`에 `notes.txt` 포함 확인
- `search-preview-snippet`에 `budget` 포함 확인

## 검증

- `npx playwright test -g "count-only partial-failure notice"` → 1 passed (7.5s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean

## 남은 리스크

- 없음. same scenario tightening만, docs/runtime 무변경.
