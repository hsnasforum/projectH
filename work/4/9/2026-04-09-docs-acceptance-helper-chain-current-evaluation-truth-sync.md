# docs: ACCEPTANCE_CRITERIA internal source-family and helper-chain current-evaluation wording truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 11곳(line 992-1004): 내부 소스 family intro와 헬퍼 체인 평가 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- PRODUCT_SPEC(line 1297-1313)과 ARCHITECTURE(line 1045-1062)는 이미 "current implementation now also evaluates"로 기술
- ACCEPTANCE_CRITERIA만 "may also evaluate"와 "future internal source family"로 약하게 기술
- 동일 블록 내에서 `reviewed_memory_capability_basis`는 이미 current로 기술되어 있어 소스 family도 current여야 일관됨

## 핵심 변경
- line 992: "future internal source family" → "internal source family" (future 제거)
- line 992: "may also evaluate" → "now also evaluates"
- line 993-1004: 10개 헬퍼 행에서 "may also evaluate" → "now also evaluates" (replace_all)

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 11줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — ACCEPTANCE_CRITERIA 내부 소스 family/헬퍼 체인 평가 문구 진실 동기화 완료
