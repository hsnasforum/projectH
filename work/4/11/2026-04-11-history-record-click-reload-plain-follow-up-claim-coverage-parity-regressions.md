# history-record click-reload plain-follow-up claim_coverage parity regressions

## 변경 파일

- `tests/test_web_app.py`
- `work/4/11/2026-04-11-history-record-click-reload-plain-follow-up-claim-coverage-parity-regressions.md`

## 사용 skill

- 없음

## 변경 이유

직전 tests-only 슬라이스는 natural-language reload 이후 `load_web_search_record_id` 없이 이어지는 plain follow-up 경로에 대한 정확한 proof gap 을 entity-card / latest-update 양쪽에서 닫았습니다. 같은 가족 안에 남은 current-risk 는 제품 동작 문제가 아니라, 브라우저가 실제로 타는 또 하나의 shipped user-visible 경로 — 사용자가 history-card 의 `다시 불러오기` 버튼을 눌러 `load_web_search_record_id` 만 보내는 click reload 를 한 뒤, 그 다음에 record id 없이 일반 follow-up 을 던지는 흐름 — 에 대한 proof 입니다. 기존 click-reload follow-up 테스트들은 두 번째 호출에도 `load_web_search_record_id` 를 다시 실어 주고 있어서, 이 정확한 플레인 follow-up 경로는 아직 직접 lock 되어 있지 않았습니다.

ad-hoc 재생으로 현재 구현이 이미 바르게 동작한다는 사실을 확인했으므로, 이 슬라이스는 tests-only 로 해당 정확한 click-reload plain-follow-up 경로에 대한 회귀 둘을 추가해 `/work`, 실제 coverage, 현재 구현이 한 지점에서 만나도록 닫습니다. 구현 코드, 제품 문서, browser selector, pipeline / runtime 범위, 다른 reload 가족 테스트 파일은 건드리지 않았습니다.

## 핵심 변경

### `tests/test_web_app.py`

기존 `test_handle_chat_entity_card_dual_probe_reload_preserves_active_context_source_paths` 바로 앞에 두 회귀를 추가했습니다. 배치 위치는 직전 슬라이스의 natural-language plain-follow-up 회귀 옆입니다.

- `test_handle_chat_click_reload_plain_follow_up_keeps_top_level_claim_coverage`
  - `WebSearchStore.save(...)` 로 `이용 형태 weak / 개발 weak` claim_coverage + `재조사했지만 이용 형태는 아직 단일 출처 상태입니다.` progress_summary 를 갖는 entity-card record 를 seed.
  - Step 1: `handle_chat({"session_id": ..., "provider": "mock", "load_web_search_record_id": record_id})` — 브라우저 click reload 가 보내는 exact payload 그대로, `user_text` 는 생략합니다. 이 경우 `app/handlers/chat.py:541-544` 가 `"최근 웹 검색 기록을 다시 불러와 주세요."` 를 auto-inject 하고, 그 문장이 `_reuse_web_search_record()` 의 show-only 감지 문구 목록 (`"다시 보여"`, `"불러와"`, ...) 에 매칭되어 show-only reload 분기를 탑니다. 응답의 `actions_taken == ["load_web_search_record"]` 도 lock 합니다.
  - Step 2: `handle_chat({"session_id": ..., "user_text": "이 결과 한 문장으로 요약해줘", "provider": "mock", "web_search_permission": "enabled"})` — **`load_web_search_record_id` 를 넣지 않은** plain follow-up. 이 문구는 `_should_treat_as_entity_reinvestigation()` 의 slot-name 감지에도, 새로운 web search 트리거에도 걸리지 않아 `_respond_with_active_context()` 경로로 통과합니다.
  - `result["response"]["claim_coverage"]` 에 `이용 형태` slot 이 포함되고, `result["response"]["claim_coverage_progress_summary"]` 가 저장값과 정확히 일치하며, `result["session"]["messages"]` 의 마지막 assistant message 에도 같은 값이 persist 되는지를 lock. 실패 시 현재 payload 를 assertion 메시지로 노출해 디버깅을 돕습니다.

- `test_handle_chat_latest_update_click_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty`
  - `서울 날씨` latest-update record (`claim_coverage=[]`, empty `claim_coverage_progress_summary`) 를 seed.
  - Step 1: entity-card 와 동일하게 click reload payload (`load_web_search_record_id` 만) 로 show-only reload 를 호출하고 `actions_taken == ["load_web_search_record"]` 를 lock.
  - Step 2: `load_web_search_record_id` 없이 `"이 결과 한 문장으로 요약해줘"` plain follow-up 을 돌리고, `result["response"]["claim_coverage"]` 가 `[]`, `claim_coverage_progress_summary` 는 falsy 로 유지되며, 마지막 assistant message 의 `claim_coverage` 값도 `[]`, `claim_coverage_progress_summary` 는 falsy 임을 확인. 이는 `_respond_with_active_context()` 의 `kind == "web_search"` + 비어 있지 않은 `claim_coverage` gate 가 latest-update / no-claim-coverage 경로를 여전히 건드리지 않는다는 점을 click-reload 진입로에서도 직접 증명합니다.

두 테스트 모두 기존 reload-by-id / natural-language plain-follow-up 회귀들을 수정하지 않고 그 옆에 나란히 배치됩니다. 같은 user_text (`"이 결과 한 문장으로 요약해줘"`) 와 같은 follow-up payload 모양을 natural-language reload 쪽 테스트와 공유해, 두 reload 진입로 (natural-language vs click-reload) 가 같은 plain-follow-up contract 을 공유한다는 대칭성을 읽기 쉽게 드러냅니다.

### 구현 / 제품 docs / smoke

구현 코드, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `tests/test_smoke.py`, `core/agent_loop.py`, 기타 docs family 는 이 슬라이스에서 건드리지 않았습니다. 직전 슬라이스에서 이미 `AgentLoop._respond_with_active_context()` 의 propagation 이 click-reload 진입로까지 동일하게 커버하므로, 이 슬라이스가 필요한 것은 WebAppService/browser-contract 레벨의 정확한 proof 뿐입니다. smoke 쪽의 AgentLoop 회귀는 click-reload 가 `load_web_search_record_id` metadata 에 의존하는 진입로라 `handle_chat` payload 구조를 흉내 내기 어려워, 이 슬라이스는 WebAppService 계층에 집중했습니다.

controller / pipeline / watcher / runtime, `e2e/tests/web-smoke.spec.mjs`, browser selector, `app/static/app.js`, `docs/NEXT_STEPS.md`, 다른 docs family, `work`/`verify` 이전 항목은 건드리지 않았습니다.

## 검증

- `python3 -m py_compile tests/test_smoke.py tests/test_web_app.py` → 성공.
- 신규 회귀 두 개 개별 실행:
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_click_reload_plain_follow_up_keeps_top_level_claim_coverage` → `Ran 1 test … OK`.
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_click_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty` → `Ran 1 test … OK`.
- 직전 `/work` 의 7-test proof 배치에 이번 슬라이스의 두 신규 회귀를 더해 한 번에 실행:
  - `tests.test_smoke.SmokeTest.test_reload_follow_up_propagates_top_level_claim_coverage_from_active_context`
  - `tests.test_web_app.WebAppServiceTest.test_handle_chat_reload_follow_up_propagates_top_level_claim_coverage_and_progress_summary`
  - `tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_then_follow_up_keeps_top_level_claim_coverage`
  - `tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_reload_follow_up_keeps_claim_coverage_surfaces_empty`
  - `tests.test_smoke.SmokeTest.test_plain_follow_up_without_load_record_id_keeps_top_level_claim_coverage_from_active_context`
  - `tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_plain_follow_up_keeps_top_level_claim_coverage`
  - `tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_natural_language_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty`
  - `tests.test_web_app.WebAppServiceTest.test_handle_chat_click_reload_plain_follow_up_keeps_top_level_claim_coverage`
  - `tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_click_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty`
  결과: `Ran 9 tests … OK`. 기존 reload-by-id, natural-language plain-follow-up, 그리고 새 click-reload plain-follow-up 회귀가 한 배치에서 같이 통과함을 확인했습니다.
- `git diff --check -- tests/test_smoke.py tests/test_web_app.py work/4/11` → whitespace 경고 없음.
- 구현 / 브라우저 계약은 이번 슬라이스에서 건드리지 않았으므로 Playwright `make e2e-test` 와 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 이번 라운드에 과하여 돌리지 않았습니다. (이 sandbox 에서는 전체 `tests.test_web_app` 재실행이 socket-bind `PermissionError` 를 낼 수 있다는 한계를 handoff 가 명시했고, 이번 변경은 테스트 추가뿐이라 신규 회귀 배치로 진실성을 증명했습니다.)

## 남은 리스크

- 새 회귀 두 개가 선택한 follow-up 문구 `"이 결과 한 문장으로 요약해줘"` 는 직전 슬라이스의 natural-language 경로 회귀와 같은 문구입니다. 그래서 entity reinvestigation 슬롯 키워드 (`개발`, `장르`, `플랫폼`, `출시`, `상태`) 나 새 web-search 트리거 (`검색`) 어느 쪽에도 매칭되지 않아 `_respond_with_active_context()` 경로를 통과하지만, 미래에 이 문구가 슬롯 키워드 / 트리거 어휘로 확장되면 두 가족 테스트가 동시에 경로가 바뀝니다. 그 경우 문구와 어휘를 같은 라운드에서 같이 점검해야 합니다.
- click reload 진입로는 `app/handlers/chat.py` 가 `load_web_search_record_id` 단독 payload 에서 `"최근 웹 검색 기록을 다시 불러와 주세요."` 라는 auto-injected user_text 를 붙여 준다는 사실에 의존합니다. 미래에 이 auto-inject 문구가 바뀌면 show-only reload 감지 어휘 목록과 함께 확인해야 합니다. 현재 회귀는 응답의 `actions_taken == ["load_web_search_record"]` 를 같이 assert 해서, 해당 진입로가 실제로 show-only reload 분기를 탔다는 점을 드러냅니다.
- 이 슬라이스는 tests-only 라서 구현 회귀를 직접 막지는 않습니다. 미래에 `_respond_with_active_context()` 의 propagation 블록이 사라지거나 gate 조건이 바뀌면, click-reload plain-follow-up 회귀들이 entity-card 쪽에서 먼저 빨갛게 터집니다. 반대로 latest-update 경로가 실수로 top-level claim_coverage 를 주입하게 되면 latest-update 회귀 쪽에서 터집니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `controller/server.py`, `pipeline_gui/backend.py`, `watcher_core.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`, `docs/PRODUCT_SPEC.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`, `core/agent_loop.py`, `storage/web_search_store.py`, `verify/4/10/...`, 기존 `work/4/11/`와 `verify/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았습니다.
