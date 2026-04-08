# Docs ACCEPTANCE_CRITERIA session response metadata field-shape inventory truth sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md:92`가 response metadata를 한 줄 generic 문장으로 압축하고 있었으나, PRODUCT_SPEC과 ARCHITECTURE는 이미 각 필드의 shape을 상세 기술. Acceptance layer가 authoritative contract 수준에서 field-shape을 반영하지 않아 docs 간 상세 수준 불일치.

## 핵심 변경

### docs/ACCEPTANCE_CRITERIA.md
generic 한 줄 문장을 다음 per-message 필드 inventory로 교체:
- `response_origin` — shape 기술
- `evidence` — shape 기술
- `summary_chunks` — shape 기술
- `claim_coverage` — PRODUCT_SPEC 참조
- `claim_coverage_progress_summary`
- `web_search_history` — PRODUCT_SPEC 참조
- `feedback`, `corrected_text`, `corrected_outcome`, `content_reason_record`, `approval_reason_record`
- `original_response_snapshot` — nested shape 및 same-shape 참조

## 검증

- PRODUCT_SPEC, ARCHITECTURE와 일관된 field-shape inventory 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `claim_coverage`와 `web_search_history`는 PRODUCT_SPEC 참조로 처리 (inline 전체 shape 미반복).
