# 2026-03-28 reviewed-memory boundary draft implementation

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
- `plandoc/2026-03-28-reviewed-memory-boundary-defined-contract.md`
- `work/3/28/2026-03-28-reviewed-memory-boundary-draft-implementation.md`

## 사용 skill
- `mvp-scope`: current shipped aggregate/status surface와 future reviewed-memory boundary draft를 다시 섞지 않도록 범위를 좁혔습니다.
- `approval-flow-audit`: review acceptance, approval-backed save, historical adjunct, queue presence가 draft basis로 승격되지 않도록 approval/review 경계를 다시 확인했습니다.
- `doc-sync`: aggregate item 내부의 새 read-only `reviewed_memory_boundary_draft` 구현에 맞춰 root docs와 `plandoc`을 current truth로 맞췄습니다.
- `release-check`: 실제 실행한 `py_compile`, `unittest`, `git diff --check`, `rg`, `make e2e-test` 결과만 기준으로 handoff 상태를 정리합니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 라운드 구현과 남은 리스크를 남깁니다.

## 변경 이유
- 직전 closeout에서 `reviewed_memory_boundary_defined` exact contract는 닫혔지만, current session payload에는 그 later boundary를 가리키는 read-only `reviewed_memory_boundary_draft`가 아직 없었습니다.
- 이 object가 없으면 `future_transition_target = eligible_for_reviewed_memory_draft`가 실제 직렬화 결과에서 어떤 later object를 가리키는지 여전히 추상적으로만 남아 있었습니다.

## 핵심 변경
- `app/web.py`의 same-session aggregate builder에 `reviewed_memory_boundary_draft` helper를 추가했습니다.
- draft object는 current aggregate item 아래 read-only sibling 필드로만 붙고, shape는 아래로 고정했습니다:
  - `boundary_version = fixed_narrow_reviewed_scope_v1`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - `aggregate_identity_ref`
  - `supporting_source_message_refs`
  - `supporting_candidate_refs`
  - optional `supporting_review_refs`
  - `boundary_stage = draft_not_applied`
  - `drafted_at = last_seen_at`
- draft basis는 current same-session exact aggregate 존재, current blocked marker, current blocked-only precondition status, 그리고 exact current supporting refs만 사용했고, `candidate_review_record`는 optional support ref일 뿐 identity basis를 넓히지 않게 유지했습니다.
- `aggregate_promotion_marker`, `reviewed_memory_precondition_status`, `recurrence_aggregate_candidates` identity rule, `candidate_recurrence_key`, `durable_candidate`, `candidate_review_record`, `review_queue_items` semantics는 유지했습니다.
- focused regression을 보강해 helper-level / payload-level draft emission과 deterministic `drafted_at` 규칙을 확인했고, docs와 `plandoc`은 draft shipped 상태로 동기화했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `169 tests` passed
- `git diff --check`
- `rg -n "reviewed_memory_boundary_draft|same_session_exact_recurrence_aggregate_only|aggregate_identity_ref|boundary_stage|reviewed_memory_precondition_status|aggregate_promotion_marker" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-reviewed-memory-boundary-defined-contract.md`
- `make e2e-test`
  - `11 passed`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - exact reviewed-memory boundary contract는 닫혔지만, current payload에는 그 later boundary를 가리키는 read-only `reviewed_memory_boundary_draft`가 없어 `eligible_for_reviewed_memory_draft`의 실체가 추상적으로만 남아 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - current aggregate item마다 read-only `reviewed_memory_boundary_draft`가 붙으면서 fixed narrow reviewed scope와 exact aggregate-supporting refs가 payload에 드러납니다.
  - `drafted_at = last_seen_at`로 고정해 임의 mutable timestamp를 추가하지 않았습니다.
- 여전히 남은 리스크:
  - draft는 boundary object일 뿐 readiness/satisfaction tracker가 아니고, rollback / disable / conflict / operator-audit mechanics는 여전히 미구현입니다.
  - reviewed-memory store / apply, repeated-signal promotion, cross-session counting, user-level memory는 계속 닫혀 있습니다.
  - shipped `reviewed_memory_boundary_draft`의 redundant `reviewed_scope` label을 장기적으로 유지할지, later normalization에서 줄일지는 여전히 open question입니다.
