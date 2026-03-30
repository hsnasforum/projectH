# 2026-03-27 truthful-correction-surface-contract

## 목적

- 현재 구현 truth와 next-phase 설계 목표를 분리한 채, `corrected` / `rejected` content outcome을 언제 truthfully 기록할 수 있는지 최소 사용자 surface 계약을 고정합니다.
- 이번 라운드는 문서 작업만 다룹니다.
- approval rejection과 content rejection은 계속 분리합니다.

## 현재 구현 truth

- grounded-brief assistant message는 stable `artifact_id`와 `artifact_kind = grounded_brief`를 가집니다.
- 같은 artifact anchor는 assistant message, approval, write, feedback trace에 연결됩니다.
- original grounded-brief source message는 normalized `original_response_snapshot`을 가집니다.
- current content outcome truth는 최소 `corrected_outcome.outcome = accepted_as_is`뿐입니다.
- current approval friction truth는 최소 `approval_reason_record`뿐입니다.
  - `approval_reject -> explicit_rejection`
  - `approval_reissue -> path_change`
- 아직 구현되지 않은 것:
  - corrected text persistence
  - `corrected` content outcome
  - `rejected` content outcome
  - richer reject / reissue labels
  - review queue
  - user-level memory

## Truthful Surface Contract For `corrected`

### 필요한 명시적 사용자 행동

- 사용자가 실제 수정된 텍스트를 명시적으로 제출해야 합니다.
- inferred correction, retry, feedback, approval outcome만으로는 `corrected`를 기록하지 않습니다.

### 가장 작은 truthful surface

- grounded-brief response surface에 one multiline correction editor를 둡니다.
- editor는 current grounded-brief draft text로 미리 채웁니다.
- 같은 control에서 아래 세 경우를 모두 허용합니다.
  - 일부 문장만 편집
  - 전체 재작성
  - 외부에서 작성한 전체 수정본 붙여넣기

### 기록 규칙

- `corrected` outcome은 사용자가 그 edited text를 명시적으로 제출한 경우에만 기록합니다.
- correction source of truth는 여전히 original grounded-brief artifact/source-message surface여야 합니다.
- approval-based save는 별도 흐름으로 유지합니다.
- 즉, corrected text 제출과 note save approval은 연결될 수는 있지만 같은 행동으로 취급하지 않습니다.

## Truthful Surface Contract For `rejected`

### 필요한 명시적 사용자 행동

- 사용자가 grounded-brief content 자체를 거절한다는 explicit verdict를 남겨야 합니다.
- 아래는 `rejected`로 간주하지 않습니다.
  - approval reject
  - save를 하지 않음
  - retry 요청
  - feedback `incorrect`

### 가장 작은 truthful surface

- grounded-brief response surface에 approval controls와 분리된 content-verdict control이 필요합니다.
- 최소 contract는 dedicated `Reject content` action입니다.
- short reason note는 선택 사항으로 둘 수 있지만, `rejected` verdict 자체의 truthful 기록에 필수는 아닙니다.

### 기록 규칙

- `rejected` outcome은 explicit content-verdict action이 실행된 경우에만 기록합니다.
- source of truth는 original grounded-brief artifact/source-message surface여야 합니다.
- approval friction trace는 기존처럼 approval-linked reason surface에만 남깁니다.

## Minimum MVP Recommendation

### 이번 라운드의 결정

- 이번 라운드에서는 contract만 고정하고 제품 동작은 바꾸지 않습니다.
- 다음 실제 UI/flow 도입은 `corrected` surface를 먼저 두는 것이 맞습니다.
- `rejected` surface는 distinct content-verdict control을 설계할 때까지 나중으로 둡니다.

### 왜 `corrected`를 먼저 두는가

- 실제 수정 텍스트가 남기 때문에 가장 audit-friendly한 content artifact를 만들 수 있습니다.
- document-first MVP의 생산성과 가장 직접적으로 연결됩니다.
- approval reject나 no-save와 혼동될 가능성이 낮습니다.

### 왜 `rejected`는 나중인가

- explicit control이 없으면 approval friction, no-save, retry와 섞이기 쉽습니다.
- corrected surface 없이 reject만 먼저 도입하면 usable artifact보다 verdict만 늘어나 local-first productivity 대비 이득이 작습니다.

## 범위 경계

- 이 계약은 review queue를 요구하지 않습니다.
- 이 계약은 user-level memory를 요구하지 않습니다.
- 이 계약은 operator surface를 요구하지 않습니다.
- 이 계약은 separate artifact store를 요구하지 않습니다.
- 이 계약은 richer approval reason label 도입을 요구하지 않습니다.

## OPEN QUESTION

- corrected surface를 실제 구현할 때, correction submit과 optional save approval를 같은 response card 안에서 어떻게 분리 배치해야 혼동을 최소화할지 세부 UI 결정은 아직 남아 있습니다.
