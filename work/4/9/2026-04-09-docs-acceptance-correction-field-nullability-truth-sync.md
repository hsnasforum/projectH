# docs: ACCEPTANCE_CRITERIA correction field nullability truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — Response Payload Contract 섹션(line 120)에서 5개 보정 필드에 `(nullable)` 주석 및 `all null when absent` 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `docs/PRODUCT_SPEC.md:317-322`와 `docs/ARCHITECTURE.md:161-165`는 이미 보정 필드의 null 시맨틱을 정확하게 기술
- `docs/ACCEPTANCE_CRITERIA.md`만 generic 표기로 nullability 미명시
- 3개 문서 간 정합 필요

## 핵심 변경
- `original_response_snapshot`, `corrected_outcome`, `approval_reason_record`, `content_reason_record`, `save_content_source` 모두에 `(nullable)` 추가
- `all null when absent; carry pre-correction state and reason records when present` 명시

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 보정 필드 nullability 진실 동기화가 3개 문서 모두에서 완료. 응답 페이로드 계약 전체 family 진실 동기화 완료.
