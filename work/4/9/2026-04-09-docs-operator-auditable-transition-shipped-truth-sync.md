# docs: operator_auditable_reviewed_memory_transition current-shipped wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 1곳(line 1159): "any later reviewed-memory transition" → "every shipped reviewed-memory transition"
- `docs/ARCHITECTURE.md` — 1곳(line 889): 동일 수정
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 666): 동일 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 3개 문서의 `operator_auditable_reviewed_memory_transition` 의미 행이 "later reviewed-memory transition"으로 프레이밍
- emitted transition, apply result, stop-apply, reversal, conflict-visibility 모두 이미 출하됨
  - `app/handlers/aggregate.py:392, 467, 529, 554`
  - `tests/test_web_app.py:7488, 7643, 7802`

## 핵심 변경
- "any later reviewed-memory transition above the blocked marker must/leaves" → "every shipped reviewed-memory transition above the blocked marker leaves"

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 3줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — operator_auditable 의미 행 shipped 문구 진실 동기화 완료
