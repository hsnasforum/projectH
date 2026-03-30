# 2026-03-28 reviewed-memory boundary defined contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-reviewed-memory-boundary-defined-contract.md`
- `work/3/28/2026-03-28-reviewed-memory-boundary-defined-contract.md`

## 사용 skill
- `mvp-scope`: current shipped aggregate/status surface와 next reviewed-memory boundary를 다시 섞지 않도록 범위를 좁혔습니다.
- `approval-flow-audit`: review acceptance, approval-backed save, historical adjunct, queue presence가 boundary basis처럼 읽히지 않도록 approval/review 경계를 다시 확인했습니다.
- `doc-sync`: fixed narrow reviewed scope 결정이 root docs와 `plandoc`에 같은 문구로 남도록 동기화했습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg` 결과만 기준으로 handoff 상태를 정리합니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 문서 라운드와 남은 리스크를 남깁니다.

## 변경 이유
- 직전 closeout까지 `reviewed_memory_precondition_status`와 precondition family는 고정됐지만, 그중 첫 precondition인 `reviewed_memory_boundary_defined`의 exact reviewed scope contract 자체는 아직 열려 있었습니다.
- 이 경계가 없으면 later reviewed-memory draft, rollback/disable/conflict/operator-audit, repeated-signal promotion, cross-session counting이 무엇을 기준으로 더 좁게 열려야 하는지 계속 모호했습니다.

## 핵심 변경
- `reviewed_memory_boundary_defined`를 one fixed narrow reviewed scope contract로 고정했습니다:
  - `same_session_exact_recurrence_aggregate_only`
  - first boundary는 small scope enum을 열지 않습니다.
- current shipped surfaces와 future boundary를 다시 분리했습니다:
  - `candidate_review_record`는 source-message reviewed-but-not-applied trace
  - `recurrence_aggregate_candidates`는 same-session grouping surface
  - `aggregate_promotion_marker`와 `reviewed_memory_precondition_status`는 blocked marker/status
  - future reviewed-memory boundary는 그 위의 later draft layer
- first future surface는 one read-only `reviewed_memory_boundary_draft` only로 권고했습니다.
- `future_transition_target = eligible_for_reviewed_memory_draft`는 그대로 유지하고, reviewed-memory store/apply, repeated-signal promotion, cross-session counting, user-level memory는 계속 later로 고정했습니다.

## 검증
- 실행:
  - `git diff --check`
  - `rg -n "reviewed_memory_boundary_defined|reviewed_memory_precondition_status|aggregate_promotion_marker|eligible_for_reviewed_memory_draft|reviewed scope|cross-session" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-reviewed-memory-boundary-defined-contract.md`
- 미실행:
  - `python3 -m py_compile ...`
  - `python3 -m unittest ...`
  - `make e2e-test`
- 사유:
  - 이번 라운드는 문서 작업만 수행했고 제품 코드는 변경하지 않았습니다.

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - current blocked-only precondition surface는 shipped 되었지만, `reviewed_memory_boundary_defined`가 정확히 어떤 fixed reviewed scope를 뜻하는지 아직 닫히지 않았습니다.
- 이번 라운드에서 해소한 리스크:
  - first reviewed-memory boundary를 `same_session_exact_recurrence_aggregate_only`로 고정해 same-session aggregate 위 later draft boundary가 어디까지를 가리키는지 정직하게 문서화했습니다.
  - small scope enum을 닫아 현재 MVP가 아직 구현하지 않은 broader scope choice/conflict semantics를 당겨오지 않도록 했습니다.
- 여전히 남은 리스크:
  - `reviewed_memory_boundary_draft` 자체는 아직 미구현입니다.
  - rollback / disable / conflict / operator-audit mechanics도 여전히 separate later machinery입니다.
  - cross-session counting은 local-store / stale-resolution / repair rules 없이는 계속 premature합니다.
