# 2026-03-27 session-local-memory-signal-contract

## 목적

- current shipped explicit correction / reject / approval / save trace를 다시 설계하지 않으면서, 그 위에서 만들 수 있는 first `session_local` memory signal의 최소 계약을 고정합니다.
- current shipped contract, next implementation slice, future `durable_candidate`, future user-level memory를 분리합니다.
- 이번 라운드는 문서 작업만 다루며, 제품 코드와 current UI surface는 바꾸지 않습니다.

## 현재 구현 truth

- grounded-brief source message는 `artifact_id`, `source_message_id`, `original_response_snapshot`를 가집니다.
- explicit correction submit은 same source message에 `corrected_text`와 `corrected_outcome.outcome = corrected`를 기록합니다.
- explicit `내용 거절`은 same source message에 `corrected_outcome.outcome = rejected`와 fixed-label `content_reason_record`를 기록합니다.
- optional reject-note는 same source message의 existing `content_reason_record.reason_note`를 in-place update합니다.
- original-draft save와 corrected-save는 explicit save trace를 남기며, `save_content_source = original_draft | corrected_text`와 `source_message_id`를 approval/write surfaces에 노출합니다.
- approval reject / reissue는 approval-friction trace로만 기록되며, `approval_reason_record`는 approval-linked session messages / pending approvals / task-log detail에 남습니다.
- task-log는 append-only audit 축이며, current UI/session contract의 canonical content source-of-truth는 아닙니다.

## 첫 session-local memory signal 정의

- first `session_local` memory signal은 다음 뜻만 가집니다.
  - “현재 세션에서 이 grounded-brief artifact에 대해 어떤 explicit user action state가 남아 있는가”를 읽기 전용으로 요약한 working signal
- 이것은 다음을 뜻하지 않습니다.
  - 모델이 일반 선호를 학습했다
  - durable candidate가 이미 만들어졌다
  - user-level memory가 적용된다
  - future training artifact가 준비됐다

### 가장 작은 canonical unit

- canonical unit은 artifact-scoped이되 source-message-anchored입니다.
- 즉, key는 아래 두 축을 함께 씁니다.
  - `artifact_id`
  - `source_message_id`
- 이유:
  - current content state는 original grounded-brief source message에 붙습니다.
  - approval friction과 save trace도 같은 `artifact_id` / `source_message_id`로 연결됩니다.
  - session-wide aggregate부터 시작하면 approval friction, saved history, latest verdict를 너무 일찍 평평하게 섞게 됩니다.

## signal이 포함해야 하는 것

- first signal은 현재 persisted session state에서 truthfully recoverable 한 explicit trace만 요약합니다.

### 1. Content axis

- same source message의 latest `corrected_outcome`
- same source message에 current `corrected_text`가 있는지 여부
- same source message의 current `content_reason_record` when present

### 2. Approval axis

- same `artifact_id` / `source_message_id`에 연결되는 latest approval-linked `approval_reason_record` when present
- 이것은 approval reject / reissue happened를 content verdict와 섞지 않고 별도 축으로 보여 주기 위함입니다.

### 3. Save axis

- latest save linkage when present:
  - `save_content_source`
  - optional `approval_id`
  - optional `saved_note_path`
- saved file body 자체는 signal에 복사하지 않습니다.

## signal이 포함하지 않는 것

- inferred preference statement
- inferred category (`tone`, `format` 등)
- cross-artifact aggregation
- cross-session merge
- review status
- scope suggestion
- user-level memory application
- saved body copy
- approval preview body copy
- no-save / retry / feedback `incorrect`를 content reject로 바꾼 값

## layer separation

- first signal은 아래 세 층을 분리해야 합니다.
  - saved history
  - latest content verdict
  - latest corrected text state
- 예를 들어:
  - corrected-save note가 이미 저장돼 있어도 later `내용 거절`은 latest verdict만 바꿀 수 있습니다.
  - later correction submit은 latest corrected state를 다시 바꿀 수 있습니다.
  - saved body/path는 그와 별개로 prior explicit-save history로 남습니다.
- approval reject도 여기에 억지로 합치면 안 됩니다.
  - approval reject는 save-path friction 또는 approval friction
  - content reject는 content verdict

## canonical source of truth / projection contract

### Canonical source

- canonical source of truth는 current persisted session state입니다.
- 그 안에서도 역할이 나뉩니다.
  - original grounded-brief source message:
    - content axis canonical source
    - `original_response_snapshot`
    - `corrected_text`
    - `corrected_outcome`
    - `content_reason_record`
  - approval-linked session messages and pending approvals:
    - approval axis canonical source
    - `approval_reason_record`
  - saved response messages plus source-message save linkage:
    - save axis canonical source
    - `save_content_source`
    - `saved_note_path`
    - `approval_id`

### Projection

- `session_local_memory_signal` itself는 canonical record가 아니라 read-only projection입니다.
- projection은 아래 surface까지만 허용하는 것이 가장 작습니다.
  - serialized grounded-brief source message
  - 필요 시 same source message를 현재 response가 직접 가리킬 때의 response payload mirror
- session-wide aggregate summary는 first slice 범위 밖으로 두는 편이 맞습니다.

### Task-log role

- task-log는 audit / replay 보조축입니다.
- first signal slice에서는 task-log replay를 canonical source로 삼지 않습니다.
- 이유:
  - current UI/session semantics의 source-of-truth는 session message surfaces입니다.
  - task-log replay를 먼저 canonical화하면 superseded content state와 current state를 섞기 쉽습니다.
  - first slice는 smallest truthful projection이어야 합니다.

## current truthful limitation

- later correction submit이나 explicit save가 `rejected`를 supersede 하면 same source message의 `content_reason_record`는 clear됩니다.
- 따라서 superseded reject / reject-note가 task-log에는 남아도 first signal에서는 사라질 수 있습니다.
- 이것은 버그가 아니라 current small-slice boundary입니다.
  - first signal은 “current session working state” 요약
  - task-log는 “append-only audit history”

## first implementation slice 권고

- 최종 권고는 아래 1개입니다.
- **source-message 기반 read-only `session_local_memory_signal` projection field 추가**

### 왜 이 slice가 가장 작은가

- current shipped traces를 그대로 재사용합니다.
- separate memory store가 필요 없습니다.
- review queue나 durable candidate normalization이 필요 없습니다.
- UI를 넓힐 필요가 없습니다.
- session payload / response serialization과 focused service regression으로 바로 검증 가능합니다.

### first-slice shape 예시

- shape는 아래 정도면 충분합니다.
  - `signal_scope = session_local`
  - `artifact_id`
  - `source_message_id`
  - `content_signal`
    - `latest_corrected_outcome`
    - `has_corrected_text`
    - optional `content_reason_record`
  - `approval_signal`
    - optional `latest_approval_reason_record`
  - `save_signal`
    - optional `latest_save_content_source`
    - optional `latest_approval_id`
    - optional `latest_saved_note_path`

### why not durable candidate first

- single artifact signal은 아직 reusable statement가 아닙니다.
- current traces에는 review outcome, scope, rollback, explicit confirmation policy가 없습니다.
- approval friction과 content verdict를 그냥 합치면 category/statement가 왜곡됩니다.
- saved history, latest verdict, latest corrected text를 한 문장으로 평탄화하면 truthfulness가 무너집니다.

## OPEN QUESTION

1. first signal이 current state only로 충분한지, 아니면 superseded content reject까지 later replay helper로 끌어올 가치가 있는지는 다음 단계에서 다시 볼 수 있습니다.
2. first response-level mirror까지 같이 낼지, 아니면 source-message serialization에만 먼저 넣을지는 implementation slice에서 더 좁힐 수 있습니다.
