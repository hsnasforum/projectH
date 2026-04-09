# docs: AGENTS CLAUDE current product slice response-surface truth sync

## 변경 파일
- `AGENTS.md` — 3곳(line 35-37, 40): evidence/source 확장, structured search result preview/source-type labels/applied-preferences badge 추가
- `CLAUDE.md` — 4곳(line 14-16, 19): "summary-range panel" → "summary span / applied-range panel", structured search result preview/source-type labels/applied-preferences badge 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- AGENTS.md와 CLAUDE.md의 Current Product Slice / Current implemented focus 목록에 shipped browser response surface 3종 누락:
  - structured search result preview panel
  - summary source-type labels (`문서 요약` / `선택 결과 요약`)
  - applied-preferences badge (`선호 N건 반영`)
- CLAUDE.md에 "summary-range panel" 구명칭 잔여
- 이전 라운드에서 모든 root docs와 non-core docs 동기화 완료; instruction docs만 잔여

## 핵심 변경
- 양쪽 파일의 현재 제품 surface 목록에 3개 항목 추가
- evidence/source panel에 source-role trust labels 수식어 추가
- CLAUDE.md "summary-range panel" → "summary span / applied-range panel"
- 기존 local-first / approval-based / secondary web-investigation framing 유지

## 검증
- `git diff --stat` — 2 files changed, 26 insertions(+), 5 deletions(-)
- `rg` — 5개 surface 항목 양쪽 파일에서 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo instruction docs의 current product slice response-surface 동기화 완료
