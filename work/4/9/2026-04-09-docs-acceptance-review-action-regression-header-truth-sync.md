# docs: ACCEPTANCE_CRITERIA review-action regression header current-shipped truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 1080): regression 헤더에서 "future" → "current shipped"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- review-action 슬라이스(durable_candidate, candidate_review_record, review_queue_items)는 이미 출하됨
  - `app/serializers.py:4140-4156, 4238-4279`
  - `tests/test_web_app.py:3539, 3680-3726, 3822`
  - `docs/ARCHITECTURE.md:1133-1136`
- regression 헤더만 "first future review-action slice"로 남아 있음

## 핵심 변경
- "Focused regression for the first future review-action slice" → "Focused regression for the current shipped review-action slice"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — review-action regression 헤더 진실 동기화 완료
