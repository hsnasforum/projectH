# docs: boundary_defined current-shipped wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 1곳(line 1129): "future reviewed memory must have" → "reviewed memory has ... (now shipped)"
- `docs/ARCHITECTURE.md` — 1곳(line 860): "future reviewed memory must have" → "reviewed memory has ... (now shipped)"
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 643): "later reviewed memory needs" → "reviewed memory has ... (now shipped)"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `reviewed_memory_boundary_defined` 의미 행이 boundary/persistence 레이어를 "future"/"later"로 프레이밍
- 실제로 `reviewed_memory_boundary_draft`와 내부 proof-record/store 레이어 이미 출하됨
  - `app/serializers.py:1138, 1432, 1480`
  - `tests/test_web_app.py:1223, 1304, 1321`

## 핵심 변경
- 3개 문서에서 "future/later reviewed memory must have/needs" → "reviewed memory has ... (now shipped as reviewed_memory_boundary_draft and the internal proof-record/store layer)"

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 3줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — boundary_defined 의미 행 shipped 문구 진실 동기화 완료
