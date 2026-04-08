# document-search selected-copy + dual-preview PRODUCT_SPEC wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (line 135)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `PRODUCT_SPEC.md:135`는 structured preview/search-only hidden body까지만 적고 있어, README/ACCEPTANCE에 이미 반영된 search-only `selected-copy` button + notice truth와 search-plus-summary dual-preview truth가 빠져 있었음
- same document-search contract를 PRODUCT_SPEC에도 맞게 정렬

## 핵심 변경

- search-only: `선택 경로 복사` button + `선택 경로를 복사했습니다` notice truth 추가
- search-plus-summary: `visible summary body alongside preview cards in both the response detail and the transcript` truth 추가

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
