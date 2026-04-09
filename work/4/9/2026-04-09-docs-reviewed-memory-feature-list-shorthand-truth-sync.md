# docs: remaining reviewed-memory feature-list shorthand truth sync

## 변경 파일
- `AGENTS.md` — 1곳(line 48): "reviewed-memory active-effect path (apply / stop-apply / reversal / conflict-visibility)" → full lifecycle
- `CLAUDE.md` — 1곳(line 27): 동일 패턴 교체
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 1곳(line 25): 동일 패턴 교체
- `docs/project-brief.md` — 1곳(line 15): "reviewed-memory active-effect path" → full lifecycle
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 25): 동일 패턴 교체

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 5곳에서 "reviewed-memory active-effect path (apply / stop-apply / reversal / conflict-visibility)" shorthand이 이전 라운드에서 교체된 full lifecycle wording과 불일치
- 근거 앵커: `docs/ARCHITECTURE.md:15`, `docs/MILESTONES.md:11`, `docs/PRODUCT_PROPOSAL.md:95`, `docs/TASK_BACKLOG.md:8`

## 핵심 변경
- 5개 파일 모두 "reviewed-memory active-effect path (apply / stop-apply / reversal / conflict-visibility)" → "emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility"
- project-brief.md는 parenthetical 없는 standalone variant로 별도 처리

## 검증
- `git diff --stat` — 5 files changed, 5 insertions(+), 5 deletions(-)
- `rg 'reviewed-memory active-effect path'` — 5개 대상 파일 모두 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 reviewed-memory feature-list shorthand 동기화 완료
