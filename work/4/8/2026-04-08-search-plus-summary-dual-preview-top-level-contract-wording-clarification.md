# search-plus-summary dual-preview top-level contract wording clarification

## 변경 파일

- `README.md` (line 47)
- `docs/ACCEPTANCE_CRITERIA.md` (line 36)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- top-level search contract는 search-plus-summary에서 visible summary body와 함께 response detail/transcript 양쪽에 preview cards가 유지된다는 truth를 반영하지 않았음
- smoke coverage와 scenario-level docs는 이미 response-detail + transcript dual-preview truth를 직접 고정
- top-level contract를 same truth에 맞게 정렬

## 핵심 변경

- README:47: search-plus-summary → `visible summary body alongside preview cards in both the response detail and the transcript` 추가
- ACCEPTANCE:36: 동일한 search-plus-summary dual-preview truth 추가

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
