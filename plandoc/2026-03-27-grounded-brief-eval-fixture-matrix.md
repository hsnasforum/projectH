# 2026-03-27 Grounded Brief Eval Fixture Matrix

## 목적

이 문서는 지금까지 고정한 `grounded brief` 메모리 설계를 실제로 평가 가능한 `workflow-grade eval fixture matrix` 수준으로 정리한 follow-up 메모입니다.

- 현재 shipped contract를 바꾸지 않습니다
- 새로운 메모리 정책을 추가로 넓히지 않습니다
- eval-ready artifact가 되기 위한 trace contract와 fixture family만 고정합니다

## 단계 구분

### Current Shipped Contract
- 로컬 퍼스트 문서 비서 웹 MVP
- 파일 요약 / 문서 검색 / 일반 채팅
- evidence / source / summary chunk 표시
- 승인 기반 저장과 reissue
- feedback 저장

### Future Placeholder
- `grounded brief` artifact identity
- correction / approval / preference memory
- review queue / reviewed scope / rollback trace
- workflow-grade eval fixture matrix

### Future Implementation Target
- memory trace가 실제로 생긴 뒤의 service fixture
- trace validation용 unit helper
- review / rollback UI가 생긴 뒤의 e2e

원칙:
- 현재 gate와 future placeholder를 섞지 않습니다
- user-level memory는 여전히 future target이며, 이 문서도 그 구현을 전제하지 않습니다

## Eval Axis Separation

반드시 아래 축을 분리합니다.

1. content-quality correction reuse
2. approval friction reduction
3. scope selection safety
4. reviewability / rollbackability
5. trace completeness

원칙:
- approval-backed save는 content-quality 개선으로 집계하지 않습니다
- correction reuse와 approval friction 감소는 같은 artifact를 보더라도 다른 축으로 남깁니다
- reviewed memory와 user-level memory를 같은 축으로 취급하지 않습니다

## Eval-Ready Artifact Trace Contract

### 1. Core Chain

어떤 fixture family든 공통으로 필요한 core chain은 아래입니다.

- artifact record
  - `artifact_id`
  - `artifact_kind`
  - `session_id`
  - `assistant_message_id`
  - `created_at`
- original response snapshot
  - draft text or markdown
  - source paths
  - response origin
  - summary chunks snapshot
  - evidence snapshot
- evidence / source trace
  - source path or equivalent source reference
  - snippet / label or equivalent evidence payload
  - original response snapshot과 연결 가능한 reference
- corrected or accepted outcome
  - `accepted_as_is` 또는 `corrected` 또는 `rejected`
  - corrected text if present

원칙:
- 위 core chain 중 하나라도 빠지면 그 artifact는 workflow-grade eval matrix 기준의 `eval-ready artifact`가 아닙니다
- 현재 구현에는 이 chain 전체가 아직 없습니다
- 현재 구현은 message-level raw trace만 제공합니다

### 2. Family-Specific Extension Rules

각 fixture family는 core chain 위에 아래 extension을 더 요구합니다.

- correction reuse:
  - `correction` scope reason record
- approval friction:
  - approval trail
  - approval reject / reissue trace when present
- reviewed vs unreviewed trace:
  - review record
- scope suggestion safety:
  - review record
  - `proposed_scope`
  - `scope_candidates_considered`
  - `scope_suggestion_reason`
- rollback stop-apply:
  - review record
  - rollback record
  - later artifact non-application trace
- conflict / defer trace:
  - review record
  - `conflict_candidate_ids` or equivalent resolution trace
- explicit confirmation vs approval-backed save support:
  - `has_explicit_confirmation`
  - `supporting_approval_ids` if present

원칙:
- family-specific extension이 없으면, 그 artifact는 다른 family에는 쓸 수 있어도 해당 family fixture에는 쓸 수 없습니다

### 3. Current Raw Trace Baseline

현재 구현이 이미 제공하는 raw trace는 아래입니다.

- session message의 `message_id`
- message-level `evidence`
- message-level `summary_chunks`
- message-level `saved_note_path`
- message-level `note_preview`
- message-level `feedback.label` / `feedback.reason`
- task log의 `approval_requested`
- task log의 `approval_granted`
- task log의 `approval_rejected`
- task log의 `approval_reissued`
- task log의 `write_note`

원칙:
- 이 raw trace는 future eval fixture의 출발점이지만, 아직 artifact-level eval-ready chain은 아닙니다

## Fixture Family Matrix

### `GB-EVAL-CR-01` `correction_reuse`

- Scenario:
  - 같은 사용자 패턴이 다시 나타났을 때 같은 correction reason이 줄어드는지 봅니다
- Required input conditions:
  - 관련 artifact 최소 2개
  - prior correction trace
  - later comparison artifact
- Required trace:
  - core chain
  - `correction` scope reason record
- Expected result:
  - 같은 correction reason 반복이 줄거나 later edit 규모가 줄어야 합니다
- Not implemented today:
  - artifact identity
  - corrected outcome store
  - cross-artifact fixture harness
- Future target levels:
  - manual inspection placeholder now
  - service fixture first
  - unit helper for reason-count comparison
  - e2e later only if memory UI exists

### `GB-EVAL-AF-01` `approval_friction`

- Scenario:
  - path / filename 선호가 반복될 때 reject 또는 reissue friction이 줄어드는지 봅니다
- Required input conditions:
  - save-flow artifact
  - approval activity
  - repeated path or filename pattern
- Required trace:
  - core chain
  - approval trail
  - reject / reissue reason trace when present
- Expected result:
  - `approval_reissue` 또는 reject friction이 줄어들어야 하며, approval gate 자체는 유지되어야 합니다
- Not implemented today:
  - normalized reject / reissue reason store
  - artifact-linked approval fixture harness
- Future target levels:
  - manual inspection placeholder now
  - service fixture first
  - unit helper for approval-friction counts
  - e2e later around approval UI

### `GB-EVAL-RU-01` `reviewed_unreviewed_trace`

- Scenario:
  - reviewed candidate와 unreviewed candidate가 trace에서 섞이지 않는지 봅니다
- Required input conditions:
  - comparable candidate set
  - at least one reviewed path
  - at least one unreviewed path
- Required trace:
  - core chain
  - review record
  - candidate linkage to source artifacts
- Expected result:
  - reviewed entry는 reviewed로 남고
  - unreviewed candidate는 proposal 상태로 남아야 합니다
- Not implemented today:
  - review queue
  - reviewed-memory store
- Future target levels:
  - manual inspection placeholder now
  - service fixture first
  - unit helper for eligibility checks
  - e2e later when review UI exists

### `GB-EVAL-SC-01` `scope_suggestion_safety`

- Scenario:
  - 여러 scope 후보가 맞을 때도 conservative suggested scope가 기본값으로 유지되는지 봅니다
- Required input conditions:
  - multiple matching scope candidates
  - recorded scope suggestion fields
- Required trace:
  - core chain
  - review record
  - `proposed_scope`
  - `scope_candidates_considered`
  - `scope_suggestion_reason`
- Expected result:
  - 기본 순서는 `workflow_type -> path_family -> document_type -> global`
  - broader suggestion에는 justification이 남아야 합니다
- Not implemented today:
  - scope suggestion engine
  - review record store
- Future target levels:
  - manual inspection placeholder now
  - service fixture first
  - unit helper for scope-order validation
  - e2e later when review UI exposes scope choice

### `GB-EVAL-RB-01` `rollback_stop_apply`

- Scenario:
  - rollback 또는 disable 뒤에 같은 reviewed scope에서 preference 적용이 멈추는지 봅니다
- Required input conditions:
  - reviewed candidate
  - rollback or disable event
  - later artifact in the same reviewed scope
- Required trace:
  - core chain
  - review record
  - rollback record
  - later non-application trace
- Expected result:
  - later artifact에서 해당 memory가 더 이상 적용되지 않아야 합니다
- Not implemented today:
  - rollback record
  - reviewed-memory application layer
- Future target levels:
  - manual inspection placeholder now
  - service fixture first
  - unit helper for stop-apply filtering
  - e2e later when rollback UI exists

### `GB-EVAL-CD-01` `conflict_defer_trace`

- Scenario:
  - conflict 또는 defer 상태의 candidate가 조용히 사라지지 않는지 봅니다
- Required input conditions:
  - same-category conflict or defer path
  - resolution or defer state
- Required trace:
  - core chain
  - review record
  - `conflict_candidate_ids` or equivalent resolution trace
- Expected result:
  - deferred / rejected / edited path가 구분되고
  - silent overwrite가 없어야 합니다
- Not implemented today:
  - conflict queue
  - defer-resolution surface
- Future target levels:
  - manual inspection placeholder now
  - service fixture first
  - unit helper for conflict eligibility and resolution checks
  - e2e later when review UI exists

### `GB-EVAL-AS-01` `explicit_vs_save_support`

- Scenario:
  - explicit confirmation과 approval-backed save support가 구분되는지 봅니다
- Required input conditions:
  - one explicit-confirmation path
  - one approval-backed-save-only path
- Required trace:
  - core chain
  - `has_explicit_confirmation`
  - `supporting_approval_ids` if present
  - related approval trail
- Expected result:
  - explicit confirmation이 더 강한 신호로 남아야 합니다
  - approval-backed save는 supporting evidence로만 남아야 합니다
  - content-quality axis와 approval-friction axis는 계속 분리되어야 합니다
- Not implemented today:
  - candidate review store
  - support-distinction fixture harness
- Future target levels:
  - manual inspection placeholder now
  - service fixture first
  - unit helper for support classification
  - e2e later only if UI exposes both support paths

## 지금 확정하지 않는 것

- category별 recurrence tuning
- approval-backed save의 category별 세부 가중치 튜닝
- actual review queue implementation
- actual rollback UI
- first operator surface
- model training or personalization pipeline

## OPEN QUESTION

1. 기본 recurrence rule을 모든 category에 대해 계속 같게 둘지, family별로 다르게 둘지?
2. baseline 이후 category별로 approval-backed save 가중치를 더 세분화해야 하는지?
3. 일부 repository-shaped workflow에서 `path_family`를 `workflow_type`보다 먼저 제안해야 할 예외가 필요한지?
4. review / rollback UI가 생긴 뒤 어떤 fixture family까지 e2e로 올릴지 어디서 끊을지?
