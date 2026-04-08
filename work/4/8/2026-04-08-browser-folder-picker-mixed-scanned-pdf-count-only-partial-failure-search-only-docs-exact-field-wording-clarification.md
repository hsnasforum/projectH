# browser folder picker mixed scanned-PDF count-only partial-failure search-only docs exact-field wording clarification

## 변경 파일

- `README.md` (line 189)
- `docs/MILESTONES.md` (line 101)
- `docs/TASK_BACKLOG.md` (line 96)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1398)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 4곳 모두 `count-only partial-failure notice` 표시만 적고 있었으나, actual smoke는 이미 preview exact fields, selected path/copy, transcript preview, transcript body hidden까지 직접 고정
- docs wording을 actual smoke coverage 범위에 맞게 truthful하게 정렬

## 핵심 변경

- 4곳 모두: `count-only partial-failure notice` only → notice + preview exact fields + selected path/copy + hidden body + transcript preview + transcript body hidden

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
