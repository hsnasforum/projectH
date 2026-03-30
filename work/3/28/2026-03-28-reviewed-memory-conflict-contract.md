# 2026-03-28 reviewed-memory conflict contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-reviewed-memory-conflict-contract.md`
- `work/3/28/2026-03-28-reviewed-memory-conflict-contract.md`

## 사용 skill
- `mvp-scope`: same-session aggregate 위의 future conflict-visible layer를 current shipped rollback/disable surface와 섞지 않도록 범위를 다시 좁혔습니다.
- `approval-flow-audit`: review acceptance, approval-backed save, historical adjunct, queue presence가 conflict object나 conflict basis처럼 읽히지 않도록 approval/review 경계를 다시 확인했습니다.
- `doc-sync`: conflict contract 결정이 root docs와 `plandoc`에 같은 current-truth 문구로 남도록 동기화했습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg` 결과만 기준으로 handoff 상태를 정리합니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 문서 라운드와 남은 리스크를 남깁니다.

## 변경 이유
- 직전 closeout에서 `reviewed_memory_disable_contract`까지는 shipped 되었지만 `conflict_visible_reviewed_memory_scope`가 정확히 무엇을 visible target으로 삼아야 하는지, 무엇을 자동으로 하지 말아야 하는지가 아직 문서로 닫히지 않았습니다.
- 이 경계가 없으면 later reviewed-memory apply, disable stop-apply, rollback reversal 위에서 어떤 competing reviewed target을 operator에게 보여야 하는지가 계속 모호하게 남습니다.

## 핵심 변경
- `conflict_visible_reviewed_memory_scope`를 one reviewed scope 안에서 competing reviewed-memory targets를 operator가 later apply 전에 read-only로 볼 수 있어야 하는 contract로 고정했습니다.
- first conflict-visible scope는 `same_session_exact_recurrence_aggregate_only`로 고정했고, first conflict categories는 `future_reviewed_memory_candidate_draft_vs_applied_effect`와 `future_applied_reviewed_memory_effect_vs_applied_effect` 두 개만 허용하도록 문서화했습니다.
- current `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`는 basis ref 또는 neighboring contract로 남고 conflict object 자체는 아니라고 다시 못 박았습니다.
- conflict visibility는 auto-resolve, auto-disable, auto-rollback, auto-apply를 포함하지 않으며, current append-only `task_log`는 audit mirror일 뿐 canonical conflict store가 아니라고 고정했습니다.
- next implementation slice는 one read-only `reviewed_memory_conflict_contract` only로 추천했습니다.

## 검증
- 실행: `git diff --check`
- 실행: `rg -n "conflict_visible_reviewed_memory_scope|reviewed_memory_disable_contract|reviewed_memory_rollback_contract|reviewed_memory_boundary_draft|reviewed_memory_precondition_status|aggregate_promotion_marker|same_session_exact_recurrence_aggregate_only|cross-session" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-reviewed-memory-conflict-contract.md`
- 미실행: `python3 -m py_compile ...`
- 미실행: `python3 -m unittest ...`
- 미실행: `make e2e-test`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - boundary/rollback/disable contract는 생겼지만 same reviewed scope 안에서 무엇을 conflict로 보여야 하는지는 아직 exact contract가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - first conflict-visible scope와 first conflict categories를 fixed narrow contract로 문서화했습니다.
  - conflict visibility가 resolver, disable, rollback, apply를 대신하지 않는다는 점과 `task_log`가 canonical conflict store가 아니라는 점을 분리했습니다.
- 여전히 남은 리스크:
  - `operator_auditable_reviewed_memory_transition`는 아직 separate exact contract가 더 필요합니다.
  - `reviewed_memory_conflict_contract`를 실제 payload에 어떤 최소 shape로 materialize할지 구현은 아직 남아 있습니다.
  - reviewed-memory store/apply, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
