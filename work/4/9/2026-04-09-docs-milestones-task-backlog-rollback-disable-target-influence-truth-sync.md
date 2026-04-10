# docs: MILESTONES TASK_BACKLOG rollback-disable target-influence wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 2곳(line 212, 224): "later applied reviewed-memory effect" → "applied reviewed-memory effect"
- `docs/TASK_BACKLOG.md` — 4곳(line 352, 361, 382, 391): "later applied reviewed-memory effect"/"later applied reviewed-memory influence" → "applied"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 6개 행이 rollback/disable 대상/출력 경계를 "later applied" 수식어로 프레이밍
- apply result, stop-apply, reversal 모두 이미 출하됨
- 권위 문서는 이미 "applied" 현재형으로 수정 완료

## 핵심 변경
- "later applied reviewed-memory effect" → "applied reviewed-memory effect" (4곳)
- "later applied reviewed-memory influence" → "applied reviewed-memory influence" (2곳)

## 검증
- `git diff --check` — 공백 오류 없음
- `rg 'later applied reviewed-memory' MILESTONES TASK_BACKLOG` — 0건
- 2개 파일, 6줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES/TASK_BACKLOG rollback/disable 대상/영향 "later applied" 문구 진실 동기화 완료
