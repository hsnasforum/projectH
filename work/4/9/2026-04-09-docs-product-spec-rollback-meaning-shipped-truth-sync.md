# docs: PRODUCT_SPEC precondition rollback meaning current-shipped wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 1139-1140): rollback 의미 행의 "later applied effect"/"future influence"/"future reviewed-memory effect" 제거

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 1139: "later applied effect"와 "future influence"로 프레이밍
- line 1140: "future reviewed-memory effect"로 프레이밍
- apply result, stop-apply, reversal 모두 이미 출하됨

## 핵심 변경
- "that later applied effect and stop of that effect's future influence" → "that applied effect and stop of that effect's influence"
- "rollback of future reviewed-memory effect" → "rollback of applied reviewed-memory effect"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 2줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — PRODUCT_SPEC rollback 의미 행 shipped 문구 진실 동기화 완료
