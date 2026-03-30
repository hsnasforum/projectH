# 2026-03-28 accept-only review action implementation

## 변경 파일
- `app/web.py`
- `app/templates/index.html`
- `storage/session_store.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-review-action-contract.md`

## 사용 skill
- `approval-flow-audit`
- `e2e-smoke-triage`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 남은 핵심 리스크는 shipped `review_queue_items`가 inspection only였고, actioned item을 current source message에 어떻게 남기고 pending queue에서 어떻게 빼는지 실제 상태 전이가 없다는 점이었습니다.
- 이번 라운드에서는 그 경계를 가장 작게 닫기 위해 `accept` only review action을 same source-message anchor 위에 추가하고, reviewed-but-not-applied 상태만 기록하도록 구현했습니다.

## 핵심 변경
- same source message에 optional sibling `candidate_review_record`를 추가했습니다.
  - shape: `candidate_id`, `candidate_updated_at`, `artifact_id`, `source_message_id`, `review_scope = source_message_candidate_review`, `review_action = accept`, `review_status = accepted`, `recorded_at`
- review action basis는 current source-message `durable_candidate` exact match로만 제한했습니다.
  - same `artifact_id`
  - same `source_message_id`
  - same `candidate_id`
  - same `candidate_updated_at`
- `review_queue_items`는 이제 current `durable_candidate`가 있고 `promotion_eligibility = eligible_for_review`이며 matching current `candidate_review_record`가 없을 때만 pending item으로 남습니다.
- `accept` 후에는 pending queue item이 사라지지만, `session_local_candidate`, `candidate_confirmation_record`, `durable_candidate`는 그대로 유지됩니다.
- approval-backed save는 계속 supporting evidence only로 남겼습니다.
  - save support alone으로 queue eligibility나 review outcome이 생기지 않도록 service/storage validation을 고정했습니다.
- later correction / rejected outcome 전이에서 stale `candidate_review_record`가 current state에 남지 않도록 clear 규칙을 추가했습니다.
- task-log에 review-side audit event `candidate_review_recorded`를 추가했습니다.
- 기존 candidate-confirmation browser smoke를 최소 확장해서 `검토 수락` 버튼, notice, pending queue removal, current source-message review trace, later stale-clear를 검증하도록 갱신했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_web_app`
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `make e2e-test`
- `git diff --check`
- `rg -n "candidate_review_record|review_action|review_status|review_queue|durable_candidate|candidate_confirmation_record|eligible_for_review" app/templates/index.html app/web.py storage/session_store.py storage/task_log.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-review-action-contract.md`

## 남은 리스크
- 이번 라운드에서 해소한 리스크:
  - shipped queue 위의 first review action 부재
  - pending queue item removal 규칙 부재
  - source-message review trace와 queue 상태 전이의 current implementation 부재
- 여전히 남은 리스크:
  - `edit` / `reject` / `defer`는 아직 미구현입니다.
  - reviewed-history surface와 reviewed-memory store는 아직 없습니다.
  - user-level memory, rollback, scope suggestion, second durable store는 계속 later layer입니다.
  - `candidate_id`가 아직 source-message candidate id를 재사용하므로 later durable-scope id boundary는 여전히 open question입니다.
