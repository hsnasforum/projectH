# docs: NEXT_STEPS MILESTONES TASK_BACKLOG rollback-disable applied-effect wording truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — 6곳(line 134-141): rollback/disable 의미 요약의 "later reviewed-memory effect"/"later applied" → "applied reviewed-memory effect"/"applied"
- `docs/MILESTONES.md` — 2곳(line 214, 226): "later applied effect" → "applied effect"
- `docs/TASK_BACKLOG.md` — 4곳(line 319-320, 351, 381): "later reviewed-memory effect"/"later apply" → "applied reviewed-memory effect"/"applied effect"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 12개 행이 rollback/disable 대상을 "later reviewed-memory effect"/"later apply"/"later applied influence"로 프레이밍
- 실제로 apply result, stop-apply, reversal 모두 이미 출하됨
- 권위 문서(PRODUCT_SPEC:1136-1146, ARCHITECTURE:865-873, ACCEPTANCE_CRITERIA:648-654)는 이미 "applied" 현재형으로 수정 완료

## 핵심 변경
- "later reviewed-memory effect" → "applied reviewed-memory effect" (전체)
- "later apply" → "applied effect"
- "later applied influence" → "applied influence"
- "later applied effect" → "applied effect"

## 검증
- `git diff --check` — 공백 오류 없음
- `rg 'later reviewed-memory effect|later apply|later applied' NEXT_STEPS MILESTONES TASK_BACKLOG` — 0건
- 3개 파일, 12줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 기획 문서 rollback/disable "later applied effect" 문구 진실 동기화 완료
