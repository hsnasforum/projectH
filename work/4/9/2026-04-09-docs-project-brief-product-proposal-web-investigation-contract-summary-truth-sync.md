# docs: project-brief PRODUCT_PROPOSAL web-investigation current-contract summary truth sync

## 변경 파일
- `docs/project-brief.md` — 1곳(line 15): top-level web investigation 요약 확장
- `docs/PRODUCT_PROPOSAL.md` — 1곳(line 26): Facts web investigation 요약 확장

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- project-brief.md:15 — history-card badges만 기재, entity-card / latest-update distinction, strong-badge downgrade, claim-coverage panel detail 누락
- PRODUCT_PROPOSAL.md:26 — entity-card / latest-update distinction 언급하지만 separate verification labels, strong-badge downgrade, claim-coverage panel detail (status tags, hints, reinvestigation explanation) 누락
- 같은 파일의 하위 세부 목록(project-brief:83-85, PRODUCT_PROPOSAL:63-65)과 ARCHITECTURE:11에는 이미 full detail 반영됨

## 핵심 변경
- project-brief:15 — "history-card badges" → "history-card badges (answer-mode, verification-strength, source-role trust), entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade, and a claim-coverage panel with status tags, actionable hints, and focus-slot reinvestigation explanation"
- PRODUCT_PROPOSAL:26 — "history-card badges, entity-card / latest-update answer-mode distinction, and claim-coverage panel" → "history-card badges (answer-mode, verification-strength, source-role trust), entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade, and a claim-coverage panel with status tags, actionable hints, and focus-slot reinvestigation explanation"
- PRODUCT_PROPOSAL:69 Core Product Boundaries 라인은 boundary 요약 수준으로 적절하여 변경하지 않음

## 검증
- `git diff --stat` — 2 files changed, 2 insertions(+), 2 deletions(-)
- `rg` — history-card badges, entity-card/latest-update, strong-badge downgrade, claim-coverage panel 모두 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — project-brief/PRODUCT_PROPOSAL의 top-level web-investigation contract summary 진실 동기화 완료
