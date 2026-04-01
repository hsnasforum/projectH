# 2026-03-31 entity-card weak/missing slot history-card reload retention

## 변경 파일
- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, entity-card의 weak/missing slot 섹션 분리가 history-card reload 후에도 유지되는지 확인하도록 지시.
- 테스트 추가 시 reload 경로에서 entity-card formatted summary가 아닌 generic summary가 생성되는 실제 버그 발견 — `_reuse_web_search_record`의 `_summarize_web_search_results` 호출에서 `intent_kind`와 `answer_mode`가 전달되지 않았음.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_reuse_web_search_record`에서 stored `answer_mode`가 `"entity_card"`일 때 `intent_kind="external_fact"`를 추론하여 `_summarize_web_search_results`에 전달
2. `stored_answer_mode`도 함께 전달하여 entity/latest_update summary format이 reload 경로에서도 올바르게 생성되도록 수정

### 테스트 변경 (`tests/test_web_app.py`)
- `test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_history_card_reload` 추가
  - 첫 호출: namu.wiki 단일 소스 entity search → record 저장
  - 둘째 호출: `load_web_search_record_id` history-card reload
  - 검증:
    - reload text에 `"불확실 정보:"` 섹션 존재
    - reload text에 `"추가 확인 필요:"` 섹션 존재
    - weak 섹션에 `"단일 출처"` 문구 포함
    - missing 섹션에 `"교차 확인 가능한 근거가 더 필요합니다"` 문구 포함
    - `claim_coverage`에 weak + missing status 모두 존재

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- reinvestigation, source selection, probe 로직 변경 없음

## 검증
- `python3 -m unittest -v tests.test_web_app`: 121 tests, OK (2.258s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음

## 남은 리스크
- `stored_intent_kind` 추론은 `stored_answer_mode == "entity_card"` → `"external_fact"` 매핑만 사용. `latest_update`는 `intent_kind`가 None이어도 `answer_mode` 분기에서 처리되므로 현재 영향 없음.
- dirty worktree가 여전히 넓음.
