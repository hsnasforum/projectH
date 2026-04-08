# Docs task-log feedback-correction-verdict detail field-shape truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

feedback/correction/verdict 관련 5개 action의 detail field shape이 authoritative docs에서 기술되지 않았음. `app/handlers/feedback.py`에서 이미 고정된 detail 객체를 로깅.

## 핵심 변경

### docs/ARCHITECTURE.md
5개 action per-action detail shape 추가:
- `response_feedback_recorded`: `{message_id, artifact_id, artifact_kind, feedback_label, feedback_reason}`
- `correction_submitted`: `{message_id, artifact_id, artifact_kind, source_message_id, corrected_text_length}`
- `corrected_outcome_recorded`: `{message_id, artifact_id, artifact_kind, source_message_id, outcome}` + optional extras
- `content_verdict_recorded`: `{message_id, artifact_id, artifact_kind, source_message_id, content_verdict, content_reason_record}`
- `content_reason_note_recorded`: `{message_id, artifact_id, artifact_kind, source_message_id, reason_scope, reason_label, reason_note, content_reason_record}`

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- feedback/correction/verdict action family core 필드 참조 및 ARCHITECTURE 참조 추가

## 검증

- 3개 문서 모두 feedback/correction/verdict detail 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- candidate confirmation/review action detail shape은 별도 범위.
