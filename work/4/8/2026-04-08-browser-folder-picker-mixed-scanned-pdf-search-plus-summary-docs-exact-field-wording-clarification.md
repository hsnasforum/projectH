# browser folder picker mixed scanned-PDF search-plus-summary docs exact-field wording clarification

## 변경 파일

- `README.md` (line 191)
- `docs/MILESTONES.md` (line 103)
- `docs/TASK_BACKLOG.md` (line 98)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1400)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 4곳 모두 `notes.txt preview + budget snippet 유지` 수준으로만 적고 있었으나, actual smoke는 이미 ordered label, full-path tooltip, match badge, transcript preview exact fields까지 직접 고정
- docs wording을 actual smoke coverage 범위에 맞게 truthful하게 정렬

## 핵심 변경

- 4곳 모두: `notes.txt preview + budget snippet 유지` → preview exact fields(`1. notes.txt`, `mixed-search-folder/notes.txt` tooltip, `내용 일치`, `budget` snippet) + transcript preview exact fields

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
