## 변경 파일
- `verify/4/8/2026-04-08-docs-acceptance-criteria-session-pending-approvals-active-context-field-shape-summary-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- 최신 `/work`의 `docs/ACCEPTANCE_CRITERIA.md` 수정이 실제 authoritative docs와 serializer 계약에 맞는지 재확인하고, 같은 session-schema family에서 남은 가장 작은 acceptance-layer drift를 다음 Claude 슬라이스로 고정하기 위해 검증했습니다.

## 핵심 변경
- 최신 `/work`의 실제 수정은 맞았습니다.
- [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L87)와 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L89)는 실제로 `pending_approvals`의 serialized approval object list와 `active_context`의 `{kind, label, source_paths, summary_hint, suggested_prompts, record_path, claim_coverage_progress_summary}` shape를 반영하고 있었고, 이는 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L218), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L142), [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L251), [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L318)와 일치했습니다.
- 다만 `/work`의 `남은 리스크 없음` 결론은 과했습니다. [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L92)는 아직 `response_origin`, `evidence`, `summary_chunks`, `claim_coverage`, `claim_coverage_progress_summary`, `web_search_history`, `feedback`, `corrected_text`, `corrected_outcome`, `content_reason_record`, `approval_reason_record`, `original_response_snapshot` 계열을 generic sentence로만 묶고 있습니다.
- 반면 [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L257), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L261), [docs/PRODUCT_SPEC.md](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L418), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L167), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L171), [docs/ARCHITECTURE.md](/home/xpdlqj/code/projectH/docs/ARCHITECTURE.md#L299), 그리고 [app/serializers.py](/home/xpdlqj/code/projectH/app/serializers.py#L268)은 이미 해당 response/session metadata inventory와 exact shape를 더 구체적으로 설명하거나 직렬화하고 있습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ACCEPTANCE_CRITERIA session response metadata field-shape inventory truth sync`로 고정했습니다.

## 검증
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '82,92p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '218,221p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '142,145p'`
- `nl -ba app/serializers.py | sed -n '247,257p'`
- `nl -ba app/serializers.py | sed -n '318,333p'`
- `sed -n '1,120p' docs/NEXT_STEPS.md`
- `sed -n '1,120p' docs/MILESTONES.md`
- `sed -n '1,120p' docs/TASK_BACKLOG.md`
- `rg -n 'pending_approvals|active_context|response metadata|response_origin|web_search_history|original_response_snapshot|evidence|summary_chunks|claim_coverage|corrected_text|approval_reason_record|content_reason_record' docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md -S`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '90,96p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '250,265p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '166,176p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '476,486p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '298,304p'`
- `rg -n 'claim_coverage_progress_summary|web_search_history' docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md -S`
- `nl -ba app/serializers.py | sed -n '268,295p'`
- `git diff --check`
- `git status --short`

## 남은 리스크
- [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L92)는 아직 response/session metadata를 generic sentence로만 묶고 있어 authoritative acceptance layer에서 session summary inventory drift가 남아 있습니다.
- 작업트리에 unrelated dirty files가 이미 존재하므로, 다음 슬라이스에서도 해당 파일들은 건드리지 않는 전제가 필요합니다.
