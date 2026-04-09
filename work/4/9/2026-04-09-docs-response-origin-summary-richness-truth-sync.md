# docs: response-origin summary richness truth sync

## 변경 파일
- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `docs/project-brief.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md` — 각 1곳

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 8곳에서 "response origin badge(s)" / "response origin 배지"로 축약하여 shipped answer-mode badge, source-role trust labels, verification strength tags 누락
- 근거 앵커: `README.md:62`, `docs/PRODUCT_SPEC.md:105`

## 핵심 변경
- "response origin badge" → "response origin badge with separate answer-mode badge for web investigation, source-role trust labels, and verification strength tags in origin detail"
- 8개 파일 8줄 교체

## 검증
- `git diff --stat` — 8 files changed, 8 insertions(+), 8 deletions(-)
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음
