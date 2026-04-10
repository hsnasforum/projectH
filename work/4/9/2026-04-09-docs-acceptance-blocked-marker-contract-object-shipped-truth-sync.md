# docs: ACCEPTANCE_CRITERIA promotion-boundary blocked marker and contract-object shipped truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 5곳(line 592, 599, 606, 616, 628): "may now emit" / "may now also emit" → "now emits" / "now also emits"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 5개 객체(blocked marker, precondition status, boundary draft, rollback contract, disable contract)는 이미 출하된 read-only aggregate-level 표면
- 권위 문서(PRODUCT_SPEC:1073-1116, ARCHITECTURE:809-847)에서 current-shipped 패턴 사용
- ACCEPTANCE_CRITERIA만 "may now emit"으로 약하게 기술

## 핵심 변경
- line 592: "may now emit only" → "now emits"
- line 599: "may now also emit" → "now also emits" (precondition status)
- line 606: "may now also emit" → "now also emits" (boundary draft)
- line 616: "may now also emit" → "now also emits" (rollback contract)
- line 628: "may now also emit" → "now also emits" (disable contract)

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 5줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — ACCEPTANCE_CRITERIA blocked marker / contract-object shipped 문구 진실 동기화 완료
