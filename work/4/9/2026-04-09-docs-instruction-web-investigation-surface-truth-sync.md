# docs: AGENTS CLAUDE PROJECT_CUSTOM_INSTRUCTIONS web-investigation current-surface truth sync

## 변경 파일
- `AGENTS.md` — 2곳(line 43-45): web investigation 요약 확장
- `CLAUDE.md` — 2곳(line 22-24): web investigation 요약 확장
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 2곳(line 20-22): web investigation 요약 확장

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 3개 instruction docs의 web investigation 요약이 "permission-gated web investigation with local JSON history" + "claim coverage / verification state"로 압축되어 있어 shipped surface 미반영:
  - disabled/approval/enabled per session
  - in-session reload and history-card badges (answer-mode, verification-strength, source-role trust)
  - entity-card / latest-update answer-mode distinction with separate verification labels
  - claim-coverage panel with status tags, actionable hints, and focus-slot reinvestigation explanation
- 근거 앵커: `docs/NEXT_STEPS.md:18`, `docs/project-brief.md:15`, `docs/PRODUCT_PROPOSAL.md:26`

## 핵심 변경
- 3개 파일 모두 동일한 패턴 적용:
  - "permission-gated web investigation with local JSON history" → "(disabled/approval/enabled per session) with local JSON history, in-session reload, and history-card badges (answer-mode, verification-strength, source-role trust)"
  - "claim coverage / verification state" → "entity-card / latest-update answer-mode distinction" + "claim-coverage panel with status tags, actionable hints, and focus-slot reinvestigation explanation"
- web investigation을 secondary mode로 프레이밍하는 기존 맥락 유지

## 검증
- `git diff --stat` — 3 files changed, 9 insertions(+), 6 deletions(-)
- `rg` — 4개 surface 항목 3개 파일 모두에서 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- GEMINI.md에 동일 패턴 잔여 가능 — 현재 scope 외
