# docs: AGENTS CLAUDE PROJECT_CUSTOM_INSTRUCTIONS web-investigation strong-badge downgrade truth sync

## 변경 파일
- `AGENTS.md` — 1곳(line 46): entity-card strong-badge downgrade 추가
- `CLAUDE.md` — 1곳(line 25): entity-card strong-badge downgrade 추가
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 1곳(line 23): entity-card strong-badge downgrade 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 3개 instruction docs의 entity-card / latest-update answer-mode distinction 줄에 shipped entity-card strong-badge downgrade nuance 누락
- shipped truth: entity-card verification badge가 cross-verified status가 없을 때 strong에서 downgrade됨
- 근거 앵커: `README.md:78`, `docs/PRODUCT_SPEC.md:155`, `docs/ACCEPTANCE_CRITERIA.md:41`, `app/static/app.js:2276`

## 핵심 변경
- 3개 파일 모두 "with separate verification labels" → "with separate verification labels and entity-card strong-badge downgrade"

## 검증
- `git diff --stat` — 3 files changed, 3 insertions(+), 3 deletions(-)
- `rg 'strong-badge downgrade'` — 3개 파일 모두 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — instruction docs의 entity-card strong-badge downgrade 동기화 완료
