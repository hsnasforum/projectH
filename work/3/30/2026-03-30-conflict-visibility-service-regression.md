# 2026-03-30 conflict_visibility service-level regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`와 `verify/3/30/2026-03-30-future-reviewed-memory-conflict-visibility-verification.md`에서 `check_aggregate_conflict_visibility`와 `/api/aggregate-transition-conflict-check` 경로에 대한 direct service-level regression이 없다고 지적되었습니다.
- behavior widening 없이 현재 truth를 고정하는 focused regression 한 슬라이스만 추가했습니다.

## 핵심 변경
- `test_check_aggregate_conflict_visibility_creates_separate_record_with_key_fields` 테스트 추가:
  - 2개 파일 요약 → 교정 → 후보 확인/리뷰(accept) → aggregate unblocked
  - emit → apply → confirm result → stop → reverse → conflict visibility check 전체 흐름 실행
  - `reviewed_memory_conflict_visibility_record`의 핵심 필드 검증:
    - `transition_action = future_reviewed_memory_conflict_visibility`
    - `record_stage = conflict_visibility_checked`
    - `conflict_visibility_stage = conflict_visibility_checked`
    - `source_apply_transition_ref` = 원래 apply transition의 canonical_transition_id
    - `checked_at` 존재 및 문자열 타입
    - `conflict_entries` 리스트 및 `conflict_entry_count` 일치
  - 별도 record임을 확인 (자체 canonical_transition_id, "transition-local-" 접두사)
  - 원래 apply/reversal record가 mutate되지 않음 확인
  - 직렬화된 session의 aggregate에 `reviewed_memory_conflict_visibility_record`가 올바르게 표시됨 확인
  - reversed가 아닌 record에 conflict check 호출 시 400 에러 확인

## 검증
- `python3 -m py_compile app/web.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_web_app` — 91 tests OK (기존 90 + 신규 1)
- `git diff --check` — 통과

## 남은 리스크
- HTTP handler 수준의 통합 테스트는 추가하지 않았습니다. 현재 다른 transition route도 HTTP-level 테스트가 없으므로 일관성 유지.
- e2e selector/flow는 건드리지 않았습니다.
- docs는 현재 truth와 이미 일치하므로 변경하지 않았습니다.
