# docs: aggregate item overview capability-basis conditional wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 61, 229): `reviewed_memory_capability_basis`를 deterministic projection 목록에서 분리, conditional 명시
- `docs/ARCHITECTURE.md` — 2곳(line 78, 190): 동일 수정
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 111): 동일 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 슬라이스에서 `reviewed_memory_capability_basis`를 deterministic read-only projection 목록에 포함했으나, 출하 직렬화기는 조건부로 구체화
  - `app/serializers.py:3691-3702`: 전체 capability-source family + matching unblock-contract 존재 시에만 빌드
  - `app/serializers.py:1504-1517`: basis 부재 시 `capability_outcome = blocked_all_required` 유지
  - `tests/test_smoke.py:5818-5833`: `reviewed_memory_planning_target_ref` 존재하면서 `reviewed_memory_capability_basis` 부재하는 aggregate 잠금

## 핵심 변경
- 5개 개요 행에서 `reviewed_memory_capability_basis`를 deterministic projection 괄호 목록에서 제거
- "one conditional `reviewed_memory_capability_basis` (present only when `capability_outcome = unblocked_all_required`)"로 별도 기술

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 5줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — aggregate item 개요의 capability-basis conditional 진실 동기화 완료
