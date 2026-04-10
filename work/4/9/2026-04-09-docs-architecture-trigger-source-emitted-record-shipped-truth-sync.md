# docs: ARCHITECTURE trigger-source and first emitted-record later wording truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 3곳(line 1159, 1160, 1161): trigger-source/emitted-record 레이어링의 "future"/"later" 수식어 제거, current-shipped 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 1159: "future aggregate-level trigger-source layer" — 이미 출하됨
- line 1160: "first later emitted transition surface" — 이미 출하됨
- line 1161: "materialize that first later emitted record" — 이미 출하됨
- 동일 파일 line 971-973에서 이미 current shipped로 기술
- PRODUCT_SPEC(line 1529), ACCEPTANCE_CRITERIA(line 762-763)에서도 동일

## 핵심 변경
- "future aggregate-level trigger-source layer" → "current shipped aggregate-level trigger-source layer"
- "first later emitted transition surface" → "current shipped emitted transition surface"
- "materialize that first later emitted record only for" → "that emitted record materializes only for"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 3줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — ARCHITECTURE trigger-source/emitted-record 레이어링 shipped 문구 진실 동기화 완료
