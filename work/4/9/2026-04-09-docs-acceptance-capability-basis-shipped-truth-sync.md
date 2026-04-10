# docs: ACCEPTANCE_CRITERIA capability basis current-shipped wording truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 794): "the current repo may now emit" → "the current contract now emits"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 794가 "may now emit"으로 약하게 기술
- 권위 문서(PRODUCT_SPEC:1417-1426, ARCHITECTURE:1118-1127)에서 current-shipped 패턴 사용
- 동일 파일 line 991에서도 이미 current로 기술

## 핵심 변경
- "the current repo may now emit one separate read-only basis object" → "the current contract now emits one separate read-only basis object"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — ACCEPTANCE_CRITERIA capability_basis shipped 문구 진실 동기화 완료
