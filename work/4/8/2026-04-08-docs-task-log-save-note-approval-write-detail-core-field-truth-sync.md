# Docs save-note approval/write task-log detail core-field truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

save-note 관련 task-log action 5개(`approval_requested`, `approval_granted`, `approval_rejected`, `approval_reissued`, `write_note`)의 detail field shape이 authoritative docs에서 기술되지 않았음. `core/agent_loop.py:6990-7313`에서 이미 고정된 core 필드를 포함하는 detail 객체를 로깅하고 있었으나 docs에서는 generic 문구만 사용.

## 핵심 변경

### docs/ARCHITECTURE.md
- 5개 save-note action 각각에 per-action detail field shape 추가:
  - `approval_requested`: `{approval_id, artifact_id, source_message_id, note_path, overwrite, save_content_source}` + optional extras
  - `approval_granted`: `{approval_id, kind, requested_path, overwrite, artifact_id, source_message_id, save_content_source}`
  - `approval_rejected`: `{approval_id, kind, requested_path, artifact_id, source_message_id, save_content_source, approval_reason_record}`
  - `approval_reissued`: `{old_approval_id, new_approval_id, old_requested_path, new_requested_path, overwrite, source_paths, artifact_id, source_message_id, save_content_source, approval_reason_record}`
  - `write_note`: `{artifact_id, source_message_id, note_path, save_content_source}` + optional extras

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- task-log 요약에 save-note action core 필드 참조 및 ARCHITECTURE 참조 추가

## 검증

- 3개 문서 모두 save-note action detail 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- system-level preference action 및 내부 처리 action은 여전히 문서화 범위 밖.
