# docs: root reviewed-memory aggregate lifecycle summary truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 60, 230): stop-apply/reversal/conflict-visibility 요약 확장
- `docs/ACCEPTANCE_CRITERIA.md` — 3곳(line 1358 외): stop-apply/reversal/conflict-visibility 요약 확장
- `docs/ARCHITECTURE.md` — 4곳(line 80, 1164, 1298, 1328): stop-apply/reversal/conflict-visibility 요약 확장
- `docs/MILESTONES.md` — 1곳(line 340): stop-apply/reversal/conflict-visibility 요약 확장
- `docs/TASK_BACKLOG.md` — 2곳(line 147, 717): stop-apply/reversal/conflict-visibility 요약 확장

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 압축된 요약에서 stop-apply, reversal, conflict-visibility 세부 사항이 누락:
  1. stop-apply: `apply_result.result_stage = effect_stopped` 누락
  2. reversal: `apply_result.result_stage = effect_reversed`, `reversed_at` 누락
  3. conflict-visibility: `transition_action`, `source_apply_transition_ref`, `conflict_entries`, `conflict_entry_count` 누락
- 근거 앵커: `app/handlers/aggregate.py:467`/`470`/`529`/`532`/`639`/`643`-`645`

## 핵심 변경
- 3개 수술적 replace_all 적용:
  1. "`record_stage` to `stopped` and removes the effect" → "`record_stage` to `stopped`, sets `apply_result.result_stage` to `effect_stopped`, and removes the effect from `reviewed_memory_active_effects`" (7곳)
  2. "`record_stage` to `reversed`; conflict-visibility" → "`record_stage` to `reversed`, sets `apply_result.result_stage` to `effect_reversed`, and adds `reversed_at`; conflict-visibility" (7곳)
  3. "records a `reviewed_memory_conflict_visibility_record` with `record_stage = conflict_visibility_checked`" → "creates a separate `reviewed_memory_conflict_visibility_record` with `transition_action = future_reviewed_memory_conflict_visibility`, `record_stage = conflict_visibility_checked`, `source_apply_transition_ref`, evaluated `conflict_entries`, and `conflict_entry_count`" (12곳)
- emission/apply/confirm/stop/reversal/conflict 순서 유지
- 이미 확장된 인스턴스(PRODUCT_SPEC:1537, MILESTONES:45, NEXT_STEPS:419 등)는 영향 없음

## 검증
- `git diff --stat` — 5 files changed, 12 insertions(+), 12 deletions(-)
- 압축 패턴 3종 모두 grep 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 root docs의 aggregate lifecycle summary 진실 동기화 완료
