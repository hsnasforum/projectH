# docs: PROJECT_CUSTOM_INSTRUCTIONS current product slice response-surface truth sync

## 변경 파일
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 3곳(line 12-14, 17): 근거/출처 패널 확장, structured search result preview/source-type labels/applied-preferences badge 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- PROJECT_CUSTOM_INSTRUCTIONS.md의 현재 구현 기준 목록에 shipped browser response surface 3종 누락:
  - structured search result preview panel
  - summary source-type labels (`문서 요약` / `선택 결과 요약`)
  - applied-preferences badge (`선호 N건 반영`)
- 근거/출처 패널에 source-role trust labels 수식어 누락
- 이전 라운드에서 AGENTS.md, CLAUDE.md 및 전체 root docs 동기화 완료

## 핵심 변경
- "근거/출처 패널" → "근거/출처 패널 (source-role trust labels 포함)"
- structured search result preview panel 추가
- summary source-type labels (`문서 요약` / `선택 결과 요약`) 추가
- "요약 반영 구간 패널" → "요약 반영 구간 패널 (summary span / applied-range)"
- applied-preferences badge (`선호 N건 반영`) 추가
- 기존 Korean 문체 유지

## 검증
- `git diff -- PROJECT_CUSTOM_INSTRUCTIONS.md` — 확인
- `rg` — 4개 surface 항목 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- GEMINI.md에 동일 패턴 잔여 가능 — 현재 scope 외
