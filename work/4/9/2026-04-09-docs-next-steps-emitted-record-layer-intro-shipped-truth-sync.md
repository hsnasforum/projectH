# docs: NEXT_STEPS emitted-transition-record layer intro shipped wording truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — 1곳(line 237): "the next unresolved layer now starts above" → "the trigger-source / emitted-record layer is now shipped above"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 237이 trigger-source/emitted-record 레이어를 "next unresolved layer"로 프레이밍
- 동일 블록 line 239, 244, 261에서 이미 shipped로 기술
- MILESTONES(line 314, 316), PRODUCT_SPEC(line 1518, 1524), ACCEPTANCE_CRITERIA(line 914, 922)에서 이미 shipped

## 핵심 변경
- "the next unresolved layer now starts above the shipped blocked trigger-source affordance" → "the trigger-source / emitted-record layer is now shipped above the shipped blocked trigger-source affordance"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — NEXT_STEPS emitted-record 레이어 intro shipped 진실 동기화 완료
