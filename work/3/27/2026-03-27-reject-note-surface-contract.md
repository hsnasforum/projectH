# 2026-03-27 reject-note surface contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-reject-note-surface-contract.md`
- `work/3/27/2026-03-27-reject-note-surface-contract.md`

## 사용 skill
- `frontend-skill`: response-card action separation을 기준으로, optional reject-note surface를 approval box 밖의 작은 inline note surface로만 열도록 설계 범위를 좁혔습니다.
- `doc-sync`: current shipped reject truth, next reject-note target, roadmap 우선순위를 제품 문서와 backlog 문서에 맞춰 동기화했습니다.
- `release-check`: 실제 실행한 검증만 closeout에 반영하고, 문서-only 라운드임을 기준으로 미실행 테스트를 주장하지 않도록 점검했습니다.
- `work-log-closeout`: 이번 설계 라운드의 변경 범위, 실행한 검증, 남은 리스크를 `/work` 표준 형식으로 정리했습니다.

## 변경 이유
- 직전 closeout에서는 shipped `내용 거절` path의 Playwright smoke까지 올라갔지만, optional `reason_note` input surface는 여전히 “truthful input surface가 있을 때만 가능”한 상태로 남아 있었습니다.
- 현재 구현은 fixed-label `explicit_content_rejection`만 기록하고 `content_reason_record`는 latest reject state에서만 유지하므로, note를 나중에 붙일 경우의 UX / trace / stale clearing 계약을 먼저 문서로 좁힐 필요가 있었습니다.
- 이번 라운드는 코드 변경 없이, current shipped fixed-label baseline과 next optional note surface를 분리해서 정리하는 문서 작업으로 제한했습니다.

## 핵심 변경
- optional reject-note surface의 최소 UX를 고정했습니다:
  - same response-card `내용 판정` 구역
  - short inline textarea + explicit secondary submit action
  - latest outcome이 `rejected`일 때만 노출/편집 가능
  - approval surface / correction editor / corrected-save bridge와 분리
- fixed-label baseline과의 관계를 고정했습니다:
  - `내용 거절`만 눌러도 지금처럼 `explicit_content_rejection`은 즉시 기록됨
  - note는 baseline의 optional 보강이며, note 부재가 reject verdict를 불완전하게 만들지 않음
- trace 계약을 고정했습니다:
  - same source message의 existing `content_reason_record.reason_note`를 in-place update
  - `content_reason_record.recorded_at`는 latest note update time으로 refresh
  - `corrected_outcome.recorded_at`는 reject verdict 시각으로 유지
  - later correction/save supersession 시 stale `content_reason_record`와 note가 함께 clear
  - task-log는 approval trace와 별도로 one dedicated content-linked note event를 추가하는 방향으로 정리
- roadmap 문구는 “later optional note”에서 한 단계 더 나아가, optional reject-note surface를 next implementation slice로 권고하고 richer reject taxonomy는 더 뒤로 미루는 방향으로 정리했습니다.

## 검증
- 실행함: `rg -n "reason_note|content_reason_record|내용 거절|explicit_content_rejection|approval reject|corrected-save" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-reject-note-surface-contract.md`
- 실행함: `git diff --check`
- 미실행:
  - 제품 코드 검증
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크는 “reject note UX와 richer reject labels는 아직 truthful input surface가 없으므로 구현하지 않았다”는 점이었고, 이번 라운드에서는 그중 reject-note surface contract 부재를 해소했습니다.
- 이번 라운드에서 해소한 리스크는 fixed-label baseline과 optional note가 충돌하지 않도록 하는 UX / trace / stale-note clearing 계약의 부재였습니다.
- 여전히 남은 리스크는 이 계약이 아직 코드와 테스트로 구현되지는 않았다는 점입니다.
- 특히 same rejected state 안에서 blank note submit을 no-op로 볼지 explicit clear로 볼지, note surface를 항상 펼칠지 작은 secondary affordance 뒤에 열지는 구현 slice에서 다시 결정해야 합니다.
- richer reject labels, review queue, user-level memory, operator surface는 이번 라운드에서도 범위 밖으로 남겼습니다.
