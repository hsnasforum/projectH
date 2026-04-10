# Docs memory-candidate root ownership truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-memory-candidate-root-ownership-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-memory-candidate-root-ownership-truth-sync.md`가 직전 verification note가 고정한 `PRODUCT_SPEC` / `ACCEPTANCE_CRITERIA` current-message memory/candidate root ownership drift를 실제로 닫았는지 다시 확인하고, 같은 current-session docs family 안에서 남은 다음 단일 truth-sync 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-architecture-session-message-field-ownership-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제 handoff scope를 끝까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/PRODUCT_SPEC.md:267-274`는 이제 `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`, `session_local_candidate`, `candidate_confirmation_record`, `candidate_recurrence_key`, `durable_candidate`, `candidate_review_record`를 grounded-brief source-message owned roots / sibling projections로 적습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:106-109`도 같은 memory/candidate roots를 grounded-brief source-message anchored surface로 적고, `candidate_confirmation_record` / `candidate_recurrence_key` / `durable_candidate` separation을 다시 닫습니다.
  - 이 문구는 `storage/session_store.py:519-575`, `app/serializers.py:164-212`, `app/serializers.py:4238-4255`, `app/serializers.py:4354-4465`, `tests/test_web_app.py:899-985`와 맞습니다.
- 따라서 직전 verification note가 고정했던 `PRODUCT_SPEC` / `ACCEPTANCE_CRITERIA` current-message memory/candidate root ownership drift는 닫혔습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ARCHITECTURE current message memory-candidate root condition truth sync`로 고정했습니다.
  - `docs/ARCHITECTURE.md:222-229`는 이제 broad ownership은 맞지만, 같은 family의 다른 두 문서가 이미 담은 조건 해상도까지는 닫지 못합니다.
  - 남은 차이는 다음과 같습니다.
    - `session_local_memory_signal`은 실제로 `original_response_snapshot`이 있는 grounded-brief source message에서만 구체화됩니다 (`storage/session_store.py:519-530`).
    - `session_local_candidate` / `candidate_recurrence_key`는 같은 source-message anchor를 전제로 합니다 (`app/serializers.py:4354-4465`).
    - `candidate_confirmation_record` / `durable_candidate` / `candidate_review_record`는 same-message sibling / exact join 조건을 전제로 합니다 (`app/serializers.py:164-212`, `app/serializers.py:4238-4255`).
  - `docs/PRODUCT_SPEC.md:267-274`와 `docs/ACCEPTANCE_CRITERIA.md:106-109`는 이미 그 narrower condition을 반영하므로, 같은 family에서 남은 가장 작은 truth-sync는 `ARCHITECTURE` current-message block의 detail alignment입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-memory-candidate-root-ownership-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-architecture-session-message-field-ownership-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '262,278p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '100,112p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '215,233p'`
- `nl -ba storage/session_store.py | sed -n '519,575p'`
- `nl -ba app/serializers.py | sed -n '164,212p'`
- `nl -ba tests/test_web_app.py | sed -n '899,985p'`
- `rg -n "session_local_memory_signal|superseded_reject_signal|historical_save_identity_signal|session_local_candidate|candidate_confirmation_record|candidate_recurrence_key|durable_candidate|candidate_review_record" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md -S`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `sed -n '1,240p' .pipeline/claude_handoff.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 `git diff --check`만 다시 확인했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `docs/ARCHITECTURE.md:222-229`는 broad ownership만 적고 있어, current-message memory/candidate roots의 anchor / sibling / join 조건까지 같은 해상도로 맞추려면 한 번 더 정리하는 편이 안전합니다.
