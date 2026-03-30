# 2026-03-27 reject-note-surface-contract

## 목적

- shipped fixed-label `내용 거절` baseline을 다시 열지 않으면서, optional `reason_note` input surface를 어디까지 허용할지 최소 계약으로 고정합니다.
- current shipped contract, next reject-note target, long-term memory layer를 분리합니다.
- 이번 라운드는 문서 작업만 다루며, 제품 코드와 current approval / corrected-save semantics는 바꾸지 않습니다.

## 현재 구현 truth

- grounded-brief response card에는 explicit `내용 거절` action이 이미 있습니다.
- 이 action은 approval surface 바깥의 content-verdict control입니다.
- 실행 즉시 original grounded-brief source message에 아래가 기록됩니다:
  - `corrected_outcome.outcome = rejected`
  - `artifact_id`
  - `source_message_id`
  - `recorded_at`
- 같은 source message에는 fixed-label `content_reason_record`도 기록됩니다:
  - `reason_scope = content_reject`
  - `reason_label = explicit_content_rejection`
- `reason_note`를 입력하는 UI surface는 아직 없습니다.
- current implementation에서는 latest outcome이 `rejected`에서 `corrected`나 save-driven outcome으로 바뀌면 stale `content_reason_record`가 source message에서 사라집니다.

## 고정한 다음 계약

### 1. Minimum Reject-Note UX

- reject-note는 `내용 거절`의 선행 조건이 아닙니다.
- first truthful note surface는 아래로 고정합니다:
  - 위치: 같은 grounded-brief response card의 `내용 판정` 구역
  - 형태: 짧은 inline textarea 1개 + explicit secondary submit action 1개
  - 범위: approval box 바깥, correction editor 바깥
- note surface는 아래 경우에만 보여 주는 것이 맞습니다:
  - `내용 거절` 직후 그 same source message의 latest outcome이 `rejected`가 되었을 때
  - 세션을 다시 열었을 때도 same source message의 latest outcome이 여전히 `rejected`일 때
- 즉, “이미 `rejected`인 상태에서만 편집 가능”이 가장 작은 truthful contract입니다.
- note surface는 correction submit, corrected-save bridge, approval reject와 시각적으로 분리되어야 합니다.

### 2. Fixed-Label Baseline Relationship

- `내용 거절`만 눌러도 지금과 동일하게 fixed-label `explicit_content_rejection`은 즉시 기록됩니다.
- optional note는 그 fixed label을 대체하지 않고, 같은 reject verdict를 보강하는 supplemental field입니다.
- note가 없어도 reject verdict는 이미 truthful합니다.
- 따라서 first reject-note slice는 “reject를 더 잘 설명하는 보강”이지, “reject를 완성하는 필수 단계”가 아닙니다.
- later correction submit이나 explicit save가 latest verdict를 supersede 하면, optional note도 그 stale reject state와 함께 source message에서 사라져야 합니다.

### 3. Trace Contract

- `content_reason_record.reason_note`는 아래 경우에만 생깁니다:
  - latest `corrected_outcome.outcome`이 같은 source message에서 여전히 `rejected`
  - user가 response-card reject-note surface에서 explicit submit을 실행
- note submit은 새 reject record를 만들지 않습니다.
- note submit은 same source message의 existing `content_reason_record`를 in-place update합니다:
  - `reason_scope = content_reject`
  - `reason_label = explicit_content_rejection`
  - `reason_note = <user text>`
  - `recorded_at = <latest note update time>`
- `corrected_outcome.recorded_at`는 reject verdict가 처음 기록된 시각을 계속 뜻합니다.
- `content_reason_record.recorded_at`는 latest reason payload가 기록된 시각으로 refresh되는 것이 가장 작은 truthful contract입니다.
- later correction submit, explicit original-draft save, corrected-save approval로 latest outcome이 `rejected`에서 벗어나면:
  - source message의 stale `content_reason_record`와 `reason_note`는 함께 clear
  - append-only audit log는 prior reject / note events를 그대로 유지

### 4. Audit Contract

- initial `내용 거절`은 current `content_verdict_recorded` + `corrected_outcome_recorded` trace를 그대로 유지합니다.
- later optional note submit은 별도 content-linked event 1개를 추가하는 것이 가장 작습니다.
  - 예: `content_reason_note_recorded`
- 이 event detail은 아래면 충분합니다:
  - `message_id`
  - `artifact_id`
  - `artifact_kind`
  - `source_message_id`
  - `content_verdict = rejected`
  - nested `content_reason_record`
- approval-linked `approval_reason_record`나 `approval_rejected` 이벤트는 reject-note audit source가 아닙니다.

## MVP 권고

- optional reject-note UX는 next implementation slice로 올리는 것을 권고합니다.
- 이유는 아래와 같습니다.
  - shipped fixed-label reject path와 browser smoke가 이미 안정돼 있어, 다음으로 가장 작은 truthful refinement가 note 하나뿐입니다.
  - response card 내부의 작은 inline surface로 끝낼 수 있어 local-first / audit-friendly / approval-safe 성격을 유지합니다.
  - approval box를 건드리지 않으므로 approval reject와 content verdict를 계속 분리할 수 있습니다.
  - source message의 existing `content_reason_record`만 update하면 되므로 separate store나 broad migration이 필요 없습니다.
- 다만 richer reject labels는 아직 이릅니다.
  - first note slice는 fixed-label baseline + optional free-text note까지만 다루고,
  - label taxonomy expansion은 그 다음으로 미룹니다.

## 범위 경계

- 이번 계약은 shipped `내용 거절` semantics를 바꾸지 않습니다.
- 이번 계약은 approval reject, no-save, retry, feedback `incorrect`를 content reject로 재해석하지 않습니다.
- 이번 계약은 corrected-save bridge semantics를 다시 열지 않습니다.
- 이번 계약은 review queue, user-level memory, operator surface를 요구하지 않습니다.

## OPEN QUESTION

1. same rejected state 안에서 note를 빈 값으로 다시 제출했을 때, no-op로 볼지 explicit clear로 볼지는 아직 열려 있습니다.
2. first note slice에서 textarea를 항상 펼쳐 둘지, `메모 추가` 같은 작은 secondary affordance 뒤에 열지 여부는 구현 시점의 UI restraint 판단으로 남습니다.
3. note submit 직후 dedicated browser smoke를 바로 추가할지, focused unittest로 먼저 고정한 뒤 다음 라운드에 E2E로 올릴지는 구현 라운드 범위에 따라 다시 자를 수 있습니다.
