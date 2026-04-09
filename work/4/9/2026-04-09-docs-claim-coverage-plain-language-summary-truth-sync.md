# docs: current-product web-investigation claim-coverage plain-language summary truth sync

## 변경 파일
- `AGENTS.md` — 1곳(line 47)
- `CLAUDE.md` — 1곳(line 26)
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 1곳(line 24)
- `docs/ARCHITECTURE.md` — 3곳(line 11, 135, 1370)
- `docs/PRODUCT_PROPOSAL.md` — 1곳(line 26)
- `docs/project-brief.md` — 1곳(line 15)
- `docs/PRODUCT_SPEC.md` — 1곳(line 155)

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 9곳에서 "focus-slot reinvestigation explanation"으로 축약하여 shipped "dedicated plain-language" qualifier와 "(reinforced / regressed / still single-source / still unresolved)" 상태 목록 누락
- 근거 앵커: `README.md:79`, `docs/PRODUCT_SPEC.md:107`, `docs/PRODUCT_SPEC.md:361`, `docs/NEXT_STEPS.md:21`

## 핵심 변경
- "focus-slot reinvestigation explanation" → "dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved)"
- PRODUCT_SPEC:155는 parenthetical 내 짧은 form → "dedicated plain-language ... covering reinforced / regressed / still single-source / still unresolved"
- 기존 claim-coverage panel 구조(status tags, actionable hints) 유지

## 검증
- `git diff --stat` — 7 files changed, 9 insertions(+), 9 deletions(-)
- generic "and focus-slot reinvestigation explanation" (줄 끝) — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 claim-coverage plain-language summary 동기화 완료
