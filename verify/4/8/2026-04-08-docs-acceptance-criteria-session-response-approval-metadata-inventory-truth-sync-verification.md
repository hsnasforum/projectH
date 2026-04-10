## 변경 파일
- `verify/4/8/2026-04-08-docs-acceptance-criteria-session-response-approval-metadata-inventory-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- 최신 `/work`의 `docs/ACCEPTANCE_CRITERIA.md` approval metadata inventory 확장이 실제 authoritative docs와 serializer 계약에 맞는지 재확인하고, 같은 acceptance-layer session summary block에서 남은 가장 작은 drift를 다음 Claude 슬라이스로 고정하기 위해 검증했습니다.

## 핵심 변경
- 최신 `/work`의 실제 수정은 맞았습니다.
- [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L102)의 `approval` entry 추가는 실제 [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L50), [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L300), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L189), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L281), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L191), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L210)과 맞았습니다.
- 다만 `/work`의 `response metadata inventory가 PRODUCT_SPEC/ARCHITECTURE와 대략적 parity 달성` 결론은 여전히 약간 과했습니다. 같은 top summary block은 아직 serializer가 실제로 붙이는 source-message memory roots를 양성적으로 적지 않습니다.
- 그 gap은 [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L132)~[app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L210)에서 확인됩니다. 실제 serialized message는 `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`, `session_local_candidate`, `candidate_review_record`를 모두 붙일 수 있습니다.
- 반면 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L104)~[docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L108)은 `candidate_confirmation_record`, `durable_candidate`, `candidate_recurrence_key`, `recurrence_aggregate_candidates`, `review_queue_items`는 적지만, 위 root fields는 positive inventory로 아직 적지 않습니다.
- authoritative docs는 이미 그 root fields를 inventory에 포함합니다. [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L267)~[docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L274), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L177)~[docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L184)이 그 예입니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ACCEPTANCE_CRITERIA session response memory-signal root inventory truth sync`로 고정했습니다.

## 검증
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '92,106p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '257,281p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '167,191p'`
- `nl -ba app/serializers.py | sed -n '35,65p'`
- `nl -ba app/serializers.py | sed -n '300,316p'`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `rg -n 'session_local_memory_signal|superseded_reject_signal|historical_save_identity_signal|session_local_candidate|candidate_confirmation_record|candidate_recurrence_key|durable_candidate|candidate_review_record|review_queue_items' app/serializers.py -S`
- `rg -n 'session_local_memory_signal|superseded_reject_signal|historical_save_identity_signal|session_local_candidate|candidate_confirmation_record|candidate_recurrence_key|durable_candidate|candidate_review_record|review_queue_items' docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md -S`
- `nl -ba app/serializers.py | sed -n '128,212p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '102,108p'`
- `sed -n '1,120p' docs/NEXT_STEPS.md`
- `sed -n '1,120p' docs/MILESTONES.md`
- `sed -n '1,120p' docs/TASK_BACKLOG.md`
- `git status --short`

## 남은 리스크
- [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L92)~[docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L108)의 acceptance-layer top summary block에는 아직 `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`, `session_local_candidate`, `candidate_review_record`의 positive inventory가 빠져 있어 same-family response/message parity drift가 남아 있습니다.
- 작업트리에 unrelated dirty files가 이미 존재하므로, 다음 슬라이스에서도 해당 파일들은 건드리지 않는 전제가 필요합니다.
