# Docs PRODUCT_SPEC test-lock suite split truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-product-spec-test-lock-suite-split-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-product-spec-test-lock-suite-split-truth-sync.md`가 직전 verification note가 고정한 `PRODUCT_SPEC` response payload test-lock suite split drift를 실제로 닫았는지 다시 확인하고, 같은 payload/session docs family 안에서 남은 다음 단일 truth-sync 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-test-suite-label-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제 handoff scope를 끝까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/PRODUCT_SPEC.md:324`는 이제 `tests/test_web_app.py`를 service tests, `tests/test_smoke.py`를 Python smoke tests, `e2e/tests/web-smoke.spec.mjs`를 separate Playwright browser smoke로 구분하고, control fields와 correction/save field anchors를 이 tests가 잠근다고 직접 적습니다.
  - 이 문구는 이미 truthful했던 `docs/ARCHITECTURE.md:167`, `docs/ACCEPTANCE_CRITERIA.md:121`와 정합합니다.
  - 실제 tree도 이 설명과 맞습니다. response payload는 `app/serializers.py:_serialize_response`에서 직렬화되고, correction/save anchors는 `tests/test_web_app.py`, `tests/test_smoke.py`에 잠겨 있으며, 브라우저 smoke는 `e2e/tests/web-smoke.spec.mjs`에 따로 있습니다.
- 따라서 root docs 기준 response payload test-lock suite split family는 이제 truthful하게 닫혔습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ACCEPTANCE_CRITERIA current session message field ownership truth sync`로 고정했습니다.
  - `docs/PRODUCT_SPEC.md:247-281`와 `docs/ACCEPTANCE_CRITERIA.md:92-103`는 현재 session message/per-message fields를 generic하게 나열하지만, 실제 shipped ownership은 더 좁습니다.
  - 원본 grounded-brief source message는 `original_response_snapshot`, `corrected_text`, `corrected_outcome`, `content_reason_record`의 source-of-truth surface로 남고, reject/reissue system responses와 live pending approvals는 `approval_reason_record`를 갖고, save/system trace messages는 `save_content_source`와 `source_message_id`를 미러링할 수 있습니다.
  - non-source system messages는 correction source-of-truth surface가 아니며, 이 경계는 `core/agent_loop.py:7336-7387`, `app/serializers.py:96-131`, `storage/session_store.py:628-700`, `tests/test_web_app.py:6198-6199`, `tests/test_web_app.py:6391-6420`, `tests/test_web_app.py:4442-4447`, `tests/test_smoke.py:4645-4665`에서 확인됩니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-product-spec-test-lock-suite-split-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-test-suite-label-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '285,335p'`
- `rg -n "tests/test_web_app.py|tests/test_smoke.py|web-smoke.spec.mjs|original_response_snapshot|corrected_outcome|save_content_source|approval_reason_record|content_reason_record|Control Fields \\(drive shell behavior and test assertions\\)|current top-level fields" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md tests/test_web_app.py tests/test_smoke.py e2e/tests/web-smoke.spec.mjs -S`
- `git diff -- docs/PRODUCT_SPEC.md`
- `git diff --check`
- `rg -n "response payload|_serialize_response|control fields|correction/save field anchors|Playwright browser smoke|Python smoke tests|tests/test_smoke.py|tests/test_web_app.py|web-smoke.spec.mjs" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md -S`
- `git status --short`
- `rg -n "Current Message Fields|session payload|pending_approvals|approval_reason_record|content_reason_record|original_response_snapshot|corrected_outcome|save_content_source|tests/test_smoke.py|tests/test_web_app.py" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '80,113p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '247,284p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '135,169p'`
- `rg -n "Current Message Fields|session payload|pending_approvals|messages\\[-1\\]|session\\]\\[\\\"messages\\\"\\]|response\\]\\[\\\"artifact_id\\\"\\]|approval_reason_record|content_reason_record|original_response_snapshot" tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n "def _serialize_message|serialize_message|response_origin|selected_source_paths|note_preview|approval_reason_record|content_reason_record|original_response_snapshot|save_content_source" app/serializers.py storage/session_store.py core/agent_loop.py -S`
- `nl -ba app/serializers.py | sed -n '330,430p'`
- `nl -ba storage/session_store.py | sed -n '1,260p'`
- `nl -ba storage/session_store.py | sed -n '600,700p'`
- `nl -ba app/serializers.py | sed -n '1,90p'`
- `nl -ba app/serializers.py | sed -n '90,170p'`
- `rg -n "selected_source_paths|note_preview|response_origin|evidence|summary_chunks|claim_coverage_progress_summary|follow_up_suggestions|saved_note_path" storage/session_store.py -S`
- `rg -n "append_response_message|selected_source_paths|note_preview|response_origin|summary_chunks|evidence" core/agent_loop.py storage/session_store.py -S`
- `nl -ba core/agent_loop.py | sed -n '7270,7365p'`
- `nl -ba core/agent_loop.py | sed -n '7365,7388p'`
- `nl -ba tests/test_web_app.py | sed -n '6187,6265p'`
- `rg -n "content_reason_record" tests/test_web_app.py tests/test_smoke.py -S`
- `nl -ba tests/test_web_app.py | sed -n '4388,4460p'`
- `nl -ba tests/test_smoke.py | sed -n '4645,4665p'`
- `sed -n '1,240p' .pipeline/claude_handoff.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 `git diff --check`만 다시 확인했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- current session message docs는 아직 field ownership을 top-level summary에서 직접 잠그지 않아, source-message-only correction fields와 approval/system trace fields의 경계를 한 번 더 정리하는 편이 안전합니다.
