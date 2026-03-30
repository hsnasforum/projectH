# 2026-03-26 Grounded Brief Memory Contract

## 목적

이 문서는 2026-03-26 로드맵의 2단계인 `교정 / 승인 / 선호 메모리`를 가장 작은 설계 계약 수준으로 고정한 초안입니다.

- 현재 shipped contract를 바꾸지 않습니다
- 프로그램 조작을 현재 기능처럼 확정하지 않습니다
- 모델 학습을 현재 구현처럼 쓰지 않습니다

## 현재 단계와의 관계

### 현재 shipped contract
- 로컬 퍼스트 문서 비서 웹 MVP
- 문서 읽기 / 요약 / 검색 / 일반 채팅
- 승인 기반 저장
- evidence / source / summary chunk 표시
- 피드백 기록

### 이번 문서의 역할
- 다음 단계에서 어떤 artifact를 기준 단위로 삼을지 고정
- correction / approval / preference memory가 최소한 무엇을 묶어야 하는지 정리
- acceptance / eval placeholder를 미리 정의

## 선택한 공식 artifact

첫 공식 artifact는 `grounded brief`입니다.

### 왜 `grounded brief`인가
- 현재 codebase는 이미 한 문서에서 요약 본문과 저장 미리보기를 만드는 흐름에 가장 가깝습니다
- evidence, source path, summary chunks, approval preview, feedback을 한 단위로 묶기 쉽습니다
- `memo`보다 범용적이고, `action-item note`보다 좁지 않아서 문서 종류가 달라도 재사용하기 쉽습니다
- correction memory는 사실성, 형식, 말투, 근거 충분성, 후속 질문 대응력을 한 번에 볼 수 있어야 하는데 brief 단위가 가장 적합합니다

## 최소 설계 계약

### 1. Artifact Identity

아직 구현하지 않지만, 다음 단계에서는 save-worthy 결과마다 `artifact_id` 개념이 필요합니다.

최소 필드:
- `artifact_id`
- `artifact_kind = grounded_brief`
- `session_id`
- `assistant_message_id`
- `created_at`

원칙:
- 한 번의 save-worthy 문서 결과는 하나의 artifact로 봅니다
- approval이 여러 번 재발급되어도 artifact는 유지됩니다

### 2. Original Response Snapshot

최소 필드:
- `assistant_message_id`
- `draft_markdown`
- `source_paths`
- `response_origin`
- `summary_chunks_snapshot`
- `evidence_snapshot`

원칙:
- 현재 구현이 메시지 단위로 evidence와 summary chunk를 보관하므로, 다음 단계도 우선은 **artifact-level snapshot** 방식으로 갑니다
- 별도의 정규화된 evidence store는 다음 단계의 최소 계약 범위를 벗어납니다

### 3. Corrected Outcome

최소 상태:
- `accepted_as_is`
- `corrected`
- `rejected`

최소 필드:
- `outcome`
- `corrected_text`
- `corrected_at`
- `reason_label`
- `reason_note`

원칙:
- 수정이 없더라도 `accepted_as_is`는 기록 가치가 있습니다
- correction이 있다면 원본 응답과 수정 결과가 같은 artifact 아래에서 비교 가능해야 합니다

### 4. Approval Trail

최소 필드:
- `approval_id`
- `outcome = approved | rejected | reissued`
- `requested_path`
- `overwrite`
- `created_at`

추가 연계:
- reissue일 때는 old/new approval 연결이 필요합니다
- approval trail은 artifact와 분리된 별도 이벤트일 수 있지만, artifact에서 역추적 가능해야 합니다

### 5. Shared Reason Fields + Distinct Label Sets

최소 구조:
- `reason_scope = correction | approval_reject | approval_reissue`
- `reason_label`
- `reason_note`

Correction label:
- `factual_error`
- `irrelevant_result`
- `context_miss`
- `awkward_tone`
- `format_preference`

Approval reject label:
- `content_needs_fix`
- `save_not_needed`
- `path_not_acceptable`

Approval reissue label:
- `path_change`
- `filename_preference`
- `directory_preference`

원칙:
- 현재 구현의 feedback label/reason 흐름은 `correction` scope로 최대한 그대로 이어받습니다
- reject / reissue는 correction label을 억지로 재사용하지 않습니다
- `shared fields + distinct label sets` 구조가 가장 작고, acceptance/eval에서도 scope 안에서 count를 비교하기 쉽습니다
- content correction과 save-path 변경을 한 taxonomy로 강하게 합치지 않습니다

### 6. Preference Signal Candidate

최소 필드:
- `candidate_id`
- `category`
- `statement`
- `source_artifact_ids`
- `status = session_local | durable_candidate`
- `created_at`

예시 category:
- `tone`
- `format`
- `evidence_density`
- `action_style`

원칙:
- 이 단계에서는 아직 `durable preference memory`를 확정하지 않습니다
- 우선은 후보(candidate)만 저장하고, 승격은 나중 단계에서 다룹니다

### 7. 최소 승격 정책

#### Session-Local에 머무는 경우
- 하나의 grounded brief, 한 번의 retry, 또는 한 번의 approval 이벤트에서만 나온 신호
- 명시적 사용자 확인이 없는 신호
- trace가 불완전하거나, 다른 후보와 충돌해서 아직 정규화하기 어려운 신호
- immediate follow-up 개선에는 유용하지만 장기 후보로 보기에는 근거가 약한 신호

#### Durable Candidate가 될 수 있는 최소 조건
- `category`, `statement`, `source_artifact_ids`가 있는 정규화된 candidate record가 있어야 합니다
- 각 source artifact가 아래 trace를 보존해야 합니다:
  - original response snapshot
  - evidence/source snapshot
  - reason metadata
- 그리고 아래 둘 중 하나는 충족해야 합니다:
  - 같은 정규화 신호가 최소 2개의 grounded brief에서 반복됨
  - 사용자가 그 선호를 재사용해도 된다고 명시적으로 확인함

#### Approval Trace 정책
- approval trace가 있으면 artifact에 반드시 연결합니다
- approval trace는 promotion review를 위한 보조 근거입니다
- 명시적 사용자 확인이 없을 때 approval-backed save는 다음처럼만 읽습니다:
  - content 계열 후보에는 약한 보조 근거
  - save-path acceptability 계열 후보에는 중간 수준의 보조 근거
- 하지만 현재 approval은 save flow에서만 생기므로, approval trace 존재를 유일한 최소 조건으로 두지는 않습니다
- approval-backed save만으로 `durable_candidate`를 만들거나 더 넓은 suggested scope를 정당화하지 않습니다
- 세부 suggested scope / save weighting 정책은 `2026-03-26-suggested-scope-and-save-weighting-policy.md`에서 분리합니다

#### Guardrail
- `durable_candidate`는 어디까지나 reviewable local candidate입니다
- 자동으로 user-level durable memory로 승격하지 않습니다
- 되돌리기 쉽고, 버리기 쉽고, 로컬에서 감사 가능한 상태를 유지해야 합니다

### 8. Session-Level vs Future User-Level Memory Boundary

#### Session-Level Memory
- 현재 세션과 immediate follow-up loop에 붙는 개념입니다
- 같은 세션 안의 retry나 다음 grounded brief 개선에만 우선 적용됩니다

#### Durable Candidate
- 세션 밖으로 남을 수 있지만, 아직은 review queue에 있는 후보 상태입니다
- future user-level memory와는 분리해서 다룹니다

#### Future User-Level Memory
- 아직 future design target입니다
- 현재 shipped contract에는 user profile, cross-session auto-application, always-on preference layer가 없습니다
- 다음 단계 이후로 올리려면 최소한 아래가 필요합니다:
  - candidate accept / edit / reject surface
  - local audit trail + rollback
  - scope rule
  - conflict resolution rule
- 세부 최소 계약은 `2026-03-26-durable-candidate-review-surface.md`에서 분리합니다

### 9. Evidence / Source Trace Link

각 artifact는 아래로 되짚어질 수 있어야 합니다.

- 원본 source path
- 원본 assistant message
- evidence snapshot
- summary chunk snapshot
- reason record
- approval trail if present
- corrected outcome

원칙:
- trace가 끊기면 eval 자산으로 승격할 수 없습니다

## Acceptance / Eval Placeholder

### 1. correction memory가 다음 응답을 개선했는지
- 같은 `session_local` 또는 `durable_candidate`가 적용된 다음 artifact에서 동일 correction reason이 재발하지 않는지 봅니다
- 사용자가 요구하는 수정량이 줄었는지 봅니다

### 2. 같은 실수가 줄었는지
- `correction` scope 안에서 artifact별 `reason_label` 반복 횟수를 비교합니다
- 동일 사용자 패턴에서 `factual_error`, `context_miss`, `awkward_tone`, 형식 관련 correction이 줄어야 합니다
- reject / reissue reason count는 correction count와 섞지 않습니다

### 3. 사용자 선호가 반영됐는지
- 이전에 수정된 말투/형식/근거 밀도가 다음 brief에 반영됐는지 봅니다
- 반복 재사용이나 명시적 사용자 확인이 보이는 후보만 durable candidate로 다룹니다

### 4. approval friction이 줄었는지
- path나 filename 선호가 이미 알려진 경우 `approval_reissue` scope reason이 줄어드는지 봅니다
- 단, approval trace는 계속 남아 있어야 하고 위험 동작을 숨기면 안 됩니다
- correction reuse와 approval friction은 같은 artifact를 보더라도 서로 다른 평가 축으로 유지합니다

### 5. artifact / approval / evidence trace가 끊기지 않는지
- `artifact -> original response -> evidence/source -> reason record -> approval trail if present -> corrected outcome`가 이어져야 합니다
- 중간 링크가 빠지면 eval-ready artifact가 아닙니다

## 지금 확정하지 않는 것

- user-level durable memory의 최종 schema
- category별 recurrence threshold 튜닝
- approval-backed save 가중치의 category별 세부 튜닝
- 첫 프로그램 조작 표면
- 학습 또는 재학습 파이프라인

## OPEN QUESTION

1. 기본 recurrence rule을 모든 candidate category에 대해 `grounded brief` 2회로 둘지, category별로 다르게 둘지?
2. baseline 이후 category별로 approval-backed save 가중치를 더 다르게 둘 필요가 있는지?
3. 일부 저장소/프로젝트형 workflow에서 `workflow_type`보다 `path_family`를 먼저 제안해야 할 예외가 필요한지?
4. 메모리 단계 이후의 첫 operator surface는 브라우저, 로컬 파일 작업, 특정 앱 중 어디가 가장 안전한가?
