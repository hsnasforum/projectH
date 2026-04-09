# docs: reviewed-memory lifecycle shorthand residual truth sync

## 변경 파일
- `README.md` — 2곳(line 3, 12): active-effect path shorthand → full lifecycle
- `AGENTS.md` — 1곳(line 5): active-effect path shorthand → full lifecycle
- `CLAUDE.md` — 1곳(line 5): active-effect path shorthand → full lifecycle
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 1곳(line 1): active-effect path shorthand → full lifecycle
- `docs/PRODUCT_SPEC.md` — 4곳(line 6, 18, 27, 970): active-effect path shorthand → full lifecycle
- `docs/PRODUCT_PROPOSAL.md` — 3곳(line 6, 16, 25): active-effect path shorthand → full lifecycle
- `docs/project-brief.md` — 2곳(line 5, 14): active-effect path shorthand → full lifecycle
- `docs/MILESTONES.md` — 1곳(line 6): active-effect path shorthand → full lifecycle
- `docs/NEXT_STEPS.md` — 1곳(line 19): active-effect path shorthand → full lifecycle
- `docs/ARCHITECTURE.md` — 2곳(line 5, 10): active-effect path shorthand → full lifecycle
- `docs/TASK_BACKLOG.md` — 1곳(line 5): active-effect path shorthand → full lifecycle
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 186): active-effect path shorthand → full lifecycle

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 20곳에서 shipped reviewed-memory first slice를 "active-effect path"로만 축약하여 stop-apply, reversal, conflict-visibility 누락
- shipped truth: emitted/apply/result/active-effect path + stop-apply + reversal + conflict-visibility 전체 출하
- 근거 앵커: `docs/ARCHITECTURE.md:15`, `docs/MILESTONES.md:11`, `docs/PRODUCT_PROPOSAL.md:95`에 이미 full form 존재

## 핵심 변경
- "review queue, aggregate apply trigger, and active-effect path" → "review queue, aggregate apply trigger, emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility" (replace_all 12개 파일)
- "reviewed-memory active-effect path" standalone → "emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility" (NEXT_STEPS, ACCEPTANCE_CRITERIA)
- Korean variant 포함 (README, PROJECT_CUSTOM_INSTRUCTIONS)

## 검증
- `git diff --stat` — 12 files changed, 20 insertions(+), 20 deletions(-)
- `rg 'and active-effect path'` — active docs 0건 (work/verify notes만 잔여)
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 reviewed-memory lifecycle shorthand 동기화 완료
