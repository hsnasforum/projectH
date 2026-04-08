# Docs task-log agent_response detail field-shape truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`agent_response` task-log detail의 구체적 field shape이 authoritative docs에서 기술되지 않았음. `core/agent_loop.py:7389-7412`에서 이미 고정된 16개 필드를 포함하는 detail 객체를 로깅하고 있으며, approval audit mirror 섹션에서 이를 참조하고 있었으나 실제 shape은 미기술 상태였음.

## 핵심 변경

3개 문서에 `agent_response` detail field shape 추가:
`{status, actions, requires_approval, proposed_note_path, saved_note_path, selected_source_paths, has_note_preview, approval_id, artifact_id, artifact_kind, source_message_id, save_content_source, approval_reason_record, active_context_label, evidence_count, summary_chunk_count}`

## 검증

- 3개 문서 모두 동일 field shape 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- system-level preference action 및 내부 처리 action은 여전히 문서화 범위 밖.
