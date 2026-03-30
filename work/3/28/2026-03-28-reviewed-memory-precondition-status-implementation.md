# 2026-03-28 reviewed-memory precondition status implementation

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
- `plandoc/2026-03-28-reviewed-memory-preconditions-contract.md`
- `work/3/28/2026-03-28-reviewed-memory-precondition-status-implementation.md`

## 사용 skill
- `mvp-scope`: current shipped contract와 next-phase reviewed-memory boundary를 다시 섞지 않도록 범위를 확인했습니다.
- `approval-flow-audit`: review acceptance, approval-backed save, historical adjunct가 status basis로 승격되지 않도록 기존 approval/review 경계를 다시 확인했습니다.
- `doc-sync`: aggregate item 내부의 새 read-only status object 구현에 맞춰 root docs와 `plandoc`을 current truth로 맞췄습니다.
- `release-check`: 실제 실행한 `py_compile`, `unittest`, `git diff --check`, `rg`, `make e2e-test` 결과만 기준으로 handoff 상태를 정리합니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 라운드 구현과 남은 리스크를 남깁니다.

## 변경 이유
- 직전 closeout에서 reviewed-memory precondition family는 문서로 고정되었지만, current session payload에는 그 blocked 이유를 aggregate item 단위로 inspect할 수 있는 read-only status surface가 아직 없었습니다.
- 이 상태가 없으면 later reviewed-memory apply, repeated-signal promotion, cross-session counting이 무엇 때문에 아직 막혀 있는지 current serialization에서 정직하게 읽기 어려웠습니다.

## 핵심 변경
- `app/web.py`의 same-session aggregate builder에 `reviewed_memory_precondition_status` helper를 추가했습니다.
- status object는 current aggregate item 아래 read-only sibling 필드로만 붙고, shape는 아래로 고정했습니다:
  - `status_version = same_session_reviewed_memory_preconditions_v1`
  - `overall_status = blocked_all_required`
  - `all_required = true`
  - ordered fixed `preconditions`
  - `future_transition_target = eligible_for_reviewed_memory_draft`
  - `evaluated_at = last_seen_at`
- status basis는 current same-session exact aggregate 존재와 current blocked marker contract만 사용했고, `candidate_review_record`, approval-backed save, historical adjunct, queue presence, fixed statement, task-log replay는 basis에서 계속 제외했습니다.
- `aggregate_promotion_marker`, `recurrence_aggregate_candidates` identity rule, `candidate_recurrence_key`, `durable_candidate`, `candidate_review_record`, `review_queue_items` semantics는 유지했습니다.
- focused regression을 보강해 helper-level / payload-level status emission과 deterministic `evaluated_at` 규칙을 확인했고, docs와 `plandoc`은 object shipped 상태로 동기화했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `169 tests` passed
- `git diff --check`
- `rg -n "reviewed_memory_precondition_status|aggregate_promotion_marker|blocked_pending_reviewed_memory_boundary|future_transition_target|same_session_reviewed_memory_preconditions_v1" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-reviewed-memory-preconditions-contract.md`
- `make e2e-test`
  - `11 passed`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - aggregate-level blocked marker는 shipped 되었지만 exact precondition family를 current payload에서 read-only로 inspect할 수 있는 surface가 없어 later promotion/apply boundary를 직렬화 결과에서 정직하게 읽기 어려웠습니다.
- 이번 라운드에서 해소한 리스크:
  - current aggregate item마다 read-only `reviewed_memory_precondition_status`가 붙으면서 “왜 아직 blocked 인지”가 fixed overall-blocked contract로 payload에 드러납니다.
  - `evaluated_at = last_seen_at`로 고정해 임의 mutable timestamp를 추가하지 않았습니다.
- 여전히 남은 리스크:
  - per-precondition satisfied / unsatisfied 상태는 아직 구현되지 않았고, current repo가 실제 readiness를 평가하지도 않습니다.
  - reviewed-memory store / apply, rollback / disable controls, repeated-signal promotion, cross-session counting은 여전히 미구현입니다.
  - current fixed `confidence_marker = same_session_exact_key_match` 위에 later second conservative level이 필요한지는 여전히 open question입니다.
