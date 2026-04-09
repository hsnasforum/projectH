# docs: remaining web-investigation surface richness truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 1곳(line 154): history-card badge shorthand → color-coded 확장
- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md` — 각 1곳: claim-coverage panel에 source role + fact-strength bar 추가
- `docs/ARCHITECTURE.md` — 3곳: claim-coverage panel에 source role + fact-strength bar 추가
- `docs/PRODUCT_PROPOSAL.md` — 1곳, `docs/project-brief.md` — 1곳, `docs/NEXT_STEPS.md` — 1곳: 동일 패턴
- `docs/TASK_BACKLOG.md` — 1곳, `docs/ACCEPTANCE_CRITERIA.md` — 1곳: 동일 패턴 (variant form)

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- PRODUCT_SPEC:154 — "history-card display (answer-mode, verification-strength, source-role trust badges)" → color-coded qualifier 누락
- 12곳의 claim-coverage panel 요약에서 "source role with trust level labels"와 "color-coded fact-strength summary bar" 누락
- 근거 앵커: `README.md:78-79`, `docs/PRODUCT_SPEC.md:338-339`, `docs/PRODUCT_SPEC.md:359-361`

## 핵심 변경
- PRODUCT_SPEC:154 — history-card display → history-card badges with color-coded qualifiers
- 12곳 — "status tags, actionable hints, and dedicated plain-language" → "status tags, actionable hints, source role with trust level labels, color-coded fact-strength summary bar, and dedicated plain-language"

## 검증
- `git diff --stat` — 10 files changed, 12 insertions(+), 12 deletions(-)
- enriched lines — 12건, unenriched — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — web-investigation surface richness 동기화 완료
