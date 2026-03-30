# 2026-03-27 First Memory Trace Implementation Cut

## 목적

이 문서는 `grounded brief` 메모리 설계에서 실제 구현을 시작할 때의 **첫 구현 슬라이스**를 하나로 고정합니다.

- 현재 shipped contract를 바꾸지 않습니다
- memory 정책 자체를 다시 열지 않습니다
- review queue, user-level memory, operator surface를 첫 슬라이스로 끌어오지 않습니다

## 이번 라운드에서 고정하는 것

### Current Shipped Contract
- 로컬 퍼스트 문서 비서 웹 MVP
- 문서 읽기 / 요약 / 검색 / 일반 채팅
- 승인 기반 저장과 reissue
- evidence / source / summary chunk 표시
- feedback 저장

### Next-Phase Design Target
- `grounded brief` 기준 correction / approval / preference memory foundation

### 이번 문서의 역할
- 첫 구현 슬라이스를 1개로 고정
- 왜 그 슬라이스가 가장 작은 가치 있는 시작점인지 설명
- 실제로 먼저 움직일 파일, 테스트, 문서 범위를 고정

## 최종 선택한 First Slice

`artifact_id` 생성과 `message / session / task-log` linkage를 첫 슬라이스로 고정합니다.

### 한 줄 정의

각 `grounded brief` 응답에 하나의 `artifact_id`를 부여하고, 같은 식별자를 현재 assistant message, approval trace, task log에 일관되게 남기는 additive trace-anchor 슬라이스입니다.

## 왜 이 슬라이스가 1순위인가

### 1. 현재 raw trace를 가장 많이 재사용합니다
- assistant message에는 이미 아래가 들어갑니다:
  - `message_id`
  - 응답 본문
  - `response_origin`
  - `selected_source_paths`
  - `evidence`
  - `summary_chunks`
  - `note_preview`
  - `saved_note_path`
- task log에는 이미 아래가 들어갑니다:
  - `approval_requested`
  - `approval_granted`
  - `approval_rejected`
  - `approval_reissued`
  - `write_note`
  - `response_feedback_recorded`

### 2. 아직 없는 것은 “새 저장소”보다 “공통 anchor”입니다
- original response snapshot은 이미 assistant message surface에 상당 부분 존재합니다
- approval trail도 이미 이벤트로 남습니다
- feedback도 이미 `message_id` 기준으로 붙습니다
- 하지만 이들을 같은 brief 단위로 묶는 안정적인 artifact anchor가 아직 없습니다

### 3. 다른 후보들이 모두 이 anchor를 먼저 필요로 합니다
- corrected outcome 저장은 어떤 원본 brief를 수정한 것인지 먼저 알아야 합니다
- approval trail artifact linkage는 같은 brief를 가리키는 stable key가 먼저 있어야 합니다
- eval-ready eligibility marker는 어떤 trace chain이 같은 artifact인지 먼저 알아야 합니다

## First Slice Contract

### 목표
- `grounded brief` 1개를 현재 저장소의 여러 raw trace surface에서 같은 id로 따라갈 수 있게 만듭니다

### 비목표
- separate artifact store
- corrected outcome persistence
- approval reject / reissue reason normalization
- review queue
- user-level memory
- 새 UI surface

### 최소 필드

#### Assistant message
- `artifact_id`
- `artifact_kind = grounded_brief`

#### Approval record / approval payload
- `artifact_id`

#### Task-log detail
- `artifact_id` when applicable

원칙:
- schema를 크게 다시 짜지 않습니다
- additive optional field로 시작합니다
- 현재 `message_id`를 대체하지 않습니다

### 기존 trace 재사용 포인트
- assistant message를 첫 raw snapshot surface로 그대로 사용합니다
- pending approval record를 현재 approval linkage surface로 그대로 사용합니다
- append-only task log를 현재 audit linkage surface로 그대로 사용합니다
- feedback는 계속 `message_id`로 입력받되, 같은 assistant message가 가진 `artifact_id`로 역연결 가능해야 합니다

### 예상 변경 파일
- `core/agent_loop.py`
- `storage/session_store.py`
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

### UI/UX 영향
- 첫 슬라이스는 UI 확대 없이 들어가야 합니다
- 기존 browser flow, approval card, feedback flow는 그대로 둡니다
- 브라우저 e2e를 새로 늘리기보다 service/smoke regression으로 시작합니다

### approval / evidence / feedback 연결 방식
- approval:
  - 같은 `artifact_id`가 approval request와 outcome trace에 붙어야 합니다
- evidence:
  - 기존 assistant message의 `evidence`와 `summary_chunks`를 그대로 첫 snapshot surface로 재사용합니다
- feedback:
  - 기존 `response_feedback_recorded` 흐름은 유지하되, 대상 assistant message의 `artifact_id`와 연결 가능해야 합니다

## 이 슬라이스가 끝나면 바로 가능해지는 것

- 같은 `grounded brief`를 message, approval, write, feedback trace에서 안정적으로 추적
- later slice에서 corrected outcome이나 approval trail을 붙일 stable key 확보
- service fixture 수준에서 artifact linkage regression 추가
- eval-ready artifact의 core chain 중 첫 anchor를 구현 쪽에서 갖출 준비

## 이 슬라이스 후에도 여전히 불가능한 것

- eval-ready artifact 완성
- corrected output pair 저장
- approval reject / reissue reason taxonomy 저장
- reviewed vs unreviewed candidate 구분
- rollbackable reviewed memory
- user-level durable memory

## Verification Plan

### 어디부터 시작할지
- service / smoke regression부터 시작합니다
- e2e는 첫 슬라이스의 우선순위가 아닙니다

### 첫 테스트 방향

#### `tests/test_web_app.py`
- summarize file response가 session payload에서 `artifact_id`를 유지하는지 확인
- approval request가 response/session payload에서 같은 `artifact_id`를 유지하는지 확인
- feedback submission 이후에도 대상 assistant message가 같은 `artifact_id`를 유지하는지 확인

#### `tests/test_smoke.py`
- approval-backed save 흐름에서 같은 `artifact_id`가 approval / write path까지 이어지는지 확인
- reissue path가 있어도 artifact anchor는 유지되고 approval id만 바뀌는지 확인

### 문서 동기화 범위
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

### Migration / Backward-Compat Risk
- 낮은 편입니다
- 이유:
  - assistant message는 optional field 추가로 시작 가능
  - pending approval도 dict payload 확장으로 대응 가능
  - task log는 append-only detail 확장으로 대응 가능

### Rollback-Friendly 구현 순서
1. assistant message에 `artifact_id`, `artifact_kind` 추가
2. approval request / outcome / write-note event에 같은 `artifact_id` 연결
3. session / response serialization 노출
4. focused service / smoke regression 추가

## 이번 라운드에서 일부러 하지 않는 것

- corrected outcome store
- review queue
- durable candidate store
- user-level memory
- operator surface 선택
- category별 recurrence tuning
- approval-backed save category tuning

## OPEN QUESTION

1. `response_feedback_recorded`에서 `artifact_id`를 직접 log detail에 남길지, message lookup으로만 복원할지?
2. first slice에서 pending approval public payload까지 `artifact_id`를 노출할지, session trace에만 먼저 둘지?
3. additive optional field만으로 충분한지, later slice에서 별도 artifact store가 언제 필요한지?
4. review / rollback UI가 생긴 뒤 어떤 regression부터 e2e로 올릴지?
