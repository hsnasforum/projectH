# docs: PRODUCT_SPEC aggregate item late-stage state qualifier truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — aggregate item 개요 행(line 61)에서 후행 수식어 확장

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 슬라이스에서 "reflect shipped emitted/applied state"로 수정했으나, 출하 동작은 더 넓음
- `reviewed_memory_transition_record`는 emitted/applied 외에 stopped/reversed 단계도 포함
  - `tests/test_web_app.py:7286`: `record_stage = reversed` 잠금
- `reviewed_memory_conflict_visibility_record`는 별도 conflict-visibility 상태
  - `tests/test_web_app.py:7301-7302, 7323-7326`: `record_stage = conflict_visibility_checked` 잠금
- `docs/PRODUCT_SPEC.md:1537`에서 이미 stopped/reversed/conflict_visibility 기술

## 핵심 변경
- `reflect shipped emitted/applied state` → `reflects shipped lifecycle state (emitted / applied / stopped / reversed)` + `reflects shipped conflict-visibility state`

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — aggregate item 개요 수식어가 전체 출하 라이프사이클 진실 동기화 완료
