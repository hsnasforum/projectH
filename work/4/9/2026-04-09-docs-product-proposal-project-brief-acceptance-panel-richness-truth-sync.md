# docs: PRODUCT_PROPOSAL project-brief ACCEPTANCE_CRITERIA remaining panel richness truth sync

## 변경 파일
- `docs/PRODUCT_PROPOSAL.md` — 1곳(line 65): claim-coverage panel에 source role + fact-strength bar 추가
- `docs/project-brief.md` — 1곳(line 89): claim-coverage panel에 source role + fact-strength bar 추가
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 32): claim-coverage에 source role + reinvestigation explanation 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 3곳에서 claim-coverage panel 요약이 "source role with trust level labels"와 "color-coded fact-strength summary bar" 누락
- ACCEPTANCE_CRITERIA:32에서 "dedicated plain-language focus-slot reinvestigation explanation" 누락
- 근거 앵커: `README.md:79`, `docs/PRODUCT_SPEC.md:338`/`361`

## 핵심 변경
- PRODUCT_PROPOSAL:65, project-brief:89 — "status tags, actionable hints, and dedicated plain-language" → "status tags, actionable hints, source role with trust level labels, color-coded fact-strength summary bar, and dedicated plain-language"
- ACCEPTANCE_CRITERIA:32 — source role + reinvestigation explanation 추가

## 검증
- `git diff --stat` — 3 files changed, 3 insertions(+), 3 deletions(-)
- unenriched — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음
