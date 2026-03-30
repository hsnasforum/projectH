# 2026-03-29 reviewed-memory post-cleanup compatibility-note contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-planning-target-normalization-contract.md`
- `plandoc/2026-03-29-reviewed-memory-duplicated-target-cleanup-contract.md`
- `plandoc/2026-03-29-reviewed-memory-post-cleanup-compatibility-note-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-post-cleanup-compatibility-note-contract.md`

## 사용 skill
- `mvp-scope`: shared-ref-only current truth와 post-cleanup aftercare wording을 current MVP 범위 안에서 분리했습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log` replay가 compatibility-note basis처럼 읽히지 않는 경계를 다시 확인했습니다.
- `doc-sync`: root docs와 relevant `plandoc`를 current shared-ref-only truth에 맞춰 함께 정리했습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg` 결과만 기준으로 이번 문서 round를 닫았습니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 계약 정리와 남은 리스크를 기록했습니다.

## 변경 이유
- 직전 closeout에서 shared-ref-only cleanup은 이미 shipped 되었지만, cleanup 뒤 one short compatibility note를 docs와 `/work`에 한 라운드 더 둘지 여부는 아직 exact contract가 없었습니다.
- 이 질문이 열려 있으면 removed echo fields가 라운드마다 historical note와 current truth 사이에서 흔들려 읽힐 수 있어, aftercare wording을 먼저 닫는 편이 더 정직했습니다.

## 핵심 변경
- post-cleanup compatibility note는 `Option B`로 고정했습니다:
  - shared-ref-only current truth로 바로 정리
  - extra compatibility note 없음
  - removed echo fields를 current schema처럼 다시 쓰지 않음
- root docs는 shared-ref-only planning-target truth만 current contract로 남기고, compatibility-note open question을 제거했습니다.
- `plandoc/2026-03-29-reviewed-memory-post-cleanup-compatibility-note-contract.md`를 추가해:
  - compatibility note 없음
  - ordinary `/work` historical context만 허용
  - next slice를 `one emitted-transition-record contract only`로 고정했습니다.
- 기존 planning-target 관련 `plandoc` 두 개도 같은 결정과 next-slice wording으로 동기화했습니다.

## 검증
- `git diff --check`
- `rg -n "compatibility note|shared-ref-only|reviewed_memory_planning_target_ref|blocked_all_required|unblocked_all_required|current truth|operator handoff round" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-29-reviewed-memory-post-cleanup-compatibility-note-contract.md plandoc/2026-03-29-reviewed-memory-duplicated-target-cleanup-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - shared-ref-only cleanup은 끝났지만, post-cleanup aftercare wording을 한 라운드 더 둘지 여부는 아직 닫히지 않았습니다.
- 이번 라운드에서 해소한 리스크:
  - extra compatibility note를 두지 않는다고 문서로 고정했습니다.
  - removed echo fields가 historical wording 때문에 current schema처럼 다시 읽히는 경로를 줄였습니다.
- 여전히 남은 리스크:
  - emitted transition record의 first exact shape는 아직 later contract입니다.
  - reviewed-memory store / apply / repeated-signal promotion / cross-session counting / user-level memory는 계속 later layer입니다.
