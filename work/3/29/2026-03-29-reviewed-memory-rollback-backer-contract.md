## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 `rollback_source_ref` resolver는 same exact aggregate / exact rollback contract / exact supporting refs에 묶인 unresolved 상태까지는 구현됐지만, 그 resolver가 나중에 무엇을 가리켜야 하는지는 아직 닫히지 않았습니다.
- 이 정의가 없으면 다음 구현이 current `reviewed_memory_rollback_contract`, support-only trace, 또는 `task_log` replay를 rollback backer처럼 잘못 읽을 위험이 남아 있었습니다.

## 핵심 변경
- exact real later local `rollback_source_ref` backer를 one internal local `reviewed_memory_reversible_effect_handle`로 고정했습니다.
- 이 future internal handle은 `same_session_exact_recurrence_aggregate_only` scope, exact aggregate/supporting refs, matching `boundary_source_ref`, matching `rollback_contract_ref`, `effect_target_kind = applied_reviewed_memory_effect`, `effect_capability = reversible_local_only`, `effect_stage = handle_defined_not_applied`를 갖는 최소 계약으로 정리했습니다.
- current `reviewed_memory_rollback_contract`는 여전히 contract-only, current `rollback_source_ref`는 여전히 exact-scope-validated but unresolved, future backer는 그 위의 actual local capability라는 층 분리를 root docs와 plandoc에 다시 고정했습니다.
- `candidate_review_record`, queue presence, approval-backed save, historical adjunct, `task_log` replay, contract object existence alone은 rollback backer가 될 수 없다는 점을 다시 명시했습니다.
- next slice는 basis object나 `unblocked_all_required`가 아니라 one real later local rollback-capability backer implementation only로 추천했고, 구체 target을 `reviewed_memory_reversible_effect_handle`로 좁혔습니다.

## 검증
- 실행: `git diff --check`
- 실행: `rg -n "rollback_source_ref|boundary_source_ref|reviewed_memory_rollback_contract|reviewed_memory_capability_source_refs|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record|candidate_review_record" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/web.py app/templates/index.html plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 남은 리스크
- current repo에는 still no real later local rollback-capability backer implementation이 없어서 `rollback_source_ref`는 계속 unresolved입니다.
- `boundary_source_ref`만 resolved된 current truth와 future rollback backer truth를 문서로는 분리했지만, actual local handle이 아직 없어 full source family, `reviewed_memory_capability_basis`, `unblocked_all_required`는 여전히 닫혀 있습니다.
- `reviewed_memory_reversible_effect_handle`를 first rollback-only scaffold로 둘지, later disable-capability와 일부 내부 family를 공유할지는 아직 open question입니다.
