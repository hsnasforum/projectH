# docs: current-product web-investigation badge-and-panel richness truth sync

## 변경 파일
- `AGENTS.md` — 1곳(line 45)
- `CLAUDE.md` — 1곳(line 24)
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 1곳(line 22)
- `docs/ARCHITECTURE.md` — 3곳(line 11, 137, 1372)
- `docs/PRODUCT_PROPOSAL.md` — 2곳(line 26, 63)
- `docs/project-brief.md` — 2곳(line 15, 87)
- `docs/NEXT_STEPS.md` — 1곳(line 21)
- `docs/TASK_BACKLOG.md` — 1곳(line 24)

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 12곳에서 "history-card badges (answer-mode, verification-strength, source-role trust)"로 축약하여 shipped color-coded badge 세부사항 누락
- 근거 앵커: `README.md:78`("answer-mode badges, color-coded verification-strength badges ... color-coded source-role trust badges")

## 핵심 변경
- "history-card badges (answer-mode, verification-strength, source-role trust)" → "history-card badges (answer-mode badges, color-coded verification-strength badges, color-coded source-role trust badges)"
- TASK_BACKLOG:24 — "history-card answer-mode / verification-strength / source-role trust badges" → "history-card badges: answer-mode badges, color-coded verification-strength badges, color-coded source-role trust badges"

## 검증
- `git diff --stat` — 8 files changed, 12 insertions(+), 12 deletions(-)
- old shorthand — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 web-investigation badge-and-panel richness 동기화 완료
