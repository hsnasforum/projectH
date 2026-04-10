# docs: ACCEPTANCE_CRITERIA capability_source_refs summary current-internal wording truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 982): source family 요약 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- PRODUCT_SPEC(line 1280)과 ARCHITECTURE(line 1028)는 이미 "one current internal"로 기술
- ACCEPTANCE_CRITERIA line 1072도 이미 "current internal machinery that stays payload-hidden"으로 기술
- line 982만 "stays one additive internal aggregate-scoped helper only"로 약하게 기술

## 핵심 변경
- "stays one additive internal aggregate-scoped helper only" → "is one current internal aggregate-scoped helper that stays payload-hidden"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — capability_source_refs 요약 문구 진실 동기화 완료
