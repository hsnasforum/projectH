# Docs ACCEPTANCE_CRITERIA session pending_approvals active_context field-shape summary truth sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md`의 session JSON 요약에서 `pending_approvals`와 `active_context`가 이름만 나열. `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`는 이미 field-shape을 기술하고 있어 authoritative docs 간 상세 수준 불일치.

## 핵심 변경

### docs/ACCEPTANCE_CRITERIA.md
- `pending_approvals`: serialized approval 객체 리스트, Approval 섹션 참조
- `active_context`: `{kind, label, source_paths, summary_hint, suggested_prompts, record_path, claim_coverage_progress_summary}` shape 추가

## 검증

- PRODUCT_SPEC, ARCHITECTURE와 동일 shape 기술 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 없음. session JSON summary의 주요 필드가 authoritative docs 3개에서 모두 field-shape 기술 완료.
