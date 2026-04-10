# Docs save_content_source source_message_id ownership truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync.md`가 직전 verification note가 고정한 `save_content_source` / `source_message_id` session-message ownership drift를 실제로 닫았는지 다시 확인하고, 같은 current session docs family 안에서 남은 다음 단일 truth-sync 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-session-message-field-ownership-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제 handoff scope를 끝까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/PRODUCT_SPEC.md:277-283`은 이제 `save_content_source`와 `source_message_id`가 grounded-brief source message direct-approved-save path와 save/approval trace messages 양쪽에 나타날 수 있다고 적습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:103`도 같은 ownership 확장을 반영합니다.
  - 이 문구는 `storage/session_store.py:644-650`, `tests/test_web_app.py:6247-6262`, `tests/test_smoke.py:4409-4423`, `tests/test_smoke.py:7638-7656`와 맞습니다.
- 따라서 current session message ownership family는 이제 truthful하게 닫혔습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ACCEPTANCE_CRITERIA current session response_origin omission truth sync`로 고정했습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:93`은 current session per-message `response_origin`을 `or null when absent`처럼 적지만, 실제 session messages는 없을 때 `null`로 직렬화되지 않고 키가 빠집니다.
  - 이 차이는 top-level response payload와 다릅니다. top-level payload의 `response_origin`은 `null`일 수 있지만 (`app/serializers.py:53`, `docs/PRODUCT_SPEC.md:312`), session message surface는 `core/agent_loop.py:7367-7368`, `app/serializers.py:91-100`, `app/localization.py:146-177` 기준으로 present-when-available / omitted-when-absent semantics입니다.
  - `docs/PRODUCT_SPEC.md`는 이미 `Current Message Fields`를 optional list로 두고 있어 same-family drift는 현재 `ACCEPTANCE_CRITERIA` 한 줄에 가장 작게 남아 있습니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-session-message-field-ownership-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '272,285p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '99,105p'`
- `nl -ba storage/session_store.py | sed -n '644,650p'`
- `nl -ba tests/test_web_app.py | sed -n '6247,6262p'`
- `nl -ba tests/test_smoke.py | sed -n '4409,4423p'`
- `nl -ba tests/test_smoke.py | sed -n '7638,7656p'`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `rg -n "response_origin|original_response_snapshot|corrected_outcome|approval_reason_record|content_reason_record|save_content_source|note_preview|selected_source_paths|claim_coverage_progress_summary" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n "assertNotIn\\(|NotIn\\(" tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n "response_origin|original_response_snapshot|corrected_outcome|approval_reason_record|content_reason_record|save_content_source|note_preview|selected_source_paths|claim_coverage_progress_summary" app/serializers.py core/agent_loop.py storage/session_store.py -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '452,470p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '520,531p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '92,105p'`
- `nl -ba app/serializers.py | sed -n '91,100p'`
- `nl -ba app/localization.py | sed -n '141,178p'`
- `nl -ba core/agent_loop.py | sed -n '7365,7369p'`
- `sed -n '1,220p' .pipeline/claude_handoff.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 `git diff --check`만 다시 확인했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- current session docs family에서는 `docs/ACCEPTANCE_CRITERIA.md:93`의 `response_origin` absence semantics가 아직 top-level payload와 섞여 읽히므로, 그 한 줄을 session-message reality에 맞게 분리하는 편이 안전합니다.
