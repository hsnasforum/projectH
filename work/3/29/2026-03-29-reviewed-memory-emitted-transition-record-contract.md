# 2026-03-29 reviewed-memory emitted-transition-record contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-emitted-transition-record-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-emitted-transition-record-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 shared-ref-only planning-target truth와 post-cleanup aftercare wording은 닫혔지만, already shipped `reviewed_memory_transition_audit_contract` 위에서 first emitted transition record를 어떤 exact contract로 열지 아직 정해지지 않았습니다.
- 이 경계가 없으면 later work가 canonical transition identity, append-only `task_log` mirror, reviewed-memory apply result를 한 번에 섞어 과장할 위험이 남아 있었습니다.

## 핵심 변경
- current shipped truth는 그대로 유지하면서, future first emitted-transition-record layer를 별도 contract로 고정했습니다.
- 결정은 `Option A`입니다:
  - current shipped `reviewed_memory_transition_audit_contract`는 계속 `contract_only_not_emitted`
  - first later surface는 one aggregate-level read-only `reviewed_memory_transition_record`
  - canonical transition identity는 `task_log`와 separate canonical layer로 남고, `task_log`는 mirror / appendix only로 유지됩니다
- future first shape는 아래로 고정했습니다:
  - `transition_record_version = first_reviewed_memory_transition_record_v1`
  - `canonical_transition_id`
  - `transition_action`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - `aggregate_identity_ref`
  - exact `supporting_source_message_refs`
  - exact `supporting_candidate_refs`
  - optional `supporting_review_refs`
  - explicit `operator_reason_or_note`
  - `record_stage = emitted_record_only_not_applied`
  - `task_log_mirror_relation = mirror_allowed_not_canonical`
  - local `emitted_at`
- 문서 전반에서 `transition-audit contract exists` / `transition record emitted` / `reviewed-memory apply result`를 separate three-layer contract로 다시 고정했습니다.

## 검증
- `git diff --check`
- `rg -n "emitted transition record|transition record|reviewed_memory_transition_audit_contract|canonical transition|task_log|blocked_all_required|unblocked_all_required|apply result" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-29-reviewed-memory-emitted-transition-record-contract.md plandoc/2026-03-29-reviewed-memory-post-cleanup-compatibility-note-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - current payload에는 exact transition-audit contract가 있지만, first emitted transition-record surface의 exact contract가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - canonical transition identity, `task_log` mirror, reviewed-memory apply result를 separate layer로 정리하는 first emitted-transition-record contract를 문서로 고정했습니다.
  - future first emitted surface를 one aggregate-level read-only canonical record로 좁혀, apply나 user-level memory와의 overloading을 막았습니다.
- 여전히 남은 리스크:
  - emitted transition record는 아직 미구현입니다.
  - `task_log` mirror를 first implementation round에서 mandatory로 둘지 optional로 둘지는 아직 open question입니다.
  - reviewed-memory apply, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
