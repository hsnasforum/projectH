# docs: PRODUCT_SPEC aggregate item overview qualifier truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — aggregate item 개요 행(line 61)에서 후행 수식어 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 슬라이스에서 `reviewed_memory_transition_record`과 `reviewed_memory_conflict_visibility_record`를 추가했으나, 후행 수식어가 "all kept deterministic and narrower than emitted transition/apply semantics"로 남아 있었음
- 실제로 `reviewed_memory_transition_record`은 출하된 emitted/applied 상태를 반영하며 contract-only가 아님
  - `app/serializers.py:4094-4103`: 조건부 구체화
  - `app/handlers/aggregate.py:254-295`: transition record 발행/저장
- 기존 수식어가 새로 추가된 필드와 모순

## 핵심 변경
- `all kept deterministic and narrower than emitted transition/apply semantics` → `planning and contract fields are deterministic read-only projections, while reviewed_memory_transition_record and reviewed_memory_conflict_visibility_record reflect shipped emitted/applied state`

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — aggregate item 개요 수식어 진실 동기화 완료
