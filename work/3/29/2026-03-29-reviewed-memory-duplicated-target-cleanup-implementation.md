# 2026-03-29 reviewed-memory duplicated-target cleanup implementation

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
- `plandoc/2026-03-29-reviewed-memory-planning-target-normalization-contract.md`
- `plandoc/2026-03-29-reviewed-memory-duplicated-target-cleanup-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-duplicated-target-cleanup-implementation.md`

## 사용 skill
- `doc-sync`: cleanup 이후 current shipped truth를 root docs와 relevant `plandoc`에 같이 반영했습니다.
- `release-check`: `py_compile`, focused `unittest`, `make e2e-test`, `git diff --check`, `rg` 결과만 기준으로 round를 닫았습니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 구현과 남은 리스크를 기록했습니다.
- `mvp-scope`: cleanup-only pass가 reviewed-memory apply나 satisfaction widening처럼 읽히지 않도록 MVP 경계를 다시 확인했습니다.

## 변경 이유
- 직전 closeout에서 shared `reviewed_memory_planning_target_ref`는 이미 shipped 되었지만, duplicated target echo fields 세 개가 payload에 그대로 남아 있어 structural redundancy가 계속 남아 있었습니다.
- cleanup contract는 이미 문서로 닫혀 있었고, next smallest slice는 docs / payload / tests를 같은 round에 함께 맞추는 removal pass뿐이었습니다.

## 핵심 변경
- `app/web.py`에서 아래 세 duplicated target echo fields를 together remove 했습니다:
  - `reviewed_memory_precondition_status.future_transition_target`
  - `reviewed_memory_unblock_contract.readiness_target`
  - `reviewed_memory_capability_status.readiness_target`
- `reviewed_memory_planning_target_ref`는 unchanged canonical planning-target source로 유지했습니다:
  - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
  - `target_label = eligible_for_reviewed_memory_draft_planning_only`
  - `target_scope = same_session_exact_recurrence_aggregate_only`
  - `target_boundary = reviewed_memory_draft_planning_only`
  - `defined_at = last_seen_at`
- current blocked truths는 그대로 유지했습니다:
  - `overall_status = blocked_all_required`
  - `unblock_status = blocked_all_required`
  - `capability_outcome = blocked_all_required`
- `tests/test_smoke.py`, `tests/test_web_app.py`는 old target fields absence와 shared-ref-only truth를 검증하도록 갱신했습니다.
- root docs와 `plandoc`는 current shipped truth를 shared-ref-only planning-target source로 다시 맞추고, duplicated echo cleanup이 이미 shipped 되었다는 점을 반영했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `make e2e-test`
- `git diff --check`
- `rg -n "reviewed_memory_planning_target_ref|future_transition_target|readiness_target|eligible_for_reviewed_memory_draft_planning_only|blocked_all_required|unblocked_all_required" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-planning-target-normalization-contract.md plandoc/2026-03-29-reviewed-memory-duplicated-target-cleanup-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - shared ref는 already shipped 되었지만 duplicated target echo fields removal round가 아직 구현되지 않았습니다.
- 이번 라운드에서 해소한 리스크:
  - three-field duplicated target echo fields를 together remove 했고, docs / payload / tests를 같은 round에 맞췄습니다.
  - current planning-target meaning이 `reviewed_memory_planning_target_ref` only source라는 점을 코드와 문서에서 함께 고정했습니다.
- 여전히 남은 리스크:
  - cleanup 뒤 one short compatibility note를 docs와 `/work`에 한 라운드 더 남길지 여부는 아직 open question입니다.
  - reviewed-memory store / apply / emitted transition record / repeated-signal promotion / cross-session counting / user-level memory는 계속 later layer입니다.
