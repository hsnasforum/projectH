# docs: ARCHITECTURE ACCEPTANCE_CRITERIA conflict visibility shipped truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 3곳(line 1162, 1164, 1299): `future_reviewed_memory_conflict_visibility`를 "later"/"next step"에서 "now implemented"로 변경
- `docs/ACCEPTANCE_CRITERIA.md` — 3곳(line 937, 957, 967): "conflict-visibility remains closed"를 "now also implemented"로 변경

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `future_reviewed_memory_conflict_visibility`는 이미 출하됨:
  - `docs/PRODUCT_SPEC.md:1537`: `충돌 확인` 단계와 `reviewed_memory_conflict_visibility_record` 기술
  - `tests/test_web_app.py:7288-7326`: `conflict_visibility_checked` record_stage 잠금
  - `e2e/tests/web-smoke.spec.mjs:938-966`: 브라우저 `충돌 확인` 흐름 잠금
- ARCHITECTURE와 ACCEPTANCE_CRITERIA만 "later"/"closed"로 남아 진실 불일치

## 핵심 변경
- ARCHITECTURE 3곳: "keep later" / "next step" → "now implemented" + `충돌 확인` 버튼 + `record_stage = conflict_visibility_checked` 기술
- ACCEPTANCE_CRITERIA 3곳: "remains closed" → "now implemented" + 동일 기술

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 6줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — conflict-visibility 출하 상태 진실 동기화 완료
