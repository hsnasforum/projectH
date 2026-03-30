# 2026-03-27 session-local-memory-signal-contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-session-local-memory-signal-contract.md`
- `work/3/27/2026-03-27-session-local-memory-signal-contract.md`

## 사용 skill
- `mvp-scope`
  - current shipped trace foundation, next memory slice, long-term durable memory를 섞지 않고 단계별로 다시 정리하는 데 사용했습니다.
- `doc-sync`
  - current implementation truth와 next slice 계약이 root docs와 `plandoc`에서 같은 경계를 유지하도록 맞췄습니다.
- `release-check`
  - 실제로 실행한 문서 검증만 closeout에 반영하고, 미실행 테스트는 남겨 두기 위해 사용했습니다.
- `work-log-closeout`
  - 이번 설계 라운드의 변경 파일, 권고, 검증, 남은 리스크를 `/work` 표준 형식으로 정리했습니다.

## 변경 이유
- 직전 closeout 기준으로 shipped reject-note surface와 long-history smoke는 이미 안정됐고, manual clear UX도 당장 열지 않기로 고정됐습니다.
- 다음 라운드는 UI를 더 넓히기보다 내부 기반으로 돌아가야 했고, current shipped explicit correction / reject / approval / save trace를 어떤 최소 session-local signal로 묶을 수 있는지 먼저 문서 계약으로 고정할 필요가 있었습니다.

## 핵심 변경
- first `session_local` memory signal을 문서로 정의했습니다.
  - one grounded-brief artifact inside the current session에 대한 read-only working summary
  - `artifact_id` + `source_message_id`로 anchor
  - content / approval / save 축을 분리한 thin projection
- canonical source of truth를 current persisted session state로 고정했습니다.
  - original grounded-brief source message는 content axis canonical source
  - approval-linked session messages / pending approvals는 approval axis canonical source
  - saved response messages plus save linkage fields는 save axis canonical source
  - task-log는 first slice에서 audit/replay 보조축일 뿐 canonical source가 아님
- first signal의 범위를 좁게 고정했습니다.
  - current persisted session state에서 truthfully recoverable 한 explicit trace만 포함
  - inferred preference statement, cross-artifact aggregate, durable candidate promotion, user-level memory application은 제외
  - later correction/save로 source message에서 이미 clear된 superseded reject/note는 first signal에서 빠질 수 있고, audit log에만 남을 수 있다고 명시
- 최종 권고를 1개로 고정했습니다.
  - source-message 기반 read-only `session_local_memory_signal` projection field 추가
  - separate memory store 없이 response/session serialization에서 계산하는 것이 first slice로 가장 작다고 정리
- 관련 문서의 next priorities도 같이 조정했습니다.
  - `NEXT_STEPS`, `MILESTONES`, `TASK_BACKLOG`에서 다음 구현 우선순위를 session-local projection slice로 옮겼습니다.

## 검증
- `rg -n "session-local|memory signal|session_local_memory_signal|corrected_outcome|content_reason_record|approval_reason_record|save_content_source|durable_candidate|user-level memory" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-session-local-memory-signal-contract.md`
- `git diff --check`

## 남은 리스크
- 이전 closeout에서 이어받은 “다음은 UI widening보다 내부 기반 쪽으로 가야 한다”는 방향은 이번 라운드에서 문서 계약 수준으로 구체화했습니다.
- 이번 라운드에서 해소한 리스크:
  - first session-local memory signal의 canonical unit, source-of-truth, projection boundary, first implementation slice가 불명확하던 상태를 정리했습니다.
- 이번 라운드에서 의도적으로 범위 밖에 둔 것:
  - actual session-local memory implementation
  - review queue / durable candidate / user-level memory 구현
  - task-log replay helper 구현
- 여전히 남은 리스크:
  - first signal이 current state only로 충분한지, 아니면 superseded content reject까지 later replay helper로 끌어와야 하는지는 다음 설계 또는 구현 slice에서 다시 좁혀야 합니다.
  - first slice에서 source-message serialization에만 붙일지, top-level response mirror까지 같이 낼지는 implementation round에서 더 잘라야 합니다.
