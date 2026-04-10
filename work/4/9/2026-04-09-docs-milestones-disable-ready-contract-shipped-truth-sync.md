# docs: MILESTONES disable_ready contract-decision wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 223): `disable_ready_reviewed_memory_effect` 헤딩에서 "next contract decision should now also fix" → "is now fixed as one shipped disable contract surface"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 223이 "next contract decision should now also fix"로 프레이밍하지만, 동일 블록 line 228-234에서 이미 `reviewed_memory_disable_contract`를 implemented로 기술
- 권위 문서(PRODUCT_SPEC:1143-1148, 1490-1491; ARCHITECTURE:870-875; ACCEPTANCE_CRITERIA:653-657)도 이미 shipped로 기술

## 핵심 변경
- "the next contract decision should now also fix `disable_ready_reviewed_memory_effect` to one exact future stop-apply target" → "`disable_ready_reviewed_memory_effect` is now fixed as one shipped disable contract surface"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES disable_ready 헤딩 shipped 진실 동기화 완료
