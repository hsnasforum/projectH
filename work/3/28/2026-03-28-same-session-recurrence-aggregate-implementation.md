## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-post-key-aggregation-boundary.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 truthful `candidate_recurrence_key`는 이미 shipped 되었지만, same-session 안에서 distinct grounded-brief source messages를 정직하게 묶는 first aggregation surface가 아직 없어 repeated-signal promotion이나 same-family merge를 과장해서 열 위험이 남아 있었습니다.
- 이번 라운드는 그 리스크를 닫기 위해, current persisted session state만 canonical source로 쓰는 same-session-only read-only `recurrence_aggregate_candidates` projection을 실제 코드로 구현하고 문서를 현재 구현 사실에 맞춰 동기화했습니다.

## 핵심 변경
- `app/web.py` session serialization에 optional top-level `recurrence_aggregate_candidates` projection을 추가했습니다.
- aggregate identity basis는 current source-message `candidate_recurrence_key`의 exact match만 사용합니다:
  - `candidate_family`
  - `key_scope`
  - `key_version`
  - `derivation_source`
  - `normalized_delta_fingerprint`
- aggregate는 같은 세션 안에서 서로 다른 `artifact_id` + `source_message_id` anchor가 2개 이상일 때만 생기도록 제한했습니다.
- `supporting_candidate_refs`와 optional `supporting_review_refs`는 `artifact_id`, `source_message_id`, `candidate_id`, `candidate_updated_at` exact current-version join만 허용했습니다.
- `confidence_marker`는 과장 없이 고정값 `same_session_exact_key_match`로 두고, review acceptance / durable / approval-backed save / historical adjunct는 identity basis로 승격하지 않았습니다.
- `session_local_candidate`, `durable_candidate`, `candidate_review_record`, `candidate_recurrence_key`, `review_queue_items` 기존 semantics는 유지했고, repeated-signal promotion / merge helper / reviewed-memory store / user-level memory / cross-session counting은 열지 않았습니다.
- focused regression을 추가했습니다:
  - helper-level exact identity grouping, same-anchor dedupe, review support ref, non-basis exclusion
  - web-app payload-level aggregate emission, review support ref 노출, save-support / historical-adjunct-only omission
- 문서는 shipped same-session aggregate projection과 fixed `confidence_marker = same_session_exact_key_match`를 현재 구현 사실로 반영했고, next priority는 post-aggregate promotion / reviewed-memory boundary 정의로 한 단계 이동시켰습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `169 tests` passed
- `git diff --check`
- `rg -n "recurrence_aggregate_candidates|candidate_recurrence_key|normalized_delta_fingerprint|candidate_review_record|durable_candidate|same_session_current_state_only|recurrence_count" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-post-key-aggregation-boundary.md`
- `make e2e-test`
  - `11 passed`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 “post-key aggregation boundary 부재”는 이번 라운드에서 해소했습니다. 이제 same-session current state 안에서는 exact recurrence identity를 가진 distinct grounded briefs를 정직하게 묶을 수 있습니다.
- 이번 라운드에서 의도적으로 남겨둔 리스크:
  - repeated-signal promotion은 여전히 미구현입니다.
  - same-family merge helper는 여전히 닫혀 있습니다.
  - cross-session counting은 local store / rollback / reviewed-memory boundary 없이는 여전히 열 수 없습니다.
  - `confidence_marker`는 현재 fixed conservative value 하나뿐이라 later reviewed-memory vocabulary가 열릴 때 재검토가 필요할 수 있습니다.
