# Docs corrected_outcome_recorded shared-core wording truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

PRODUCT_SPEC과 ACCEPTANCE_CRITERIA의 top-level task-log summary가 `corrected_outcome_recorded`를 다른 4개 action과 같은 `message_id`, `artifact_id`, `artifact_kind` core 필드 그룹에 포함시키고 있었으나, 실제로는 `outcome`, `recorded_at`, `artifact_id`, `source_message_id` core로 별도 shape 사용.

## 핵심 변경

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- feedback/correction/verdict 그룹에서 `corrected_outcome_recorded`를 분리하여 별도 multi-path shape 설명 추가
- 나머지 4개 action (`response_feedback_recorded`, `correction_submitted`, `content_verdict_recorded`, `content_reason_note_recorded`)의 shared-core 기술은 유지

## 검증

- 두 문서 모두 `corrected_outcome_recorded` 별도 shape 기술 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- candidate confirmation/review action detail shape은 별도 범위.
