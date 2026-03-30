# 2026-03-28 reviewed-memory disable contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-reviewed-memory-disable-contract.md`
- `work/3/28/2026-03-28-reviewed-memory-disable-contract.md`

## 사용 skill
- `mvp-scope`: current same-session aggregate surface와 future disable-ready reviewed-memory layer를 다시 섞지 않도록 범위를 좁혔습니다.
- `approval-flow-audit`: review acceptance, approval-backed save, historical adjunct, queue presence가 disable basis처럼 읽히지 않도록 approval/review 경계를 다시 확인했습니다.
- `doc-sync`: disable contract 결정이 root docs와 `plandoc`에 같은 current-truth 문구로 남도록 동기화했습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg` 결과만 기준으로 handoff 상태를 정리합니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 문서 라운드와 남은 리스크를 남깁니다.

## 변경 이유
- 직전 closeout에서 `reviewed_memory_rollback_contract`는 shipped 되었지만 `disable_ready_reviewed_memory_effect`가 정확히 무엇을 뜻하는지, 무엇을 stop-apply target으로 삼아야 하는지가 아직 문서로 닫히지 않았습니다.
- 이 경계가 없으면 future reviewed-memory apply, rollback reversal, disable stop-apply의 차이가 흐려져 later state transition을 과장해서 해석할 위험이 남습니다.

## 핵심 변경
- `disable_ready_reviewed_memory_effect`를 one later applied reviewed-memory effect stop-apply contract로 고정했습니다.
- disable target은 `same_session_exact_recurrence_aggregate_only` scope 안의 future applied effect only로 정리했고, current `reviewed_memory_boundary_draft`와 current `reviewed_memory_rollback_contract`는 basis ref로 남기되 disable target으로 쓰지 않도록 고정했습니다.
- disable 이후에도 aggregate identity, supporting refs, boundary draft, rollback contract, operator-visible audit trace는 남고 later applied effect only가 future apply 관점에서 비활성화될 수 있다고 문서화했습니다.
- disable을 rollback reversal, conflict visibility, operator audit와 separate later machinery로 분리했고, `task_log`는 audit mirror일 뿐 canonical disable store가 아니라고 다시 못 박았습니다.
- next implementation slice는 one read-only `reviewed_memory_disable_contract` only로 추천했습니다.

## 검증
- 실행: `git diff --check`
- 실행: `rg -n "disable_ready_reviewed_memory_effect|reviewed_memory_rollback_contract|reviewed_memory_boundary_draft|reviewed_memory_precondition_status|aggregate_promotion_marker|same_session_exact_recurrence_aggregate_only|cross-session" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-reviewed-memory-disable-contract.md`
- 미실행: `python3 -m py_compile ...`
- 미실행: `python3 -m unittest ...`
- 미실행: `make e2e-test`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - rollback contract는 생겼지만 later reviewed-memory effect를 “삭제 없이 적용 중단”할 exact disable semantics가 아직 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - disable target이 current evidence traces나 current rollback contract가 아니라 one later applied reviewed-memory effect only라는 점을 문서로 고정했습니다.
  - disable 이후에도 무엇이 남아야 하는지와 `task_log`가 canonical disable store가 아니라는 점을 분리했습니다.
- 여전히 남은 리스크:
  - conflict-visible, operator-auditable precondition은 아직 separate exact contract가 더 필요합니다.
  - `reviewed_memory_disable_contract`를 실제 payload에 어떤 최소 shape로 materialize할지 구현은 아직 남아 있습니다.
  - reviewed-memory store/apply, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
