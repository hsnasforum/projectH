# 2026-03-27 rejected-content-verdict-contract

## 목적

- content-level `rejected`를 truthfully 기록하려면 어떤 explicit user control이 필요한지 최소 계약을 고정합니다.
- current shipped contract와 next implementation slice를 분리합니다.
- 이번 라운드는 문서 작업만 다루며, 제품 코드나 current corrected-save semantics는 바꾸지 않습니다.

## 현재 구현 truth

- grounded-brief response card에는 `수정본 기록`과 `이 수정본으로 저장 요청`이 있습니다.
- `수정본 기록`은 original grounded-brief source message에 `corrected_text`와 `corrected_outcome.outcome = corrected`를 기록합니다.
- corrected-save bridge action은 recorded `corrected_text`만 approval save target으로 올립니다.
- approval surface의 reject / reissue는 approval-friction trace일 뿐, content verdict가 아닙니다.
- 현재 UI와 코드에는 “이 답변 내용 자체를 거절한다”는 distinct control이 없습니다.
- 따라서 지금은 `rejected`를 truthfully 기록할 수 없습니다.

## 고정한 다음 계약

### 1. Minimum Content-Verdict Control

- `rejected`는 grounded-brief response card에서만 시작하는 distinct content-verdict action으로 기록합니다.
- 첫 control은 one-click utility action이면 충분합니다.
  - 예: `내용 거절`
- 이 action은 아래와 반드시 분리됩니다.
  - `수정본 기록`
  - `이 수정본으로 저장 요청`
  - approval surface의 approve / reject / reissue
- 이 action은 save approval를 만들거나 취소하지 않습니다.
- 이 action은 local session / trace에 content verdict를 바로 기록하는 explicit user action입니다.

### 2. 왜 approval reject와 분리해야 하는가

- approval reject는 pending save approval에 대한 friction signal입니다.
- content reject는 grounded-brief 내용 자체에 대한 verdict입니다.
- 두 신호는 source surface도 다릅니다.
  - approval reject: approval surface
  - content reject: response-card content surface
- 아래는 모두 content-level `rejected`로 승격하면 안 됩니다.
  - approval reject
  - no-save
  - retry
  - feedback `incorrect`

### 3. Source Of Truth And Trace Contract

- source of truth는 계속 original grounded-brief source message입니다.
- separate artifact store나 reject-only store는 첫 slice에서 추가하지 않습니다.
- 가장 작은 additive 계약은 기존 content-outcome envelope를 재사용하는 것입니다.
  - `corrected_outcome.outcome = accepted_as_is | corrected | rejected`
  - `recorded_at`
  - `artifact_id`
  - `source_message_id`
- reject-only path에서는 아래 필드는 기본적으로 비어 있어야 합니다.
  - `approval_id`
  - `saved_note_path`
- response/session serialization은 같은 source message에서 이 verdict를 다시 노출할 수 있습니다.
- approval payload, pending approval, approval reject trace는 content verdict source of truth가 아닙니다.

### 4. Reject Reason Contract

- first slice에서 user-entered reject reason은 필수가 아닙니다.
- 다만 explicit `내용 거절` action 자체가 reason label 하나를 truthfully 고정할 수 있습니다.
  - `reason_scope = content_reject`
  - `reason_label = explicit_content_rejection`
  - `reason_note`는 optional
- 첫 slice에서는 optional note UI를 강제하지 않습니다.
- approval reject labels는 재사용하지 않습니다.
  - `approval_reject / explicit_rejection`은 pending approval 취소를 뜻할 뿐, content verdict를 뜻하지 않기 때문입니다.

### 5. Audit Contract

- content verdict audit은 approval-linked trace가 아니라 content-linked trace여야 합니다.
- 첫 slice에서는 기존 content-outcome logging path를 재사용해도 충분합니다.
  - 핵심은 audit detail이 `outcome = rejected`, `artifact_id`, `source_message_id`, 그리고 위 reject reason fields를 같이 남기는 것입니다.
- approval-side `approval_rejected` 이벤트를 content verdict audit으로 재해석하면 안 됩니다.

## MVP 권고

- `rejected` control은 next implementation slice로 바로 올리는 것을 권고합니다.
- 이유는 아래와 같습니다.
  - corrected surface와 corrected-save bridge contract가 이미 고정되어 있어, 다음으로 비어 있는 truthful content axis가 `rejected` 하나뿐입니다.
  - 이 slice는 response card에 작은 explicit action 1개를 추가하는 수준으로 끝낼 수 있습니다.
  - save approval를 건드리지 않으므로 approval-safe합니다.
  - source-message anchor와 local audit trail을 그대로 재사용하므로 auditable합니다.
  - approval reject와 semantic surface를 분리하면 later review/memory 설계도 덜 헷갈립니다.

## 범위 경계

- 이번 계약은 current shipped behavior를 `rejected` 지원 상태처럼 설명하지 않습니다.
- 이번 계약은 corrected-save semantics를 다시 열지 않습니다.
- 이번 계약은 review queue, user-level memory, operator surface를 요구하지 않습니다.
- 이번 계약은 richer reject taxonomy나 required note UX를 먼저 요구하지 않습니다.

## OPEN QUESTION

1. first rejected slice에서 optional `reason_note` 입력을 바로 둘지, action-only로 먼저 시작할지는 여전히 선택지로 남습니다.
2. later explicit correction이나 accepted-as-is save가 같은 source message의 `rejected` verdict를 덮을 때, source message에는 latest verdict만 남기고 audit log가 history를 보존하는 현재 패턴을 그대로 유지할지 추가 확인이 필요합니다.
