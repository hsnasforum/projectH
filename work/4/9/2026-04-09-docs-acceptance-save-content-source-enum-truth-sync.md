# docs: ACCEPTANCE_CRITERIA save_content_source enum truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — Response Payload Contract 섹션(line 120)에서 `save_content_source`를 `(nullable)` → `(original_draft | corrected_text | null)`로 변경

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `docs/PRODUCT_SPEC.md:322`와 `docs/ARCHITECTURE.md:165`는 이미 `original_draft | corrected_text | null`로 정확하게 기술
- `docs/ACCEPTANCE_CRITERIA.md`만 generic `(nullable)`로 표기하여 값 계약 미명시
- `core/approval.py:17-18`의 정규 열거형과 일치 필요

## 핵심 변경
- `save_content_source (nullable)` → `save_content_source (original_draft | corrected_text | null)`

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 보정 필드 family의 3개 문서 진실 동기화 완료
