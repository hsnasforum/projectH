# 2026-03-31 actual-search dual-probe reload active-context retention

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 실제 entity search가 만든 record를 history-card reload했을 때 dual probe가 `active_context["source_paths"]`에 보존되는지 확인하도록 지시.
- 이전 라운드의 direct `store.save()` fixture test는 통과했지만, 실제 `handle_chat` → entity search → probe → record 저장 → reload 전체 경로는 아직 explicit regression으로 잠기지 않았음.

## 핵심 변경
- `test_handle_chat_actual_entity_search_dual_probe_reload_preserves_active_context_source_paths` 추가 (`tests/test_web_app.py`)
  - `_FakeWebSearchTool`으로 실제 dual-probe entity search 수행 (namu.wiki + platform probe boardNo=200 + service probe boardNo=300)
  - 첫 호출: entity search → record 저장 → `record_id` 획득
  - 둘째 호출: `load_web_search_record_id`로 history-card reload
  - 검증: reload 후 `active_context["source_paths"]`에 두 probe URL 모두 포함
- production 코드 변경 없음 — test-only slice (이전 라운드의 `pre_selected_sources` 전달이 실제 search 경로에서도 작동 확인)

## 검증
- `python3 -m unittest -v tests.test_web_app`: 112 tests, OK (1.851s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음 (test_web_app에 test-only 추가)

## 남은 리스크
- dirty worktree가 여전히 넓음.
