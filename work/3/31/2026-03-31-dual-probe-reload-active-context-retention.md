# 2026-03-31 dual-probe reload active-context source-path retention

## 변경 파일
- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, history reload 뒤에도 entity-card dual probe가 `active_context["source_paths"]`에 보존되는지 확인하도록 지시.
- 이전 라운드에서 initial response 경로는 `pre_selected_sources`로 수정했으나, `_reuse_web_search_record`의 reload 경로는 여전히 `_build_web_search_active_context`를 `pre_selected_sources` 없이 호출하여 동일 불일치 가능성이 있었음.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_reuse_web_search_record`에서 entity-card reload 시 `entity_sources` 변수를 `None`으로 초기화
2. entity profile일 때 `entity_sources`에 `_select_ranked_web_sources(max_items=3)` 결과 할당
3. `_build_web_search_active_context` 호출에 `pre_selected_sources=entity_sources` 전달

### 테스트 변경 (`tests/test_web_app.py`)
- `test_handle_chat_entity_card_dual_probe_reload_preserves_active_context_source_paths` 추가
  - WebSearchStore에 dual-probe entity-card record 직접 저장 (namu.wiki + pearlabyss.com/200 platform probe + pearlabyss.com/300 service probe)
  - `load_web_search_record_id`로 reload
  - 검증: `active_context["source_paths"]`에 두 probe URL 모두 포함

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- initial response 경로(이전 라운드) 유지
- latest_update/general 경로 유지

## 검증
- `python3 -m unittest -v tests.test_web_app`: 111 tests, OK (1.839s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음 (reload 경로 변경이므로 test_web_app만 검증)

## 남은 리스크
- dirty worktree가 여전히 넓음.
