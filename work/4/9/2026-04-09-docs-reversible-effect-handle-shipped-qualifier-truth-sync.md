# docs: NEXT_STEPS reversible_effect_handle emitted/apply shipped qualifier truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — line 328: "any later emitted transition record, or any later reviewed-memory apply result" → "the now-shipped emitted transition record, and the now-shipped reviewed-memory apply result"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `reviewed_memory_reversible_effect_handle`의 계층 순서 설명이 emitted transition record와 apply result를 "later"로 기술
- 실제로는 이미 출하됨:
  - `docs/PRODUCT_SPEC.md:1529-1537`
  - `e2e/tests/web-smoke.spec.mjs:900-966`
- 내부 핸들의 계층 위치(rollback_contract 위, basis/emitted/apply 아래)는 동일하지만, "later" 수식어가 부정확

## 핵심 변경
- "any later emitted transition record" → "the now-shipped emitted transition record"
- "any later reviewed-memory apply result" → "the now-shipped reviewed-memory apply result"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 내부 핸들 계층 수식어 진실 동기화 완료
