# 2026-03-29 reviewed-memory capability-basis source contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/NEXT_STEPS.md`
- `docs/TASK_BACKLOG.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-capability-basis-source-contract.md`

## 사용 skill
- `mvp-scope`: current shipped contract, next phase source layer, long-term north star를 다시 분리해 capability-source 범위를 좁게 고정했습니다.
- `approval-flow-audit`: approval-backed save, review acceptance, `task_log`가 capability-basis source로 오인되지 않도록 경계를 다시 확인했습니다.
- `doc-sync`: current serializer truth와 문서의 next-slice wording을 source-helper-first로 맞췄습니다.
- `release-check`: 실행한 검증과 미실행 검증을 정직하게 정리하기 위해 사용했습니다.
- `work-log-closeout`: 이번 라운드의 변경 파일, 검증, 남은 리스크를 `/work` 형식에 맞춰 기록했습니다.

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 current repo에 truthful `reviewed_memory_capability_basis` source가 still 없다는 점이었습니다.
- 이 상태에서 다음 구현을 바로 basis object나 `unblocked_all_required`로 열면 current contract chain, `candidate_review_record`, approval-backed save support, historical adjunct, `task_log` replay를 source처럼 잘못 재해석할 위험이 남아 있었습니다.
- 그래서 이번 라운드는 basis object 구현이 아니라, later basis object를 truthfully materialize할 exact source layer를 먼저 문서로 닫는 데 집중했습니다.

## 핵심 변경
- future exact source를 one additive internal aggregate-scoped helper family `reviewed_memory_capability_source_refs`로 고정했습니다.
- current blocked contract chain -> blocked trigger affordance -> future capability-basis source layer -> future `reviewed_memory_capability_basis` -> future `unblocked_all_required` -> future emitted transition record -> future reviewed-memory apply result 순서를 문서 전체에서 다시 분리했습니다.
- `candidate_review_record`, queue presence, approval-backed save alone, historical adjunct alone, `task_log` replay alone, current contract-object existence alone은 capability-basis source가 될 수 없다고 다시 고정했습니다.
- next slice recommendation을 `one exact capability-source helper implementation only`로 좁혔고, 기존 basis-object-first / materialization-first wording은 source-helper-first wording으로 정리했습니다.
- current shipped truth는 그대로 유지한다고 명시했습니다:
  - blocked aggregate affordance는 여전히 visible-but-disabled
  - `reviewed_memory_capability_basis`는 여전히 absent
  - `reviewed_memory_transition_record`는 여전히 absent
  - `reviewed_memory_capability_status.capability_outcome`는 여전히 `blocked_all_required`

## 검증
- `git diff --check`
- `rg -n "reviewed_memory_capability_basis|basis source|truthful later capability source|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record|검토 메모 적용 시작|candidate_review_record" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/web.py app/templates/index.html plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 남은 리스크
- 이번 라운드에서 해소한 리스크:
  - future `reviewed_memory_capability_basis` source가 무엇인지 미정인 상태는 문서로 닫았습니다.
  - next implementation이 current contract chain이나 support-only traces를 source처럼 오해할 여지는 줄였습니다.
- 여전히 남은 리스크:
  - `reviewed_memory_capability_source_refs`를 실제로 어떤 local helper family로 구현할지는 아직 미구현입니다.
  - source helper가 생긴 뒤 `reviewed_memory_capability_basis`를 바로 materialize할지, 한 라운드를 더 분리할지는 아직 열려 있습니다.
  - enabled aggregate card, note input, emitted transition record, reviewed-memory apply result, cross-session counting은 계속 later scope입니다.
