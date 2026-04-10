# docs: ACCEPTANCE_CRITERIA operator-visible trigger-source layer shipped wording truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 744): "the first later operator-visible trigger-source slice should stay" → "the current shipped operator-visible trigger-source layer stays"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 744가 trigger-source 레이어를 "later slice"로 프레이밍
- 동일 문서 line 931, 937에서 이미 shipped로 기술
- PRODUCT_SPEC(line 1518)과 ARCHITECTURE(line 971)에서도 이미 current shipped로 기술

## 핵심 변경
- "the first later operator-visible trigger-source slice should stay" → "the current shipped operator-visible trigger-source layer stays"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — ACCEPTANCE_CRITERIA trigger-source 레이어 shipped 문구 진실 동기화 완료
