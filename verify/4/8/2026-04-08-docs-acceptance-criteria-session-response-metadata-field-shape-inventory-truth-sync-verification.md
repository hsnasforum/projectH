## 변경 파일
- `verify/4/8/2026-04-08-docs-acceptance-criteria-session-response-metadata-field-shape-inventory-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- 최신 `/work`의 `docs/ACCEPTANCE_CRITERIA.md` inventory 확장이 실제 authoritative docs와 serializer 계약에 맞는지 재확인하고, 같은 acceptance-layer session summary block에서 남은 가장 작은 drift를 다음 Claude 슬라이스로 고정하기 위해 검증했습니다.

## 핵심 변경
- 최신 `/work`의 실제 수정은 맞았습니다.
- [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L92)~[docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L101)는 실제로 `response_origin`, `evidence`, `summary_chunks`, `claim_coverage`, `claim_coverage_progress_summary`, `web_search_history`, `feedback`, `corrected_text`, `corrected_outcome`, `content_reason_record`, `approval_reason_record`, `original_response_snapshot` inventory를 추가했고, 이는 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L257), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L418), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L167), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L299), [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L258), [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L268)와 충돌하지 않았습니다.
- 다만 `/work`의 `남은 리스크`는 축소돼 있었습니다. acceptance-layer top summary inventory에는 아직 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L275), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L185) 기준 shipped response/save-trace fields인 `selected_source_paths`, `saved_note_path`, `note_preview`, `save_content_source`, `source_message_id`가 빠져 있습니다.
- 이 omission은 실제 serializer와도 맞물립니다. [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L38)~[app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L61)는 response payload에 `source_message_id`, `saved_note_path`, `selected_source_paths`, `note_preview`, `save_content_source`를 이미 직렬화합니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ACCEPTANCE_CRITERIA session response save-trace field inventory truth sync`로 고정했습니다.

## 검증
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '90,112p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '250,279p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '166,190p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '476,486p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '298,304p'`
- `nl -ba app/serializers.py | sed -n '247,295p'`
- `rg -n 'session_local_memory_signal|superseded_reject_signal|historical_save_identity_signal|session_local_candidate|candidate_confirmation_record|candidate_recurrence_key|durable_candidate|candidate_review_record|selected_source_paths|saved_note_path|note_preview|save_content_source|source_message_id|approval_reason_record|web_search_history|response_origin|original_response_snapshot' docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n 'session_local_memory_signal|superseded_reject_signal|historical_save_identity_signal|session_local_candidate|candidate_confirmation_record|candidate_recurrence_key|durable_candidate|candidate_review_record|selected_source_paths|saved_note_path|note_preview|save_content_source|source_message_id' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md -S`
- `sed -n '1,120p' docs/NEXT_STEPS.md`
- `sed -n '1,120p' docs/MILESTONES.md`
- `sed -n '1,120p' docs/TASK_BACKLOG.md`
- `rg -n 'selected_source_paths|saved_note_path|note_preview|save_content_source|source_message_id' app/serializers.py tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n 'selected_source_paths|saved_note_path|note_preview|save_content_source|source_message_id' docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md README.md -S`
- `nl -ba app/serializers.py | sed -n '30,65p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '272,280p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '183,190p'`
- `git diff --check`
- `git status --short`

## 남은 리스크
- [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L92)~[docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L101)의 acceptance-layer top summary inventory에는 아직 `selected_source_paths`, `saved_note_path`, `note_preview`, `save_content_source`, `source_message_id`가 빠져 있어 same-family session response/save-trace parity drift가 남아 있습니다.
- 작업트리에 unrelated dirty files가 이미 존재하므로, 다음 슬라이스에서도 해당 파일들은 건드리지 않는 전제가 필요합니다.
