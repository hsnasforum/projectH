# docs: README PRODUCT_SPEC ACCEPTANCE_CRITERIA ARCHITECTURE applied-preferences response-meta badge truth sync

## 변경 파일
- `README.md` — 1곳(line 54): applied-preferences badge 항목 추가
- `docs/PRODUCT_SPEC.md` — 3곳(line 106, 314, 336): badge 항목 추가 및 필드 설명 확장
- `docs/ACCEPTANCE_CRITERIA.md` — 2곳(line 27, 122): badge 항목 추가 및 필드 설명 확장
- `docs/ARCHITECTURE.md` — 2곳(line 156, 1361): 필드 테이블 설명 확장 및 badge 항목 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `applied_preferences` 페이로드 필드는 이미 문서에 기술되어 있었으나, 실제 브라우저에서 렌더링되는 `선호 N건 반영` 배지에 대한 설명이 누락
- 실제 shipped truth: `MessageBubble.tsx:275-281`에서 `applied_preferences`가 비어있지 않을 때 violet 색 `선호 {n}건 반영` 배지를 tooltip과 함께 렌더링
- response origin badge와 동일한 assistant-message meta 영역에 표시됨

## 핵심 변경
- 기존 response origin badge 항목 옆에 applied-preferences badge 항목 추가
- 페이로드 필드 설명에 badge 렌더링 동작 추가
- durable preference memory나 cross-session preference learning 주장 없이 현재 MVP truthful 범위 유지
- 코드, 테스트, 런타임 변경 없음

## 검증
- `git diff --stat` — 4 files changed, 8 insertions(+), 3 deletions(-)
- `rg 'applied_preferences|선호 .*건 반영'` — 모든 대상 파일에서 badge 설명 확인
- `git diff --check` — 공백 오류 없음

## 남은 리스크
- 없음 — applied-preferences response-meta badge 문서화 완료
