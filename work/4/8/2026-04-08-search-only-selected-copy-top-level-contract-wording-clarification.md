# search-only selected-copy top-level contract wording clarification

## 변경 파일

- `README.md` (line 47)
- `docs/ACCEPTANCE_CRITERIA.md` (line 36)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- top-level search-only contract는 preview cards와 hidden body까지만 적고 `selected-copy` visibility/click/notice/clipboard truth를 반영하지 않았음
- smoke coverage docs와 pure/mixed search-only smoke는 이미 `selected-copy` button visibility, click, `선택 경로를 복사했습니다` notice, clipboard behavior를 직접 고정
- top-level contract를 same truth에 맞게 정렬

## 핵심 변경

- README:47: search-only primary surface 설명에 `선택 경로 복사` button + `선택 경로를 복사했습니다` notice truth 추가
- ACCEPTANCE:36: 동일한 `선택 경로 복사` button + notice truth 추가

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
