# 2026-03-27 reject-note-clear-contract

## 목적

- shipped `내용 거절` + optional reject-note surface를 다시 열지 않으면서, manual clear UX가 필요한지와 필요하다면 어떤 가장 작은 truthful contract가 맞는지 고정합니다.
- current shipped contract, next refinement candidate, long-term memory layer를 분리합니다.
- 이번 라운드는 문서 작업만 다루며, 제품 코드와 approval / corrected-save semantics는 바꾸지 않습니다.

## 현재 구현 truth

- `내용 거절`은 grounded-brief response card의 distinct content-verdict action으로 이미 shipped 상태입니다.
- same response-card `내용 판정` 구역에는 optional reject-note surface가 이미 있습니다.
- note submit은 non-empty text만 허용합니다.
- blank submit은 disabled 상태이며, 현재 구현은 blank submit을 clear로 재해석하지 않습니다.
- note update는 same source message의 existing `content_reason_record.reason_note`를 in-place update합니다.
- `content_reason_record.recorded_at`는 note update 시각으로 refresh됩니다.
- `corrected_outcome.recorded_at`는 reject verdict가 처음 기록된 시각을 계속 뜻합니다.
- later correction submit 또는 explicit save supersession이 latest outcome을 `rejected` 밖으로 옮기면 stale `content_reason_record`와 `reason_note`는 source message에서 함께 clear됩니다.

## 최종 권고

- `Option B`를 고정합니다.
- 즉, manual clear UX는 next refinement slice로 바로 올리지 않고, current disabled-blank-submit behavior를 더 유지합니다.

### 왜 지금은 미루는가

- current shipped reject-note surface는 이미 가장 작은 truthful augmentation을 만족합니다.
  - fixed-label `explicit_content_rejection` baseline은 note 없이도 완전합니다.
  - note는 optional 보강이므로, absence 자체가 usability bug는 아닙니다.
- manual clear는 value보다 semantic risk가 더 큽니다.
  - 같은 박스 안에 또 하나의 micro-action이 생기면 “메모 지우기”가 “거절 철회”처럼 오해될 수 있습니다.
  - blank submit을 clear로 재해석하면 current add/update-only contract와 audit semantics가 흐려집니다.
- local-first / approval-safe / audit-friendly 관점에서도 지금은 미루는 편이 맞습니다.
  - current source-message trace는 add/update와 later supersession clear만으로도 충분히 설명 가능합니다.
  - clear 전용 UX를 열려면 별도 helper copy, separate event, and-browser regression까지 같이 늘어나므로 response-card surface가 불필요하게 넓어집니다.

## 미래에 manual clear를 연다면 무엇을 지우는가

- clear 대상은 `reason_note`뿐입니다.
- clear는 `corrected_outcome.outcome = rejected`를 지우지 않습니다.
- clear는 fixed-label `explicit_content_rejection` baseline을 지우지 않습니다.
- clear는 `content_reason_record` 전체를 삭제하지 않습니다.
- 즉, reject verdict와 optional note는 다른 층입니다.
  - verdict는 그대로 유지
  - label baseline도 그대로 유지
  - optional `reason_note` field만 제거

## 미래에 manual clear를 연다면 가장 작은 truthful UX

- 위치:
  - same response-card `내용 판정` box 안
  - approval surface 밖
  - correction editor / corrected-save bridge와 분리
- 형태:
  - existing note가 있을 때만 보이는 tiny secondary action 1개
  - 예: `메모 지우기`
- 금지:
  - blank submit을 clear 수단으로 재해석하지 않기
  - modal / panel / workspace로 확장하지 않기
  - reject verdict revoke action처럼 보이게 만들지 않기
- confirmation:
  - first clear slice에서는 별도 modal confirm 없이 inline helper copy 정도로 끝내는 편이 가장 작습니다.

## Trace / Task-Log Contract

### Source Of Truth

- source of truth는 계속 original grounded-brief source message입니다.
- future manual clear가 생겨도 separate note-clear store를 만들지 않습니다.

### Record Mutation

- clear 시 같은 `content_reason_record`를 유지합니다.
- mutation target은 optional field only입니다:
  - remove `content_reason_record.reason_note`
- empty string 보존보다 field removal이 더 truthful합니다.
  - “현재 note가 없다”를 더 명확히 표현하기 때문입니다.
  - current shipped add/update contract도 non-empty text만 허용하므로 empty string persistence와 잘 맞지 않습니다.

### Timestamp Rule

- clear 시 `content_reason_record.recorded_at`는 clear 시점으로 refresh하는 쪽을 고정합니다.
- `corrected_outcome.recorded_at`는 그대로 둡니다.
  - 이 필드는 reject verdict가 처음 기록된 시각이기 때문입니다.

### Task-Log Rule

- existing `content_reason_note_recorded`를 재사용하지 않습니다.
- future manual clear가 생기면 별도 content-linked clear event를 둡니다.
  - 예: `content_reason_note_cleared`
- minimum detail은 아래면 충분합니다.
  - `artifact_id`
  - `source_message_id`
  - `reason_scope = content_reject`
  - `reason_label = explicit_content_rejection`
  - cleared note linkage or latest cleared payload indicator

### Stale-Clearing Relationship

- future manual clear와 existing stale-clearing rule은 서로 다른 층입니다.
- manual clear:
  - latest outcome이 계속 `rejected`인 상태에서 optional note만 제거
- stale clear on later correction/save:
  - latest outcome이 `rejected` 밖으로 이동하면서 `content_reason_record` 전체와 note를 source message에서 제거
- 두 경로를 섞지 말아야 합니다.

## 범위 경계

- 이번 계약은 shipped reject-note semantics를 바꾸지 않습니다.
- 이번 계약은 approval reject / no-save / retry / feedback `incorrect`를 content reject로 재해석하지 않습니다.
- 이번 계약은 corrected-save semantics를 다시 열지 않습니다.
- 이번 계약은 richer reject label taxonomy를 열지 않습니다.
- 이번 계약은 review queue, user-level memory, operator surface를 요구하지 않습니다.

## OPEN QUESTION

1. operator usage가 더 쌓였을 때도 manual clear가 실제로 필요한지, 아니면 later correction/save supersession만으로 충분한지 아직 추가 관찰이 필요합니다.
2. 만약 future clear가 필요해진다면, inline helper copy만으로 충분한지 아니면 tiny one-step confirm이 필요한지는 implementation slice에서 다시 자를 수 있습니다.
