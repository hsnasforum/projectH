# docs: precondition meaning rollback-disable-conflict current-shipped wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 8곳(line 1136-1150): rollback/disable/conflict 의미 블록의 "later"/"future" 수식어 제거
- `docs/ARCHITECTURE.md` — 3곳(line 868, 875, 877): 동일 수정
- `docs/ACCEPTANCE_CRITERIA.md` — 2곳(line 657, 659): 동일 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- rollback/disable/conflict 전제조건의 의미 설명에서 apply/effect를 "later applied effect", "future influence stop", "future reviewed-memory layer", "before any later apply"로 프레이밍
- 실제로 apply result, stop-apply, reversal, conflict visibility 모두 이미 출하됨

## 핵심 변경
- "later reviewed-memory effect" → "reviewed-memory effect"
- "later applied reviewed-memory effect" → "applied reviewed-memory effect"
- "later applied effect may deactivate" → "applied effect may deactivate"
- "future influence stop" → "influence stop"
- "later applied effect becomes inactive for future apply" → "applied effect becomes inactive"
- "future reviewed-memory layer ... before any later apply" → "reviewed-memory layer ... inside one reviewed scope"

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 13줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 전제조건 의미 블록의 rollback/disable/conflict shipped 문구 진실 동기화 완료
