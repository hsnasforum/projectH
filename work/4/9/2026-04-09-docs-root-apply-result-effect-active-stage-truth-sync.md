# docs: root reviewed-memory apply-result effect-active stage truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 3곳(line 60, 230, 1537)
- `docs/ACCEPTANCE_CRITERIA.md` — 3곳(line 923, 930, 1358)
- `docs/ARCHITECTURE.md` — 4곳(line 80, 1164, 1298, 1328)
- `docs/MILESTONES.md` — 2곳(line 45, 340)
- `docs/NEXT_STEPS.md` — 2곳(line 16, 419)
- `docs/TASK_BACKLOG.md` — 2곳(line 147, 717)

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 16곳 모두 `결과 확정` 단계에서 `apply_result.result_stage = result_recorded_effect_pending`을 생성한다고 기술
- 실제 구현(`app/handlers/aggregate.py:399`): confirm 단계에서 바로 `ResultStage.EFFECT_ACTIVE`를 기록
- `result_recorded_effect_pending` 중간 단계는 현재 코드에 존재하지 않음
- confirm 즉시 `reviewed_memory_active_effects`에 추가되고 future response에 `[검토 메모 활성]` prefix가 적용됨

## 핵심 변경
- 전체 root docs 6개 파일에서 `result_stage = result_recorded_effect_pending` → `result_stage = effect_active` 일괄 교체 (16곳)
- 후속 서술("the memory effect on future responses is now active (`result_stage = effect_active`)")과의 일관성 확보
- stop-apply (`effect_stopped`), reversal (`effect_reversed`) 등 후속 stage 서술은 이미 정확하므로 변경 없음
- emission/apply/confirm/stop/reversal/conflict 순서 유지
- literal id, 기존 계약 구조 변경 없음

## 검증
- `git diff --stat` — 6 files changed, 16 insertions(+), 16 deletions(-)
- `rg 'result_stage = result_recorded_effect_pending' docs/` — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 root docs의 apply-result stage enum 진실 동기화 완료
