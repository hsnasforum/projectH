# docs: recurrence aggregate item overview projection-vs-record wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 61, 229): aggregate item 개요를 projection family + lifecycle record family로 분리
- `docs/ARCHITECTURE.md` — 2곳(line 78, 190): 동일 분리
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 111): 동일 분리

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 5개 개요 행이 read-only projection과 lifecycle record를 하나의 긴 나열로 혼합
- 직렬화기(`app/serializers.py:4044-4105`)에서 이미 projection과 record를 구분하여 조립
- 더 깊은 shipped 섹션에서도 이미 transition/conflict-visibility 라이프사이클을 별도 기술

## 핵심 변경
- "one read-only X, one read-only Y, ... one conditional Z, one optional W" 나열 → 두 가족으로 분리:
  1. deterministic read-only projections (11개 필드 괄호 나열)
  2. lifecycle records: conditional `reviewed_memory_transition_record` (emitted/applied/stopped/reversed) + optional `reviewed_memory_conflict_visibility_record` (conflict_visibility_checked)
- "may now also expose" → "now also exposes" / "now also serializes"

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 5줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — aggregate item 개요의 projection vs record 구분 진실 동기화 완료
