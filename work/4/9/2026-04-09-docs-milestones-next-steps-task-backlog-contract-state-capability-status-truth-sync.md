# docs: MILESTONES NEXT_STEPS TASK_BACKLOG reviewed-memory contract-state capability-status truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 193): contract state machine / satisfaction booleans later 문구 수정
- `docs/NEXT_STEPS.md` — 1곳(line 536): rollback/disable contract state machine later 문구 수정
- `docs/TASK_BACKLOG.md` — 1곳(line 306): contract state machine / satisfaction booleans later 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 세 라인 모두 "state machines and satisfaction booleans remain later" 또는 "state machines remain later"로 적어, capability-status path (`unblocked_all_required`)와 apply/stop-apply/reversal/conflict-visibility lifecycle이 아직 미출하인 것처럼 프레이밍
- 실제 shipped truth: capability-status path는 이미 materialized, apply lifecycle은 이미 출하, contract objects는 read-only로 출하
- 정확한 later 범위: per-precondition satisfaction booleans와 repeated-signal promotion만 later
- 근거 앵커: `docs/PRODUCT_SPEC.md:1473`/`1474`, `app/serializers.py:1515`, `app/handlers/aggregate.py:393`/`469`/`531`

## 핵심 변경
- MILESTONES:193 — "(state machines and satisfaction booleans remain later)" → "the capability-status path is materialized (`unblocked_all_required`) while per-precondition satisfaction booleans and repeated-signal promotion remain later"
- NEXT_STEPS:536 — "while their state machines remain later" → "and the capability-status path plus apply / stop-apply / reversal / conflict-visibility lifecycle are already shipped above them; per-precondition satisfaction booleans and repeated-signal promotion remain later"
- TASK_BACKLOG:306 — "while their state machines and satisfaction booleans remain later" → "the capability-status path is materialized (`unblocked_all_required`) while per-precondition satisfaction booleans and repeated-signal promotion remain later"
- contract objects가 read-only라는 보수적 의미 보존
- promotion-ineligible, cross-session counting later 등 기존 제약 유지

## 검증
- `git diff -- docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md` — 3줄 변경 확인
- `rg` stale 문구 검색 — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — MILESTONES/NEXT_STEPS/TASK_BACKLOG의 contract-state capability-status 진실 동기화 완료
