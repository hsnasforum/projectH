# Docs task-log corrected_outcome_recorded multi-path field-shape truth sync

## 변경 파일

- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

이전 슬라이스에서 `corrected_outcome_recorded`의 core 필드를 `{message_id, artifact_id, artifact_kind, source_message_id, outcome}`으로 기술했으나, 실제 코드는 `{outcome, recorded_at, artifact_id, source_message_id}`이며 `message_id`/`artifact_kind`는 포함하지 않음. feedback handler와 save/write path 두 곳에서 emit되는 multi-path action.

## 핵심 변경

### docs/ARCHITECTURE.md
- `corrected_outcome_recorded` detail: `{message_id, artifact_id, artifact_kind, source_message_id, outcome}` → `{outcome, recorded_at, artifact_id, source_message_id}` 수정
- multi-path emitter 명시 (feedback handler + save/write paths)

## 검증

- `corrected_outcome_recorded` shape이 `app/handlers/feedback.py:86-98,190-201`과 `core/agent_loop.py:249-260`에 일치
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- candidate confirmation/review action detail shape은 별도 범위.
