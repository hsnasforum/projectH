# docs: ARCHITECTURE ACCEPTANCE_CRITERIA control content field truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 응답 페이로드 테이블(line 140, 145-146)에서 `actions_taken`, `follow_up_suggestions`, `search_results`에 `(default [])` 추가
- `docs/ACCEPTANCE_CRITERIA.md` — Response Payload Contract 섹션(line 116-118)에서 제어/아이덴티티/콘텐츠 필드에 nullable/default-empty 주석 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 슬라이스에서 PRODUCT_SPEC의 동일 필드는 이미 정확하게 기술
- ARCHITECTURE와 ACCEPTANCE_CRITERIA만 generic 표기로 nullability/기본-빈 계약 미명시
- 3개 문서 간 정합 필요

## 핵심 변경
- ARCHITECTURE: `actions_taken`, `follow_up_suggestions`, `search_results` 3개 리스트 필드에 `(default [])` 추가
- ACCEPTANCE_CRITERIA: 제어 필드에 `(default [])` / `(nullable)`, 아이덴티티 필드에 `(nullable)`, 콘텐츠 필드에 `(nullable)` / `(default [])` 주석 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 6줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 제어/콘텐츠 필드 진실 동기화가 3개 문서 모두에서 완료
