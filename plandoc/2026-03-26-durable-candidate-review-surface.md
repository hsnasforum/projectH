# 2026-03-26 Durable Candidate Review Surface

## 목적

이 문서는 `durable_candidate` 이후 단계에서 필요한 최소 `review / scope / rollback` surface를 고정하는 follow-up 설계 메모입니다.

- 현재 shipped contract를 바꾸지 않습니다
- `grounded brief`, `session_local`, `durable_candidate` 선택을 다시 열지 않습니다
- user-level memory를 현재 구현처럼 쓰지 않습니다
- 프로그램 조작과 모델 학습을 현재 단계처럼 쓰지 않습니다

## 현재 단계와의 관계

### 현재 shipped contract
- 로컬 퍼스트 문서 비서 웹 MVP
- 문서 읽기 / 요약 / 검색 / 일반 채팅
- 승인 기반 저장
- evidence / source / summary chunk 표시
- feedback 저장

### 이미 고정된 것
- 공식 artifact는 `grounded brief`
- `session_local -> durable_candidate` 최소 승격 정책은 문서 계약으로 존재합니다
- `durable_candidate`는 아직 future user-level memory가 아니라 reviewable local candidate 상태입니다

### 이번 문서의 역할
- `durable_candidate`를 future user-level memory로 올리기 전에 필요한 최소 review surface를 고정합니다
- scope / conflict / rollback 원칙을 가장 작은 수준으로 고정합니다
- acceptance / eval placeholder가 어떤 review trace를 요구해야 하는지 정리합니다

## 최소 Review Surface 계약

### 1. Review Queue에 들어가는 candidate

review queue에는 아래 조건을 모두 만족한 `durable_candidate`만 들어갑니다.

- `candidate_id`, `category`, `statement`, `source_artifact_ids`가 있는 정규화된 candidate
- source artifact가 trace-complete 상태인 candidate
- 아직 final review outcome이 없는 candidate

원칙:
- `session_local`은 review queue에 직접 들어가지 않습니다
- review queue는 future local review surface이며, 현재 구현된 세션 UI나 API가 아닙니다

### 2. 최소 Review Item 필드

최소 필드:
- `review_item_id`
- `candidate_id`
- `category`
- `proposed_statement`
- `proposed_scope`
- `scope_candidates_considered`
- `scope_suggestion_reason`
- `source_artifact_ids`
- `supporting_reason_labels`
- `supporting_approval_ids` if present
- `has_explicit_confirmation`
- `conflict_candidate_ids`
- `review_status = pending | accepted | edited | rejected | deferred`
- `created_at`
- `reviewed_at`
- `review_note`

원칙:
- review item은 candidate를 대체하지 않고 candidate를 검토하기 위한 별도 로컬 surface입니다
- review item은 나중에 user-level memory가 생기더라도 원본 candidate trace를 잃지 않아야 합니다

### 3. 최소 Review Action

#### `accept`
- candidate를 수정 없이 future user-level memory 후보로 승인합니다
- reviewed scope와 reviewed timestamp가 남아야 합니다

#### `edit`
- statement나 scope를 좁히거나 다듬은 뒤 승인합니다
- 원래 candidate와 편집된 reviewed 결과를 둘 다 추적할 수 있어야 합니다

#### `reject`
- candidate를 승격하지 않습니다
- rejection 자체가 감사 가능한 trace로 남아야 합니다

#### `defer`
- 판단을 미루고 review queue에 남깁니다
- conflict가 있거나 scope를 아직 고르기 어렵다면 defer가 기본 안전 동작이 됩니다

### 4. Review 주체 가정

- 기본 가정은 같은 로컬 사용자 본인 review입니다
- 현재 저장소에는 multi-user profile, admin review, shared workspace 개념이 없습니다
- 따라서 future review surface도 우선은 single local operator 가정으로 시작합니다

### 5. 현재 구현과 섞지 않는 서술 원칙

- review queue는 현재 UI, 현재 API, 현재 storage schema가 아닙니다
- 이 문서는 future design target의 최소 계약만 고정합니다
- 현재 구현은 여전히 feedback, approval, task log까지만 존재합니다

## Scope / Conflict / Rollback 원칙

### 1. Scope 후보 단위

future user-level memory가 생긴다면 최소 후보 scope는 아래입니다.

- `workflow_type`
- `path_family`
- `document_type`
- `global`

원칙:
- 기본 suggested scope는 더 좁고 되돌리기 쉬운 쪽을 우선해야 하므로 아래 순서를 기본값으로 둡니다:
  - `workflow_type`
  - `path_family`
  - `document_type`
  - `global`
- scope는 넓을수록 위험하므로 review 없이 자동 확정하면 안 됩니다
- 더 넓은 scope suggestion은 아래 중 하나가 있을 때만 허용합니다:
  - 더 좁은 scope 후보가 trace상 불안정하거나 부정확함
  - 같은 신호가 이미 둘 이상의 더 좁은 context에 걸쳐 반복됨
  - 사용자가 더 넓은 재사용을 명시적으로 확인함
- `proposed_scope`는 review를 위한 제안값일 뿐, reviewed scope 자체가 아닙니다
- 세부 suggested scope / save weighting 정책은 `2026-03-26-suggested-scope-and-save-weighting-policy.md`에서 분리합니다

### 2. Approval-Backed Save Weighting 원칙

- approval-backed save는 현재 note-save approval을 거쳐 실제로 `approval_granted`가 남은 artifact를 뜻합니다
- approval-backed save는 supporting evidence이지, 자동 승격 버튼이 아닙니다
- 명시적 사용자 확인이 없을 때는 아래처럼만 읽습니다:
  - content 계열 후보에는 약한 보조 근거
  - save-path acceptability 계열 후보에는 중간 수준의 보조 근거
- approval-backed save만으로는 다음을 할 수 없습니다:
  - `durable_candidate` 생성
  - broader suggested scope 정당화
  - future user-level memory 승격
- content correction signal과 save-path preference signal은 같은 artifact에 있어도 다른 평가 축으로 유지합니다

### 3. Conflict 원칙

- reviewed memory는 unreviewed `durable_candidate`보다 우선합니다
- 같은 category에서는 더 좁은 reviewed scope가 더 넓은 reviewed scope보다 우선합니다
- 같은 scope와 같은 category에서 statement가 충돌하면 자동 승격하지 않고 `defer` 또는 `reject`로 남겨야 합니다
- `edit`는 conflict를 해소하기 위해 statement를 좁히거나 scope를 줄이는 기본 수단이어야 합니다

### 4. Rollback / Disable 원칙

최소한 아래 단위에서 rollback 또는 disable이 가능해야 합니다.

- reviewed memory item 단위
- reviewed scope bucket 단위

원칙:
- rollback은 과거 trace를 삭제하지 않습니다
- rollback 뒤에는 해당 memory가 이후 응답에 더 이상 적용되지 않아야 합니다
- rollback 사실, 적용 중단 시점, 관련 source candidate는 모두 로컬 audit에 남아야 합니다

### 5. 왜 이 surface 없이는 승격하면 안 되는가

- review surface가 없으면 `durable_candidate`가 실제로 검토됐는지 알 수 없습니다
- scope가 없으면 선호가 과도하게 넓은 문맥에 적용될 수 있습니다
- conflict 원칙이 없으면 서로 다른 후보가 조용히 덮어써질 수 있습니다
- rollback이 없으면 잘못된 선호가 고착되고, 로컬 감사 가능성과 가역성이 사라집니다

## Acceptance / Eval Placeholder

### 1. reviewed vs unreviewed 구분

- future user-level memory로 취급되는 항목은 반드시 review outcome을 가져야 합니다
- unreviewed `durable_candidate`는 계속 proposal 상태로 남아야 합니다

### 2. rollback 후 적용 중단 확인

- rollback 또는 disable 뒤에는 같은 reviewed scope 안의 later artifact에서 해당 memory가 적용되지 않아야 합니다
- non-application trace도 audit에 남아야 합니다

### 3. conflict trace 유지

- conflict가 있었던 candidate는 `conflict_candidate_ids` 또는 동등한 resolution trace를 남겨야 합니다
- 어떤 항목이 accepted/edited/rejected/deferred 되었는지 사후에 되짚을 수 있어야 합니다

### 4. acceptance 문서에서의 분리 원칙

- review surface와 future user-level memory는 current shipped gate로 쓰면 안 됩니다
- acceptance 문서에서는 항상 `future placeholder`로만 표시해야 합니다
- suggested scope와 approval-backed save weighting도 current shipped behavior처럼 쓰면 안 됩니다

## 지금 확정하지 않는 것

- category별 recurrence threshold 튜닝
- approval-backed save의 category별 세부 가중치 튜닝
- review UI 세부 UX
- first operator surface
- 모델 학습 또는 재학습 파이프라인

## OPEN QUESTION

1. 일부 repository-shaped workflow에서 `path_family`를 `workflow_type`보다 먼저 제안해야 할 예외가 필요한지?
2. `defer` 상태가 오래 유지될 때 자동 만료가 필요한지, 명시적 review까지 유지할지?
3. scope-level disable이 더 좁은 child scope까지 같이 막아야 하는지?
4. 메모리 단계 이후의 첫 operator surface는 브라우저, 로컬 파일 작업, 특정 앱 중 어디가 가장 안전한가?
