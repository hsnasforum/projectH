# Docs task-log candidate confirmation-review detail field-shape truth sync verification

## 변경 파일

- `verify/4/8/2026-04-08-docs-task-log-candidate-confirmation-review-detail-field-shape-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work`의 candidate task-log detail 문서화가 실제 코드와 맞는지 재확인하고, 같은 task-log family에서 남은 가장 작은 current-risk 문서 drift를 다음 Claude 슬라이스로 고정할 필요가 있었습니다.

## 핵심 변경

- 최신 `/work`는 truthful하다고 확인했습니다.
- `docs/PRODUCT_SPEC.md:118`과 `docs/ACCEPTANCE_CRITERIA.md:112`는 `candidate_confirmation_recorded`, `candidate_review_recorded`를 candidate action detail core fields(`message_id`, `artifact_id`, `source_message_id`, `candidate_id`, `candidate_family`, `candidate_updated_at`)로 요약하고 있었습니다.
- `docs/ARCHITECTURE.md:209-210`은 두 action의 exact detail shape를 각각 `{message_id, artifact_id, source_message_id, candidate_id, candidate_family, candidate_updated_at, confirmation_scope, confirmation_label}` / `{message_id, artifact_id, source_message_id, candidate_id, candidate_family, candidate_updated_at, review_scope, review_action, review_status}`로 적고 있었고, 이는 `app/handlers/aggregate.py:82-95`, `app/handlers/aggregate.py:194-207`의 실제 logger와 일치했습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ACCEPTANCE_CRITERIA ARCHITECTURE task-log web-search reload-retry-active-context detail truth sync`로 고정했습니다.
- 다음 슬라이스를 그렇게 잡은 이유는 `docs/ARCHITECTURE.md:215-217`이 아직 `web_search_record_loaded`, `web_search_retried`, `answer_with_active_context`를 action name-only로만 적고 있지만, 실제 구현은 `core/agent_loop.py:6124-6134`, `core/agent_loop.py:6344-6352`, `core/agent_loop.py:6779-6791`에서 exact detail shape를 이미 고정하고 있기 때문입니다.

## 검증

- `sed -n '1,260p' work/4/8/2026-04-08-docs-task-log-candidate-confirmation-review-detail-field-shape-truth-sync.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-docs-corrected-outcome-recorded-shared-core-wording-truth-sync-verification.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '112,122p;800,820p;1528,1544p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '108,116p;1064,1074p;1218,1226p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '204,212p;564,584p;606,626p'`
- `nl -ba app/handlers/aggregate.py | sed -n '76,103p;190,217p'`
- `nl -ba app/handlers/chat.py | sed -n '48,66p;184,200p'`
- `nl -ba core/agent_loop.py | sed -n '6108,6136p;6338,6354p;6772,6792p;8700,8788p'`
- `rg -n "candidate_confirmation_recorded|candidate_review_recorded|corrected_outcome_recorded|message_id|candidate_id|candidate_family|review_action|review_status|confirmation_scope|confirmation_label" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md app/handlers/aggregate.py -S`
- `rg -n "request_received|request_cancelled|document_context_updated|stream_cancel_requested|web_search_permission_updated|permissions_updated|ocr_not_supported|web_search_record_loaded|web_search_retried|answer_with_active_context|reviewed_memory_transition_emitted|reviewed_memory_transition_applied|reviewed_memory_transition_result_confirmed|reviewed_memory_transition_stopped|reviewed_memory_transition_reversed|reviewed_memory_conflict_visibility_checked|agent_response" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md core/agent_loop.py app/handlers/chat.py app/handlers/aggregate.py -S`
- `rg -n "stream_cancel_requested|web_search_permission_updated|permissions_updated|ocr_not_supported|web_search_record_loaded|web_search_retried|answer_with_active_context" docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md tests/test_smoke.py tests/test_web_app.py -S`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md`
- `git diff --check`
- `git status --short`

## 남은 리스크

- task-log docs family 안에는 아직 `stream_cancel_requested`, `web_search_permission_updated`, `permissions_updated`, `ocr_not_supported`, `request_received`, `request_cancelled`, `document_context_updated`, reviewed-memory transition actions의 exact detail shape omission이 남아 있습니다.
- 이번 라운드는 문서/코드 truth 대조만 다시 실행했습니다. 새 unit test나 Playwright는 다시 실행하지 않았습니다.
