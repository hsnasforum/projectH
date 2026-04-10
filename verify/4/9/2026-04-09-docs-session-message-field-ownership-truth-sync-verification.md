# Docs session message field ownership truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-session-message-field-ownership-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-session-message-field-ownership-truth-sync.md`가 직전 verification note가 고정한 current session message field ownership drift를 실제로 닫았는지 다시 확인하고, 같은 docs family 안에서 남은 다음 단일 truth-sync 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-product-spec-test-lock-suite-split-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제 handoff scope를 끝까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 부분적으로 truthful합니다.
  - `docs/PRODUCT_SPEC.md:256-266,279`와 `docs/PRODUCT_SPEC.md:283`가 `original_response_snapshot`, `corrected_text`, `corrected_outcome`, `content_reason_record`를 original grounded-brief source message ownership으로 정리한 부분은 실제 구현과 맞습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:100-101`이 `corrected_text`, `corrected_outcome`, `content_reason_record`를 source-message-only로, `approval_reason_record`를 reject/reissue approval trace message ownership으로 정리한 부분도 맞습니다.
- 하지만 `save_content_source`와 `source_message_id` ownership은 아직 과도하게 좁습니다.
  - `docs/PRODUCT_SPEC.md:277`은 `save_content_source`를 save/approval trace messages only처럼 적고, `docs/PRODUCT_SPEC.md:280`은 `source_message_id`를 save/approval trace messages linking-back field처럼 적습니다.
  - `docs/PRODUCT_SPEC.md:283`도 `approval_reason_record`, `save_content_source`, `source_message_id`를 모두 reject/reissue/save system responses에만 사는 approval-linked trace fields처럼 묶습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:103` 역시 `save_content_source`, `source_message_id`를 save/approval trace messages ownership으로만 적습니다.
- 실제 구현과 테스트는 이보다 넓습니다.
  - grounded-brief source message도 `source_message_id`를 가집니다 (`storage/session_store.py:644-650`).
  - direct approved source-message save path에서는 source message가 `save_content_source`와 `source_message_id`를 같이 가집니다 (`tests/test_web_app.py:6247-6262`, `tests/test_smoke.py:4409-4423`, `tests/test_smoke.py:7638-7656`).
  - 따라서 최신 `/work` closeout의 “세션 메시지 필드 소유권 진실 동기화 완료”는 아직 과합니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ACCEPTANCE_CRITERIA session message save_content_source source_message_id ownership truth sync`로 고정했습니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-session-message-field-ownership-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-product-spec-test-lock-suite-split-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '247,290p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '92,108p'`
- `nl -ba core/agent_loop.py | sed -n '7336,7388p'`
- `nl -ba app/serializers.py | sed -n '96,131p'`
- `nl -ba storage/session_store.py | sed -n '628,700p'`
- `nl -ba tests/test_web_app.py | sed -n '6187,6200p'`
- `nl -ba tests/test_web_app.py | sed -n '6391,6420p'`
- `nl -ba tests/test_web_app.py | sed -n '4442,4448p'`
- `nl -ba tests/test_smoke.py | sed -n '4645,4665p'`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `rg -n "source_message_id\\\"\\]|source_message_id\\\"\\)|\\[\\\"source_message_id\\\"\\].*message|message\\[\\\"source_message_id\\\"\\]" tests/test_web_app.py tests/test_smoke.py -S`
- `nl -ba tests/test_web_app.py | sed -n '6243,6265p'`
- `nl -ba tests/test_smoke.py | sed -n '2741,2752p'`
- `rg -n "source_message_id.*original grounded-brief|owned by save/approval trace messages|source_message_id.*source message" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md -S`
- `rg -n "session\\[\\\"messages\\\"\\]\\[-1\\]\\[\\\"save_content_source\\\"\\]|source_message\\[\\\"save_content_source\\\"\\]|saved_messages\\[-1\\]\\[\\\"save_content_source\\\"\\]|save_content_source.*source message" tests/test_web_app.py tests/test_smoke.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md -S`
- `nl -ba tests/test_smoke.py | sed -n '4407,4423p'`
- `nl -ba tests/test_smoke.py | sed -n '7638,7656p'`
- `rg -n "owned by save/approval trace messages|live on reject/reissue/save system responses|save/approval trace messages linking back to the source message|approval-linked trace fields" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md -S`
- `sed -n '1,240p' .pipeline/claude_handoff.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 `git diff --check`만 다시 확인했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- current session message ownership wording은 거의 닫혔지만 `save_content_source`와 `source_message_id`를 source message에도 존재할 수 있다는 점까지 반영해야 family를 truthfully 닫을 수 있습니다.
