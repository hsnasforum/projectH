# 2026-03-27 corrected-save-reconciliation-contract

## 목적

- current shipped truth와 next reconciliation target을 분리한 채, corrected text와 save approval의 관계를 한 가지 권고안으로 고정합니다.
- 이번 라운드는 문서 작업만 다룹니다.
- correction submit과 save approval를 자동으로 합치지 않습니다.

## 현재 구현 truth

- grounded-brief response surface에는 one multiline correction editor가 있습니다.
- editor는 current grounded-brief draft text로 seed됩니다.
- explicit correction submit은 original grounded-brief source message에 `corrected_text`와 `corrected_outcome.outcome = corrected`를 기록합니다.
- unchanged submit은 validation으로 막습니다.
- save approval는 여전히 별도 흐름입니다.
- current pending approval preview와 pending approval execution은 approval가 발급될 때 캡처된 original draft 기반 `note_text`를 따릅니다.
- correction submit은 이미 발급된 pending approval를 수정하지 않습니다.

## 검토한 선택지

### Option A

- save approval는 계속 original draft만 대상으로 둡니다.
- corrected text는 content artifact로만 남기고 save target으로는 다루지 않습니다.

### Option B

- current original-draft save approval는 그대로 유지합니다.
- 다만 나중에 사용자가 원할 때 corrected text를 대상으로 한 save approval를 별도 명시 action으로 요청할 수 있게 둡니다.
- correction submit 자체는 save request가 아닙니다.

## 최종 권고안

- `Option B`를 권고안으로 고정합니다.

## 왜 `Option B`가 현재 MVP에 맞는가

- document-first MVP는 실제 작업 결과를 저장 가능한 문서 흐름으로 이어 가는 것이 중요합니다.
- corrected text를 영구히 save 불가능한 side artifact로만 두면 문서 생산성 루프가 끊깁니다.
- 동시에 correction submit이 save approval로 바로 승격되면 approval-safe 원칙이 깨집니다.
- `Option B`는 둘을 동시에 피합니다:
  - correction submit은 content artifact 기록으로 남음
  - save는 여전히 별도 명시 행동과 approval를 거침

## 왜 approval-safe 한가

- auto-rebase를 금지하므로, 사용자가 한 번 본 approval preview가 나중에 조용히 다른 텍스트로 바뀌지 않습니다.
- corrected-save는 새 approval object를 발급할 때만 생기므로, approval preview와 실제 write body가 항상 같은 snapshot을 가리킬 수 있습니다.
- 기존 original-draft approval는 그대로 immutable snapshot으로 남아 audit 읽기가 쉬워집니다.

## 왜 감사 가능성이 높은가

- same `artifact_id`와 `source_message_id` anchor를 그대로 재사용할 수 있습니다.
- original draft save와 corrected save를 같은 artifact 아래에서 서로 다른 approval event로 구분할 수 있습니다.
- future corrected-save approval가 생기더라도 audit는 아래처럼 단순하게 읽힙니다.
  - original grounded-brief source message
  - optional `corrected_text`
  - explicit corrected-save approval request
  - approval preview snapshot
  - approval granted / write_note outcome

## 왜 future memory/review layer와 덜 충돌하는가

- correction signal과 approval signal이 계속 분리됩니다.
- later review queue나 durable candidate review는 `corrected_text` 존재와 corrected-save approval 존재를 별도 축으로 읽을 수 있습니다.
- content improvement와 save-path acceptability를 서로 다른 trace로 유지할 수 있어, future evaluation에서도 axis separation을 해치지 않습니다.

## Response Card Action Contract

### current shipped contract

- correction submit action은 response card의 content-edit area에 속합니다.
- save approval action은 approval surface에 속합니다.
- 사용자는 correction만 하고 저장하지 않을 수 있습니다.
- current approval preview는 original draft snapshot 기준입니다.

### recommended next contract

- response card 안에서는 `내용 수정` area와 `저장 요청` area를 semantic하게 분리합니다.
- correction area는 계속 아래 역할만 가집니다.
  - draft text 확인
  - 수정
  - `수정본 기록`
- corrected-save가 추가되더라도 bridge action은 별도 라벨을 써야 합니다.
  - 예: `이 수정본으로 저장 요청`
- actual approval preview, approve, reject, reissue controls는 계속 approval surface에 남깁니다.
- 즉, response card는 save target을 선택하는 곳이고, approval surface는 risky write를 검토/승인하는 곳입니다.

### copy and placement rule

- correction copy는 content artifact 언어를 써야 합니다.
  - 예: `수정본 기록`
- save copy는 approval 언어를 써야 합니다.
  - 예: `저장 요청`, `이 수정본으로 저장 요청`
- 같은 버튼이 correction과 save를 동시에 뜻하면 안 됩니다.
- same response card 안에 둘 다 있더라도, correction textarea footer와 approval card는 visually separate되어야 합니다.

## Approval Preview Contract

### current shipped truth

- approval preview는 original draft 기반 `note_text` snapshot을 보여 줍니다.
- correction submit은 그 preview를 바꾸지 않습니다.

### future corrected-save contract

- corrected-save approval preview는 사용자가 explicit corrected-save action을 눌렀을 때의 `corrected_text` snapshot으로 생성되어야 합니다.
- 이미 떠 있는 original-draft approval preview를 수정본 기준으로 silent rewrite하면 안 됩니다.
- corrected text가 다시 바뀌어도 기존 corrected-save approval preview는 immutable snapshot으로 남아야 합니다.

## Trace / Acceptance Contract

### current trace reading

- corrected submit 성공:
  - original grounded-brief source message에 `corrected_text`
  - same source message에 `corrected_outcome.outcome = corrected`
  - task log에 `correction_submitted`
- original-draft save approval 성공:
  - approval trail
  - write note trace
  - source message에 `corrected_outcome.outcome = accepted_as_is`
- 이 둘은 같은 artifact anchor를 공유하지만 서로 다른 사실을 뜻합니다.
  - `corrected`는 edited content 제출
  - `accepted_as_is`는 explicit save completion

### future corrected-save trace requirement

- future corrected-save approval는 current trace를 재해석하면 안 되고, 별도 explicit trace가 필요합니다.
- 최소 요구:
  - same `artifact_id`
  - same `source_message_id`
  - new `approval_id`
  - approval preview / `note_text` snapshot generated from corrected text
  - explicit save-target discriminator
    - 예: `save_content_source = original_draft | corrected_text`
- 이 discriminator는 최소한 아래 surface에 반복되어야 합니다.
  - approval payload
  - approval_requested task-log detail
  - approval_granted task-log detail
  - write_note task-log detail

### acceptance separation

- `corrected submit 성공`과 `save approval 성공`은 각각 독립 acceptance로 봅니다.
- future `corrected-save reconciliation`이 생기면 세 번째 acceptance로 따로 봐야 합니다.
- 즉 acceptance는 아래 셋으로 분리됩니다.
  - corrected submit success
  - original-draft save approval success
  - corrected-save approval success

## 범위 경계

- 이 계약은 corrected-save approval를 아직 구현했다고 주장하지 않습니다.
- 이 계약은 `rejected` content outcome을 다루지 않습니다.
- 이 계약은 review queue나 user-level memory를 요구하지 않습니다.
- 이 계약은 separate artifact store를 요구하지 않습니다.

## OPEN QUESTION

- future corrected-save trace에서 save-target discriminator의 실제 field name을 `save_content_source`, `approval_content_source`, `note_source_kind` 중 무엇으로 고정할지가 아직 남아 있습니다.
