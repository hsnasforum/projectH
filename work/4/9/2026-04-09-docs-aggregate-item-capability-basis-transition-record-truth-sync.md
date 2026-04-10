# docs: recurrence aggregate item capability-basis transition-record truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 61, 229): aggregate item 요약에 `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`, `reviewed_memory_conflict_visibility_record` 추가
- `docs/ARCHITECTURE.md` — 2곳(line 78, 190): 동일 추가
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 111): 동일 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `app/serializers.py:4084-4104`에서 aggregate 직렬화 시 `reviewed_memory_capability_basis`, 조건부 `reviewed_memory_transition_record`, 선택적 `reviewed_memory_conflict_visibility_record`를 구체화
- 기존 요약 행은 이 3개 필드를 누락
- 더 깊은 shipped 섹션에서는 이미 정확히 기술 (PRODUCT_SPEC:1242-1243, ARCHITECTURE:993-994 등)

## 핵심 변경
- 5개 요약 행에 3개 누락 필드 추가:
  - `reviewed_memory_capability_basis` (read-only)
  - `reviewed_memory_transition_record` (conditional)
  - `reviewed_memory_conflict_visibility_record` (optional read-only, PRODUCT_SPEC에서는 이전에 누락)

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 5줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — aggregate item 요약 필드 리스트 진실 동기화 완료
