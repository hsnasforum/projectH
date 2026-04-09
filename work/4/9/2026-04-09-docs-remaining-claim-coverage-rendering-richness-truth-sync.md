# docs: PRODUCT_SPEC README NEXT_STEPS MILESTONES TASK_BACKLOG remaining claim-coverage rendering richness truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 107, 361): source role with trust level labels 추가
- `README.md` — 1곳(line 137): smoke description에 source role + fact-strength bar 추가
- `docs/NEXT_STEPS.md` — 1곳(line 22): smoke description에 source role + fact-strength bar 추가
- `docs/MILESTONES.md` — 1곳(line 41): smoke description에 source role + fact-strength bar 추가
- `docs/TASK_BACKLOG.md` — 1곳(line 26): smoke description에 source role + fact-strength bar 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- PRODUCT_SPEC:107, 361에서 "source role with trust level labels" 누락
- README:137, NEXT_STEPS:22, MILESTONES:41, TASK_BACKLOG:26의 smoke/rendering description에서 "source role with trust level labels"와 "color-coded fact-strength summary bar" 누락

## 핵심 변경
- 5개 파일 6곳에 "source role with trust level labels" 및/또는 "color-coded fact-strength summary bar" 추가
- 기존 claim tags, actionable hints, reinvestigation explanation 유지

## 검증
- `git diff --stat` — 5 files changed, 6 insertions(+), 6 deletions(-)
- enriched lines — 10건 across 5 files
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음
