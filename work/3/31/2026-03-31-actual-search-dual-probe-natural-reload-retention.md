# 2026-03-31 actual-search dual-probe natural reload retention

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 실제 entity search가 만든 최근 record를 자연어 recent-record recall로 reload했을 때 dual probe가 `active_context["source_paths"]`에 보존되는지 확인하도록 지시.
- 이전 라운드에서 `load_web_search_record_id` 경로는 잠갔으나, 자연어 `"방금 검색한 결과 다시 보여줘"` 경로는 아직 explicit regression이 없었음.

## 핵심 변경
- `test_handle_chat_actual_entity_search_dual_probe_natural_reload_preserves_source_paths` 추가 (`tests/test_web_app.py`)
  - `_FakeWebSearchTool`로 실제 dual-probe entity search 수행
  - 첫 호출: entity search → record 저장
  - 둘째 호출: `user_text="방금 검색한 결과 다시 보여줘"` 자연어 reload
  - 검증: `actions_taken == ["load_web_search_record"]`, `active_context["source_paths"]`에 두 probe URL 모두 포함
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 113 tests, OK (1.889s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음 (test_web_app에 test-only 추가)

## 남은 리스크
- dirty worktree가 여전히 넓음.
