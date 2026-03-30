# 2026-03-29 reviewed-memory planning-target-ref implementation

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
- `work/3/29/2026-03-29-reviewed-memory-planning-target-ref-implementation.md`

## 사용 skill
- `mvp-scope`: current shipped same-session aggregate contract와 later cleanup question을 분리한 채 additive shared-ref 범위를 좁게 유지했습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log` replay가 planning-target basis처럼 읽히지 않는 current safety boundary를 다시 확인했습니다.
- `doc-sync`: payload 구현과 root docs / `plandoc`를 current shipped truth에 맞춰 함께 동기화했습니다.
- `release-check`: 실제 실행한 `py_compile`, `unittest`, `make e2e-test`, `git diff --check`, `rg` 결과만 기준으로 round를 닫았습니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 구현과 남은 cleanup risk를 기록했습니다.

## 변경 이유
- 직전 closeout에서 current payload는 planning-only meaning을 정확히 담고 있었지만, 세 target field가 같은 label을 중복 노출하고 있고 shared planning-target ref는 아직 materialize되지 않았다는 리스크를 이어받았습니다.
- 이 상태에서 duplicated-field cleanup이나 later widening을 먼저 건드리면 hidden semantic drift, partial migration, old/new mixed truth가 다시 생길 수 있었습니다.

## 핵심 변경
- current same-session `recurrence_aggregate_candidates` item 아래에 additive read-only `reviewed_memory_planning_target_ref`를 materialize했습니다.
- current emitted shape는 아래로 고정했습니다:
  - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
  - `target_label = eligible_for_reviewed_memory_draft_planning_only`
  - `target_scope = same_session_exact_recurrence_aggregate_only`
  - `target_boundary = reviewed_memory_draft_planning_only`
  - `defined_at = aggregate.last_seen_at`
- current three target fields는 그대로 유지했습니다:
  - `reviewed_memory_precondition_status.future_transition_target`
  - `reviewed_memory_unblock_contract.readiness_target`
  - `reviewed_memory_capability_status.readiness_target`
- 위 세 field는 모두 `reviewed_memory_planning_target_ref.target_label`의 exact derived echo가 되도록 helper와 회귀를 함께 고정했습니다.
- current blocked / satisfied / transition / apply semantics는 바꾸지 않았습니다:
  - `overall_status = blocked_all_required`
  - `unblock_status = blocked_all_required`
  - `capability_outcome = blocked_all_required`
- `candidate_review_record`, approval-backed save, historical adjunct, `task_log` replay alone은 planning-target basis에 포함하지 않았고, new ref도 meaning clarification only로 유지했습니다.
- `docs/`와 `plandoc/`는 shared planning-target ref가 now shipped truth라는 점, duplicated string fields cleanup은 later separate contract라는 점에 맞춰 동기화했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `make e2e-test`
- `git diff --check`
- `rg -n "reviewed_memory_planning_target_ref|planning_target_version|target_label|eligible_for_reviewed_memory_draft_planning_only|future_transition_target|readiness_target|reviewed_memory_unblock_contract|reviewed_memory_capability_status" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-planning-target-normalization-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - current payload는 planning-only meaning을 정확히 담고 있었지만, exact shared ref shape가 아직 payload에 materialize되지 않았습니다.
- 이번 라운드에서 해소한 리스크:
  - aggregate-level `reviewed_memory_planning_target_ref`가 shipped payload에 추가되면서 shared planning-only semantic source가 explicit해졌습니다.
  - 세 target field가 current payload에서 exact derived echo라는 점이 코드와 회귀 테스트로 함께 고정됐습니다.
- 여전히 남은 리스크:
  - duplicated string target fields는 compatibility echo로 아직 남아 있으므로, later cleanup timing과 제거 방식은 별도 contract로 닫아야 합니다.
  - reviewed-memory store / apply / emitted transition record / repeated-signal promotion / cross-session counting / user-level memory는 계속 later layer입니다.
