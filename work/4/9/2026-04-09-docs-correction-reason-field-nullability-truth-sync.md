# docs: response payload correction reason field nullability truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — `### Correction And Reason Fields` 섹션(line 317-322)에서 5개 필드 모두에 `null` 시맨틱 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `app/serializers.py:57-61`에서 `original_response_snapshot`, `corrected_outcome`, `approval_reason_record`, `content_reason_record`, `save_content_source` 모두 부재 시 `null`로 직렬화
- `docs/ARCHITECTURE.md:161-165`는 이미 `object | null` / `string | null`로 정확하게 기술
- `docs/PRODUCT_SPEC.md`만 object/value-only로 기술하여 진실 불일치 존재

## 핵심 변경
- 섹션 제목에 `(all null when absent)` 추가
- 5개 필드 각각에 `, or null` 명시
- `original_response_snapshot`은 최상위 `null`과 중첩 `response_origin` `null` 모두 표기

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 6줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 보정/사유 필드 nullability 진실 동기화 완료
