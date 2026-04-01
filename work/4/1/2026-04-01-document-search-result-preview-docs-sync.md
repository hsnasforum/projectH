# 2026-04-01 document search result preview docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드(`work/4/1/2026-04-01-document-search-result-preview.md`)에서 검색 결과 미리보기 카드 UI를 구현했으나, root docs에는 해당 변경이 반영되지 않아 shipped contract 설명이 어긋남.
- `verify/4/1/2026-04-01-document-search-result-preview-verification.md`에서 docs truth sync가 남은 가장 작은 current-risk reduction으로 지적됨.
- 이번 라운드는 docs-only sync이며, 코드/테스트/브라우저 시나리오는 수정하지 않음.

## 핵심 변경
- `README.md` Current Product Slice: 검색 응답에 structured search result preview panel이 포함된다는 설명 추가
- `docs/PRODUCT_SPEC.md` Document Search mode: 검색 응답 미리보기 카드(파일명, 일치 방식 배지, snippet) 설명 추가
- `docs/ACCEPTANCE_CRITERIA.md` Implemented: 검색 결과 미리보기 패널 contract 설명 추가 (`search_results` 배열의 `path`, `matched_on`, `snippet` 구조 포함)
- milestone wording, roadmap 방향, ranking, 새 인터랙션 제안 등 scope widen 없음

## 검증
- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`: 통과
- 코드/테스트 파일은 이번 라운드에서 수정하지 않았으므로 Python 검증 및 browser smoke는 실행하지 않음

## 남은 리스크
- docs-only 변경이므로 기능적 리스크 없음
- dirty worktree가 여전히 넓음
- 이번 family(document search result preview)는 코드 구현 + docs sync까지 truthfully 닫힘
