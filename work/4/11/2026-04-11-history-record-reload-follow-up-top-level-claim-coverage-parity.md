# history-record reload-follow-up top-level claim_coverage parity

## 변경 파일

- `core/agent_loop.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/11/2026-04-11-history-record-reload-follow-up-top-level-claim-coverage-parity.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` + `/verify` 에서 natural-language show-only reload 경로와 `load_web_search_record_id` reload 경로가 같은 entity record 에 대해 `claim_coverage` / `claim_coverage_progress_summary` 를 top-level 응답 payload 및 appended session message 에 동일한 값으로 노출한다는 parity 는 이미 닫혔습니다.

같은 가족의 user-visible drift 가 한 층 더 남아 있었습니다. reload 이후의 follow-up 응답 (`load_web_search_record_id + user_text` follow-up, natural-language reload 다음에 붙는 plain follow-up) 은 `_respond_with_active_context()` 를 통과하는데, 이 경로는 top-level `claim_coverage` 와 `claim_coverage_progress_summary` 를 아예 세팅하지 않았습니다. 내부 web-search `active_context` 는 여전히 해당 데이터를 들고 있었지만, 브라우저의 claim-coverage panel / fact-strength bar 는 `app/static/app.js:3165-3215` 에서 top-level response / message `claim_coverage` 만 읽고, `claim_coverage_progress_summary` 는 그 중 보조적으로만 `active_context` fallback 을 사용합니다. 결과적으로 사용자가 reload 이후 follow-up 질문을 던지면 record 맥락은 유지되지만 claim-coverage panel / fact-strength bar 는 사라지는 user-visible drift 가 있었습니다.

이 슬라이스는 해당 remaining reload-contract drift 를 한 바운드의 response-surface propagation 으로 닫습니다. 새 저장소, 새 schema, 새 canonicalizer, 새 browser selector 를 만들지 않고, 이미 존재하는 web-search `active_context` 의 `claim_coverage` / `claim_coverage_progress_summary` 를 `_respond_with_active_context()` 의 `AgentResponse` 생성 지점에서 top-level 필드로 그대로 올려 줍니다. history-card `.meta` composition order, verification label, source-role rendering, 그리고 latest-update / no-claim-coverage 경로의 현재 empty-meta 계약은 건드리지 않습니다.

## 핵심 변경

### `core/agent_loop.py`

`_respond_with_active_context()` 의 최종 `AgentResponse(...)` 생성 직전에 web-search follow-up 전용 propagation 블록을 추가했습니다. 블록은 다음과 같이 동작합니다:

- `active_context.get("kind") == "web_search"` 인 경우에만 활성화됩니다. document / file / generic active_context 는 그대로 두므로 파일 summary, 폴더 검색, 일반 chat follow-up 의 기존 응답 모양은 바뀌지 않습니다.
- `active_context.get("claim_coverage")` 를 dict item 만 dict copy 로 추린 뒤 비어 있지 않을 때에만 top-level 값을 세팅합니다. 이는 latest-update 나 no-claim-coverage entity record 의 기존 empty-meta 계약을 그대로 유지하기 위한 안전 gate 입니다.
- propagation 은 `claim_coverage` list 와, 그에 짝지어 `claim_coverage_progress_summary` 문자열을 stripped 비공란 값일 때에만 top level 로 올려 줍니다. 빈 문자열은 `None` 으로 수렴해 기존 계약과 동일합니다.

이 블록에서 계산된 `follow_up_claim_coverage` 와 `follow_up_progress_summary` 는 기존 `AgentResponse(...)` 호출의 새 인자 `claim_coverage=...`, `claim_coverage_progress_summary=...` 로 전달합니다. 다른 경로는 건드리지 않았고, 결과적으로 `_respond_with_active_context()` 의 document / file / general / web-search 모든 follow-up 응답이 한 함수 안의 한 AgentResponse 생성 지점에서 일관된 top-level 계약을 갖게 됩니다.

부수적으로 `_append_session_message()` 는 기존 truthy-guard (`if response.claim_coverage:` / `if response.claim_coverage_progress_summary:`) 덕분에, entity record 기반 reload-follow-up 은 이제 appended assistant message 에도 `claim_coverage` 와 `claim_coverage_progress_summary` 를 함께 실어 줍니다. latest-update 계열 follow-up 은 여전히 top-level 값이 비어 있으므로 append 쪽에서도 자동으로 제외됩니다. `_reuse_web_search_record()`, `_build_web_search_active_context()`, `canonicalize_legacy_*` helper 군, serializer, browser selector, history-card `.meta` 관련 코드는 건드리지 않았습니다.

### 회귀 — `tests/test_smoke.py`

- `test_reload_follow_up_propagates_top_level_claim_coverage_from_active_context` 를 추가했습니다. 이 테스트는 두 축의 확인을 한 케이스에 묶습니다.
  - entity-card 경로: `WebSearchStore.save(...)` 로 `이용 형태 weak / 개발 weak` claim_coverage + `재조사했지만 이용 형태는 아직 단일 출처 상태입니다.` progress summary 를 갖는 record 를 seed 한 뒤, `UserRequest(user_text="이 결과 더 설명해줘", metadata={"load_web_search_record_id": ...})` 로 reload-follow-up 을 호출하고 `response.actions_taken` 에 `load_web_search_record` 가 포함되는지, `response.claim_coverage` 가 `이용 형태` slot 을 포함하는지, `response.claim_coverage_progress_summary` 가 저장값과 완전히 일치하는지를 lock 합니다. 이 경로는 show-only 가 아닌 `_respond_with_active_context()` 를 통과합니다.
  - latest-update 경로: `서울 날씨` record 를 비어 있는 claim_coverage 와 빈 progress_summary 로 seed 한 뒤 `UserRequest(user_text="이 결과 한 번 더 설명해줘", metadata={"load_web_search_record_id": ...})` 로 reload-follow-up 을 돌리고, 이어서 plain `UserRequest(user_text="내일 날씨는?")` follow-up 도 돌려, 두 응답 모두 `claim_coverage == []` 와 `claim_coverage_progress_summary is None` 을 유지하는지 lock 합니다. 이는 gate 조건이 entity-card 와 latest-update 를 정확히 구분함을 보장합니다.

### 회귀 — `tests/test_web_app.py`

- `test_handle_chat_reload_follow_up_propagates_top_level_claim_coverage_and_progress_summary` 를 추가했습니다. `load_web_search_record_id + user_text="이 결과 더 설명해줘"` 경로로 WebAppService.handle_chat 을 호출하고, `result["response"]["claim_coverage"]` 안에 `이용 형태` slot 이 포함되는지, `result["response"]["claim_coverage_progress_summary"]` 가 저장값과 일치하는지, 그리고 `result["session"]["messages"]` 의 마지막 assistant 메시지에도 같은 `claim_coverage` slot 과 `claim_coverage_progress_summary` 가 persist 되는지 lock 합니다.
- `test_handle_chat_natural_language_reload_then_follow_up_keeps_top_level_claim_coverage` 를 추가했습니다. 첫 호출에서 `user_text="방금 검색한 결과 다시 보여줘"` 로 natural-language reload 를 먼저 돌려 web-search active_context 를 세팅하고, `store.list_session_record_summaries(session_id)` 에서 record_id 를 다시 꺼내 두 번째 호출에서 `user_text="이 결과 더 설명해줘"` + 해당 record_id 조합으로 reload-follow-up 을 호출합니다. 두 번째 호출의 `response` payload 와 appended assistant message 에서 top-level `claim_coverage` slot / progress_summary 가 저장값과 정합한지를 lock 합니다.
- `test_handle_chat_latest_update_reload_follow_up_keeps_claim_coverage_surfaces_empty` 를 추가했습니다. latest-update 계열 record (`claim_coverage=[]`, empty progress_summary) 를 seed 한 뒤 reload-follow-up 을 호출하고, `result["response"]["claim_coverage"]` 가 `[]` 를 유지하고 `claim_coverage_progress_summary` 는 빈 문자열이며, 마지막 assistant message 의 `claim_coverage` 값도 비어 있고 `claim_coverage_progress_summary` 는 falsy 임을 확인합니다. 메시지 serializer 가 key 를 비워 둔 채 포함할 수 있으므로, 존재 여부 대신 user-visible 공란 계약을 assert 합니다.

### 문서 sync

- `docs/PRODUCT_SPEC.md` 의 weak-slot reinvestigation baseline 문장과 `docs/ACCEPTANCE_CRITERIA.md` 의 `Browser MVP` shipped `claim coverage` bullet 에 한 문장씩 더 추가해, reload-follow-up 경로 (`load_web_search_record_id + user_text` 와 natural-language reload 다음의 plain follow-up) 도 내부 web-search active_context 에서 동일한 top-level `claim_coverage` 와 `claim_coverage_progress_summary` 를 propagate 하여 claim-coverage panel / fact-strength bar 가 reload-follow-up chain 내내 유지된다는 계약과, latest-update / no-claim-coverage 경로는 여전히 top-level 필드를 비워 두어 기존 empty-meta 계약을 widening 하지 않는다는 점을 명시했습니다.

controller / pipeline / watcher / runtime, 다른 docs family, `work`/`verify` 이전 항목, `e2e/tests/web-smoke.spec.mjs`, browser selector, `app/static/app.js`, history-card `.meta` composition 은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `python3 -m py_compile core/agent_loop.py app/serializers.py tests/test_smoke.py tests/test_web_app.py` → 성공.
- `python3 -m unittest tests.test_smoke tests.test_web_app` → `Ran 362 tests … OK`. 108 smoke + 250 web_app + 4 신규 회귀 (smoke 1 + web_app 3) 까지 전부 통과. 기존 reload-family, reinvestigation, progress-summary, 그리고 이 슬라이스의 새 reload-follow-up 회귀가 동시에 OK.
- 요구된 회귀 재실행 배치로 직전 parity regression (`test_entity_reinvestigation_query_reports_claim_progress`, `test_natural_language_reload_exposes_top_level_claim_coverage_progress_summary`, `test_handle_chat_natural_language_reload_top_level_claim_coverage_progress_summary_parity`, `test_handle_chat_natural_language_reload_session_message_preserves_top_level_progress_summary`) 를 동일 배치에서 재실행해 `Ran 4 tests … OK` 를 확인했습니다.
- 이 슬라이스가 추가한 네 회귀 (`test_reload_follow_up_propagates_top_level_claim_coverage_from_active_context`, `test_handle_chat_reload_follow_up_propagates_top_level_claim_coverage_and_progress_summary`, `test_handle_chat_natural_language_reload_then_follow_up_keeps_top_level_claim_coverage`, `test_handle_chat_latest_update_reload_follow_up_keeps_claim_coverage_surfaces_empty`) 를 개별 및 배치로 실행해 전부 OK.
- `git diff --check -- core/agent_loop.py app/static/app.js tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md work/4/11` → whitespace 경고 없음.
- 브라우저 계약 (claim-coverage panel / fact-strength bar / history-card `.meta` composition / verification label / source-role rendering / selector) 는 이 슬라이스에서 건드리지 않았습니다. 변경 범위는 한 함수 안의 propagation 블록 + AgentResponse 두 개 인자 + 단위 회귀 네 개뿐이라 Playwright `make e2e-test` 는 이번 라운드에 과하여 실행하지 않았습니다.

## 남은 리스크

- propagation 은 `active_context.get("kind") == "web_search"` 게이트에만 의존합니다. 미래에 다른 retrieval kind 가 entity-card claim_coverage 를 가진 active_context 를 만들게 되면 그 경로도 동일 propagation 을 추가하거나 gate 를 확장해야 합니다. 지금은 오로지 web-search active_context 만 entity-card claim_coverage 를 생성하므로 현재 가정이 맞지만, routing 이 바뀔 수 있습니다.
- `_respond_with_active_context()` 는 retry-feedback 재검색, evidence pool 필터링 등 여러 분기를 가집니다. 내부 재검색 분기가 새 `active_context` 로 replace 하고 그 결과를 반환하는 경로 (e.g. `_retry_web_search_after_irrelevant_feedback`) 는 별도의 AgentResponse 를 돌려줍니다. 이번 슬라이스는 그 분기를 건드리지 않았으므로, retry-feedback 재검색이 reload-follow-up 으로 치환될 때에도 top-level claim_coverage parity 를 유지하려면 그 경로에서도 같은 propagation 이 필요할 수 있습니다. 다만 그것은 현재 user-visible drift 가 아니므로 이번 범위 밖입니다.
- `_append_session_message()` 의 truthy-guard 덕분에 latest-update 계열 reload-follow-up 은 appended message 에 `claim_coverage` key 를 실지 않는 게 기본 동작인데, 메시지 serializer 가 key 를 비워 둔 채 다시 붙일 수 있다는 것이 테스트에서 드러났습니다. user-visible 공란 계약은 유지되지만, 빈 list 를 명시적으로 drop 해야 하는지 / 유지해야 하는지에 대한 정책은 이 슬라이스 범위 밖이며, 현재 테스트는 공란 의미만 lock 합니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `controller/server.py`, `pipeline_gui/backend.py`, `watcher_core.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`, `docs/PRODUCT_SPEC.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`, `core/agent_loop.py`, `storage/web_search_store.py`, `verify/4/10/...`, 기존 `work/4/11/`와 `verify/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았습니다.
