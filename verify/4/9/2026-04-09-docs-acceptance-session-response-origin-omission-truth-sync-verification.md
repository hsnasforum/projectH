# Docs acceptance session response_origin omission truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-acceptance-session-response-origin-omission-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-acceptance-session-response-origin-omission-truth-sync.md`가 직전 verification note가 고정한 `ACCEPTANCE_CRITERIA` per-message `response_origin` omission drift를 실제로 닫았는지 다시 확인하고, 같은 current-session docs family 안에서 남은 다음 단일 truth-sync 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제 handoff scope를 끝까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:93`은 이제 current session per-message `response_origin`을 `when present; omitted from the session message when absent (unlike the top-level response payload, which returns null)`로 적고 있습니다.
  - 이 문구는 `core/agent_loop.py:7367-7368`, `app/serializers.py:91-100`, `app/localization.py:146-177`과 맞습니다. session message surface는 `response_origin`이 있을 때만 키를 쓰고, 없을 때 `null`을 합성하지 않습니다.
- 따라서 직전 verification note가 고정했던 `ACCEPTANCE_CRITERIA` 한 줄 드리프트는 닫혔습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ARCHITECTURE current session message field ownership truth sync`로 고정했습니다.
  - `docs/ARCHITECTURE.md:196-229`의 current message block은 아직 `response_origin`, `corrected_text`, `corrected_outcome`, `content_reason_record`, `save_content_source`, `source_message_id`, `approval_reason_record`를 generic optional metadata처럼만 나열합니다.
  - 실제 현재 계약은 더 좁습니다.
    - session-message `response_origin`은 present-when-available / omitted-when-absent semantics입니다 (`core/agent_loop.py:7367-7368`, `app/serializers.py:91-100`, `app/localization.py:146-177`).
    - `original_response_snapshot`, `corrected_text`, `corrected_outcome`, `content_reason_record`는 원본 grounded-brief source message surface에 붙습니다 (`storage/session_store.py:628-650`, `tests/test_web_app.py:4420-4447`, `tests/test_web_app.py:6247-6254`).
    - `save_content_source`와 `source_message_id`는 direct-approved grounded-brief source message와 save/approval trace messages 양쪽에 나타날 수 있습니다 (`storage/session_store.py:644-650`, `tests/test_smoke.py:4409-4414`, `tests/test_web_app.py:6243-6247`).
    - `approval_reason_record`는 reject/reissue approval trace 쪽에 붙고, content-reject source message에는 붙지 않습니다 (`tests/test_smoke.py:2913-2918`, `tests/test_web_app.py:500-504`, `tests/test_smoke.py:4647-4651`).
  - `docs/PRODUCT_SPEC.md:247-283`와 `docs/ACCEPTANCE_CRITERIA.md:92-105`는 이미 이 narrower ownership을 반영하므로, 남은 가장 작은 same-family drift는 `ARCHITECTURE` current-message block 정렬입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-acceptance-session-response-origin-omission-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '240,265p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '265,286p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '300,326p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '455,468p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '523,531p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '120,185p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '185,210p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '196,212p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '210,230p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '88,108p'`
- `nl -ba app/serializers.py | sed -n '84,102p'`
- `nl -ba app/localization.py | sed -n '141,178p'`
- `nl -ba core/agent_loop.py | sed -n '7365,7369p'`
- `nl -ba storage/session_store.py | sed -n '318,334p'`
- `nl -ba storage/session_store.py | sed -n '628,650p'`
- `nl -ba tests/test_web_app.py | sed -n '496,506p'`
- `nl -ba tests/test_web_app.py | sed -n '4380,4460p'`
- `nl -ba tests/test_web_app.py | sed -n '6242,6254p'`
- `nl -ba tests/test_smoke.py | sed -n '2910,2920p'`
- `nl -ba tests/test_smoke.py | sed -n '4406,4415p'`
- `nl -ba tests/test_smoke.py | sed -n '4647,4653p'`
- `nl -ba tests/test_smoke.py | sed -n '4671,4689p'`
- `nl -ba tests/test_smoke.py | sed -n '7688,7701p'`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "response_origin" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md tests/test_web_app.py tests/test_smoke.py core/agent_loop.py app/serializers.py app/localization.py storage/session_store.py -S`
- `rg -n "omitted from the session message|or null when absent|when present; omitted|Current Message Fields|Per-message fields include|Session JSON stores|response metadata is serializable back into the session|message-level" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n "Current Message Fields|messages|response_origin|source_message_id|save_content_source|original_response_snapshot|corrected_text|corrected_outcome|approval_reason_record|content_reason_record" docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md storage/session_store.py app/serializers.py core/agent_loop.py tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n "Current message records include|response_origin|original_response_snapshot|corrected_text|corrected_outcome|content_reason_record|save_content_source|source_message_id|approval_reason_record" docs/ARCHITECTURE.md -S`
- `rg -n 'assert(Not)?In\\("response_origin"|\\["response_origin"\\]|get\\("response_origin"\\)' tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n 'response_origin\"\\)|assertNotIn\\(\"response_origin\"|assertNotIn\\(\"response_origin\",|assertNotIn\\(\"response_origin\"' tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n 'message\\["response_origin"\\]|get\\("response_origin"\\)|"response_origin" in .*messages|session\\["messages"\\].*response_origin|payload\\["session"\\]\\["messages"\\].*response_origin' tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n "response_origin.*test|test.*response_origin|lock.*response_origin|response_origin.*lock|serialize.*response_origin|session message.*response_origin|per-message.*response_origin" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n "response_origin" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n "save_content_source|source_message_id|approval_reason_record|content_reason_record|corrected_outcome|corrected_text|original_response_snapshot|selected_source_paths|saved_note_path|note_preview" docs/ARCHITECTURE.md -S`
- `rg -n 'current session|session message|response metadata|per-message' docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md -S`
- `sed -n '1,220p' .pipeline/claude_handoff.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 `git diff --check` 중심으로만 다시 확인했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `docs/ARCHITECTURE.md:196-229`의 current message block은 아직 current shipped ownership을 한 줄 generic list로 눌러 적고 있어, 다음 라운드에서 `PRODUCT_SPEC` / `ACCEPTANCE_CRITERIA`와 같은 해상도로 맞추는 편이 안전합니다.
