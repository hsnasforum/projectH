# 2026-03-26 Suggested Scope And Save Weighting Policy

## 목적

이 문서는 future review surface에서 필요한 `suggested scope` 기본 정책과 `approval-backed save` 보조 가중치 원칙을 가장 작은 수준으로 고정합니다.

- 현재 shipped contract를 바꾸지 않습니다
- review queue나 user-level memory가 현재 구현된 것처럼 쓰지 않습니다
- `grounded brief`, `session_local`, `durable_candidate` 선택을 다시 열지 않습니다

## 현재 단계와의 관계

### 현재 shipped contract
- 로컬 퍼스트 문서 비서 웹 MVP
- 문서 읽기 / 요약 / 검색 / 일반 채팅
- 승인 기반 저장
- evidence / source / summary chunk 표시
- feedback 저장

### 이번 문서의 역할
- future review item이 어떤 scope를 기본값으로 제안해야 하는지 정합니다
- explicit confirmation이 없을 때 approval-backed save를 어느 수준의 보조 근거로 읽을지 정합니다
- acceptance / eval placeholder가 어떤 trace를 요구해야 하는지 정합니다

## Suggested Scope 기본 정책

### 1. 기본 suggested scope 순서

여러 scope 후보가 모두 맞는다면 기본 suggested scope는 아래 순서를 따릅니다.

1. `workflow_type`
2. `path_family`
3. `document_type`
4. `global`

### 2. 왜 이 순서인가

- 기본값은 더 좁고, 더 안전하고, 더 되돌리기 쉬운 제안이어야 합니다
- `workflow_type`는 현재 artifact가 수행된 작업 방식에 붙기 때문에, unrelated document work로 퍼질 위험이 가장 작습니다
- `path_family`는 local project 또는 folder cluster에 묶일 수 있어 여전히 좁지만, incidental directory structure를 과적용할 수 있으므로 기본 2순위로 둡니다
- `document_type`는 여러 unrelated path와 workflow로 쉽게 퍼질 수 있어 더 넓은 제안입니다
- `global`은 가장 넓고 rollback 영향도도 가장 크므로 기본 fallback으로만 남겨 둡니다

### 3. 더 넓은 suggested scope가 허용되는 경우

아래 중 하나가 있을 때만 더 넓은 suggested scope를 제안할 수 있습니다.

- 더 좁은 scope 후보가 trace상 불안정하거나 부정확합니다
- 같은 정규화 신호가 이미 둘 이상의 더 좁은 context에 걸쳐 반복됩니다
- 사용자가 더 넓은 재사용을 명시적으로 확인합니다

원칙:
- 더 넓은 suggested scope는 자동 적용이 아니라 review input입니다
- broader suggestion이 있으면 왜 더 좁은 기본값을 쓰지 않았는지 trace가 남아야 합니다

### 4. Review Item에 남겨야 할 최소 trace

최소 필드:
- `proposed_scope`
- `scope_candidates_considered`
- `scope_suggestion_reason`

원칙:
- `proposed_scope`는 reviewed scope가 아닙니다
- review의 `accept` 또는 `edit` 전까지는 제안값으로만 남아야 합니다

## Approval-Backed Save Weighting 기본 정책

### 1. Approval-Backed Save 정의

이 문서에서 approval-backed save는 다음을 뜻합니다.

- 현재 note-save approval flow를 거친 artifact
- approval trace가 남아 있고
- 실제로 `approval_granted`가 기록된 save outcome

### 2. 기본 원칙

- approval-backed save는 supporting evidence입니다
- approval-backed save는 explicit confirmation을 대체하지 않습니다
- approval-backed save는 automatic promotion trigger가 아닙니다

### 3. Explicit Confirmation이 없을 때의 baseline

명시적 사용자 확인이 없을 때 approval-backed save는 아래 수준으로만 읽습니다.

- content 계열 후보에는 약한 보조 근거
- save-path acceptability 계열 후보에는 중간 수준의 보조 근거

여기서 save-path acceptability는 아래와 같은 흐름을 뜻합니다.

- requested path가 거절되지 않았는지
- reissue 없이 승인되었는지
- 같은 path-family 또는 filename pattern이 반복되는지

### 4. Approval-Backed Save가 할 수 없는 것

approval-backed save만으로는 아래를 할 수 없습니다.

- `session_local`을 곧바로 `durable_candidate`로 승격
- `durable_candidate`를 future user-level memory로 승격
- broader suggested scope를 정당화
- content correction quality를 explicit confirmation처럼 해석

### 5. Content와 Save Friction의 분리

- content correction signal은 response quality와 preference alignment를 보는 축입니다
- approval-backed save signal은 save acceptability와 approval friction을 보는 축입니다
- 같은 artifact에 두 신호가 함께 있어도, eval에서는 서로 다른 축으로 유지해야 합니다
- 특히 simple approved save는 corrected content pair를 대체하지 않습니다

### 6. Review Item에 남겨야 할 최소 trace

최소 필드:
- `supporting_approval_ids` if present
- `has_explicit_confirmation`

원칙:
- explicit confirmation-backed candidate와 approval-backed-save-supported candidate를 trace에서 구분할 수 있어야 합니다
- save support가 있었다는 사실과, 그 support만으로는 promotion이 아니었다는 사실을 함께 남겨야 합니다

## Acceptance / Eval Placeholder

### 1. Suggested Scope가 너무 넓지 않은지

- 여러 scope 후보가 모두 맞을 때 기본 suggested scope가 `workflow_type -> path_family -> document_type -> global` 순서를 벗어나지 않는지 봅니다
- 더 넓은 scope가 제안됐다면 `scope_suggestion_reason`이 남았는지 봅니다

### 2. Approval-Backed Save가 과도한 가중치를 갖지 않는지

- explicit confirmation이 없는 candidate에서 approval-backed save가 sole reason으로 읽히지 않는지 봅니다
- approval-backed save가 broader suggested scope나 reviewed memory promotion의 단독 근거가 되지 않는지 봅니다

### 3. Narrower vs Broader Scope Trace

- 같은 candidate에 대해 어떤 narrower scope 후보가 있었는지 `scope_candidates_considered`로 되짚을 수 있어야 합니다
- review 결과가 `edit`로 scope를 좁히거나 넓혔다면 그 차이도 trace에 남아야 합니다

### 4. Separate Eval Axes

- correction reuse 개선과 approval friction 감소는 서로 다른 축으로 측정해야 합니다
- approved save가 있었다는 이유만으로 content correction 품질 개선으로 집계하면 안 됩니다

### 5. Acceptance 문서에서의 분리

- 이 정책은 future review surface placeholder입니다
- current shipped acceptance gate처럼 쓰면 안 됩니다
- user-level memory가 아직 구현되지 않았다는 사실과 계속 분리해서 적어야 합니다

## 지금 확정하지 않는 것

- category별 recurrence tuning
- approval-backed save의 category별 세부 가중치 튜닝
- review UI 상세 UX
- first operator surface
- 모델 학습 또는 personalization pipeline

## OPEN QUESTION

1. 일부 repository-shaped workflow에서 `path_family`를 `workflow_type`보다 먼저 제안해야 할 예외가 필요한지?
2. baseline 이후 category별로 approval-backed save 가중치를 더 세분화해야 하는지?
3. `defer` 상태가 오래 유지될 때 자동 만료가 필요한지, 명시적 review까지 유지할지?
4. 메모리 단계 이후의 첫 operator surface는 브라우저, 로컬 파일 작업, 특정 앱 중 어디가 가장 안전한가?
