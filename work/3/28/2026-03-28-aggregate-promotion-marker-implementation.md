# 2026-03-28 aggregate promotion marker implementation

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
- `plandoc/2026-03-28-post-aggregate-promotion-boundary.md`

## 사용 skill
- `approval-flow-audit`: review acceptance, approval-backed save, queue semantics가 marker basis로 승격되지 않도록 기존 approval/review 경계를 다시 확인했습니다.
- `doc-sync`: aggregate item 내부 marker 구현에 맞춰 root docs와 `plandoc`을 current truth로 맞췄습니다.
- `release-check`: 실제 실행한 `py_compile`, `unittest`, `git diff --check`, `rg`, `make e2e-test` 결과만 기준으로 handoff 상태를 정리합니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 라운드 구현과 남은 리스크를 남깁니다.

## 변경 이유
- 직전 closeout에서 same-session `recurrence_aggregate_candidates` 위의 post-aggregate promotion boundary는 문서로 고정됐지만, 실제 session serialization에는 그 blocked 상태를 드러내는 smallest marker가 아직 없었습니다.
- 이번 라운드는 repeated-signal promotion, reviewed-memory store/apply, cross-session counting을 열지 않은 채, current aggregate가 왜 아직 promotion-ineligible인지 read-only로 드러내는 최소 구현이 필요했습니다.

## 핵심 변경
- `app/web.py`의 same-session aggregate builder에 `aggregate_promotion_marker` helper를 추가했습니다.
- marker는 aggregate item 내부 sibling 필드로만 붙고, shape는 아래로 고정했습니다:
  - `promotion_basis = same_session_exact_recurrence_aggregate`
  - `promotion_eligibility = blocked_pending_reviewed_memory_boundary`
  - `reviewed_memory_boundary = not_open`
  - `marker_version = same_session_blocked_reviewed_memory_v1`
  - `derived_at = last_seen_at`
- marker basis는 current same-session exact aggregate 존재 여부만 사용했고, review acceptance / approval-backed save / historical adjunct / queue presence / fixed statement / task-log replay는 basis에서 계속 제외했습니다.
- `candidate_recurrence_key`, `recurrence_aggregate_candidates` identity rule, `durable_candidate`, `candidate_review_record`, `review_queue_items` semantics는 유지했습니다.
- focused regression을 보강해 helper-level / payload-level marker emission과 deterministic `derived_at` 규칙을 확인했고, docs와 `plandoc`은 marker shipped 상태로 동기화했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `169 tests` passed
- `git diff --check`
- `rg -n "aggregate_promotion_marker|promotion_basis|promotion_eligibility|reviewed_memory_boundary|recurrence_aggregate_candidates|candidate_recurrence_key|same_session_exact_key_match" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-post-aggregate-promotion-boundary.md`
- `make e2e-test`
  - `11 passed`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - same-session aggregate는 이미 shipped 되었지만, aggregate 위 blocked promotion boundary가 실제 payload에 드러나지 않아 later promotion work를 과장해서 열 위험이 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - current aggregate item마다 read-only `aggregate_promotion_marker`가 붙으면서 “exact aggregate identity는 있지만 reviewed-memory boundary가 아직 닫혀 있어서 promotion-ineligible”이라는 현재 truth가 payload에 드러납니다.
  - marker는 deterministic `derived_at = last_seen_at`로 고정해 임의 mutable timestamp를 추가하지 않았습니다.
- 여전히 남은 리스크:
  - rollback / disable / conflict / operator-audit precondition의 정확한 shape는 아직 미정입니다.
  - reviewed-memory store / apply와 cross-session counting을 열 local store precondition도 아직 미정입니다.
  - `confidence_marker = same_session_exact_key_match` 위에 later second conservative level이 필요한지는 여전히 open question입니다.
