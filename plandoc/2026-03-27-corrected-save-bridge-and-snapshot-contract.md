# 2026-03-27 corrected-save-bridge-and-snapshot-contract

## 목적

- current shipped truth와 future corrected-save target을 분리한 채, bridge action과 immutable approval snapshot 계약을 최소 범위로 고정합니다.
- 이번 라운드는 문서 작업만 다룹니다.
- corrected-save approval를 이미 구현된 것처럼 설명하지 않습니다.

## 현재 구현 truth

- grounded-brief response surface에는 correction editor가 있습니다.
- explicit correction submit은 original grounded-brief source message에 `corrected_text`와 `corrected_outcome.outcome = corrected`를 기록합니다.
- current save approval는 여전히 original draft 기준입니다.
- current shipped save path는 `save_content_source = original_draft`를 approval/write trace에 노출합니다.
- current pending approval preview와 write body는 approval 발급 시점에 캡처된 `note_text` snapshot을 따릅니다.
- correction submit은 이미 발급된 pending approval를 바꾸지 않습니다.

## 고정한 다음 계약

### 1. Explicit Bridge Action

- future corrected-save는 response card의 content-edit area에서 시작하는 별도 bridge action으로만 들어갑니다.
- action copy는 approval가 아니라 save-request language여야 합니다.
  - 예: `이 수정본으로 저장 요청`
- 이 action은 `수정본 기록`과 같은 버튼이 아니어야 합니다.
- 이 action은 approve/reject/reissue controls도 아닙니다.
- response card는 save target selection surface를 유지하고, approval surface는 risky write review surface를 유지합니다.

### 2. Bridge Input Rule

- future bridge action은 unsaved editor state를 직접 approval로 올리면 안 됩니다.
- bridge action은 original grounded-brief source message에 이미 기록된 `corrected_text`를 읽어야 합니다.
- 즉 최소 truthful 순서는 아래와 같습니다.
  - `수정본 기록`
  - 필요 시 다시 편집
  - `이 수정본으로 저장 요청`
- 이 규칙을 고정하면 correction submit과 save request가 계속 분리되고, audit 해석도 단순해집니다.

### 3. Immutable Approval Snapshot

- corrected-save bridge action이 눌린 시점의 recorded `corrected_text`로 fresh approval object를 만듭니다.
- 그 approval object의 preview와 internal write body(`note_text`)는 같은 request-time snapshot에서 생성되어야 합니다.
- approval 발급 뒤에 `corrected_text`가 다시 바뀌어도 기존 pending approval preview는 바뀌면 안 됩니다.
- 사용자가 새 수정본으로 저장하려면 새 bridge action으로 새 approval를 만들어야 합니다.
- auto-rebase는 계속 금지합니다.

## 왜 immutable snapshot이어야 하는가

- approval-safe:
  - 사용자가 본 preview와 실제 write body가 같은 approval snapshot을 가리킬 수 있습니다.
- auditability:
  - 나중에 어떤 텍스트가 승인되었는지 approval trail만으로 읽을 수 있습니다.
- local-first:
  - mutable source message와 immutable approval snapshot을 분리해도 모두 로컬 session / approval / task-log surface 안에서 유지됩니다.

## Future Trace Contract

### 재사용하는 최소 필드

- `artifact_id`
- `source_message_id`
- `save_content_source`
- `approval_id`

### 확장 규칙

- current shipped path:
  - `save_content_source = original_draft`
- future corrected-save path:
  - `save_content_source = corrected_text`

### 추가로 필요한 최소 trace 사실

- corrected-save approval는 same `artifact_id`와 same `source_message_id`를 따라야 합니다.
- approval payload와 approval/write task-log detail은 같은 `save_content_source`를 반복해야 합니다.
- approval object는 request-time frozen body snapshot을 이미 `note_text` / preview로 들고 있어야 합니다.

## Snapshot Identity Decision

- `save_content_source = corrected_text`만으로는 충분하지 않습니다.
  - 나중에 또 다른 correction submit이 들어오면 어느 corrected text를 승인하려 했는지 구분할 수 없기 때문입니다.
- `save_content_source + source_message_id`만으로도 충분하지 않습니다.
  - same source message 위에서 `corrected_text`는 다시 바뀔 수 있기 때문입니다.
- 이번 라운드에서 고정하는 최소 계약은 아래입니다.
  - separate `snapshot_id`는 first corrected-save slice에서 추가하지 않습니다.
  - 대신 `approval_id`를 immutable approval snapshot identity로 봅니다.
  - 그 approval record 안의 frozen `note_text` / preview body가 실제 snapshot body입니다.

## Acceptance / Audit Placeholder

- current shipped acceptance:
  - correction submit success
  - original-draft save approval success
- future corrected-save acceptance placeholder:
  - explicit bridge action creates a fresh approval linked to the same `artifact_id` / `source_message_id`
  - the new approval exposes `save_content_source = corrected_text`
  - the approval preview and write body both match the same request-time corrected-text snapshot
  - later correction submit does not mutate the already-issued approval preview
  - a second corrected-save request creates a different `approval_id`

## 범위 경계

- 이 계약은 corrected-save approval UI나 API가 이미 구현되었다고 주장하지 않습니다.
- 이 계약은 `rejected` content outcome을 다루지 않습니다.
- 이 계약은 review queue, user-level memory, operator surface를 요구하지 않습니다.
- 이 계약은 separate artifact store를 요구하지 않습니다.

## 후속 구현 반영

- later implementation fixed this UI policy as follows:
  - bridge action은 correction area에 항상 보입니다
  - recorded `corrected_text`가 없으면 disabled helper copy로 먼저 `수정본 기록`이 필요하다고 안내합니다
  - 이후 editor가 다시 dirty 상태가 되어도 bridge action은 마지막 recorded correction 기준을 유지하고, helper copy가 그 사실을 드러냅니다
