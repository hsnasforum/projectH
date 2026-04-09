# docs: MILESTONES NEXT_STEPS applied-preferences response-meta badge truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 33): applied-preferences badge 항목 추가
- `docs/NEXT_STEPS.md` — 1곳(line 13): applied-preferences badge 항목 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 라운드에서 README, PRODUCT_SPEC, ACCEPTANCE_CRITERIA, ARCHITECTURE에 applied-preferences badge 문서화 완료
- MILESTONES와 NEXT_STEPS에는 response origin badge만 기재되어 있고 같은 meta 영역의 applied-preferences badge가 누락
- shipped truth: `MessageBubble.tsx:275-281`에서 `applied_preferences` 비어있지 않을 때 `선호 N건 반영` 배지 렌더링

## 핵심 변경
- MILESTONES:33 — response origin badge 아래에 applied-preferences badge 항목 추가
- NEXT_STEPS:13 — response origin badge 아래에 applied-preferences badge 항목 추가
- 기존 root docs와 동일한 문구 사용 (tooltip 포함)
- durable preference memory 주장 없음

## 검증
- `git diff -- docs/MILESTONES.md docs/NEXT_STEPS.md` — 2줄 추가 확인
- `rg 'applied-preferences badge|선호 .*건 반영'` — 양쪽 파일에서 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 root docs의 applied-preferences badge 문서화 완료
