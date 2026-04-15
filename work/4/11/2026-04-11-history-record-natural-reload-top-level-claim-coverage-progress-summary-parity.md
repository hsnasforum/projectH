# history-record natural-reload top-level claim_coverage_progress_summary parity

## 변경 파일

- `core/agent_loop.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/11/2026-04-11-history-record-natural-reload-top-level-claim-coverage-progress-summary-parity.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` + `/verify` 에서 legacy stored `claim_coverage_progress_summary` 텍스트를 reload `active_context` 와 `session.web_search_history` history-card metadata 양쪽에서 canonical core-slot 으로 정돈하는 read/use-time compatibility layer 는 이미 닫혔습니다. 같은 record 를 `load_web_search_record_id` 로 불러와도 `active_context` 경로는 canonical 문구를 그대로 드러냅니다.

하지만 같은 가족의 user-visible drift 가 한 층 더 남아 있었습니다. `_reuse_web_search_record()` 의 natural-language show-only reload 분기는 `claim_coverage` 는 top level 에 실어 줬지만 `claim_coverage_progress_summary` 는 완전히 생략했고 (`core/agent_loop.py:6435-6449`), 그 때문에 canonical progress 텍스트가 오직 `active_context` 를 통해서만 생존했습니다. serializer 는 top-level response 필드를 그대로 `AgentResponse` 에서만 가져오고 (`app/serializers.py:62-65`), session-message append 도 top-level `response.claim_coverage_progress_summary` 가 있을 때에만 message 에 실어 줍니다 (`core/agent_loop.py:7427-7430`). 결과적으로 `load_web_search_record_id` reload 경로와 natural-language reload 경로는 동일 stored record 에 대해 response / message payload 모양이 달랐습니다.

이 슬라이스는 해당 remaining reload-contract drift 를 한 바운드의 parity 변경으로 닫습니다. 새 alias 체계나 새 canonicalization 경로를 만들지 않고, 이미 canonical 로 내려와 있는 `claim_coverage_progress_summary` 를 natural-language show-only reload 분기의 `AgentResponse` 생성 지점에 그대로 실어 주기만 합니다. persisted history JSON 은 여전히 건드리지 않고, history-card `.meta` composition order, verification label, source-role rendering, browser selector, latest-update / 다른 runtime 가족 범위 확장도 없습니다.

## 핵심 변경

### `core/agent_loop.py`

`_reuse_web_search_record()` 의 show-only reload 분기에서 반환하는 `AgentResponse` 생성 호출에 한 줄을 추가했습니다:

```
claim_coverage=claim_coverage,
claim_coverage_progress_summary=claim_coverage_progress_summary,
response_origin=reload_origin,
```

이 `claim_coverage_progress_summary` 변수는 직전 슬라이스가 이미 canonical 로 정돈해 둔 값입니다 (`stored_progress_summary = canonicalize_legacy_claim_coverage_progress_summary(...)` → `claim_coverage_progress_summary = stored_progress_summary or None`). 같은 값을 `_build_web_search_active_context(..., claim_coverage_progress_summary=...)` 에 전달하고 있었기 때문에 이번 한 줄 추가만으로 top level 과 `active_context` 가 완전히 동일한 canonical 문자열을 공유합니다.

두 reload 경로가 모두 `_reuse_web_search_record()` 의 show-only 분기를 사용한다는 점에 주목했습니다. `load_web_search_record_id` 만 payload 에 실린 요청은 `app/handlers/chat.py:541-544` 에서 `user_text="최근 웹 검색 기록을 다시 불러와 주세요."` 로 내려가며, 이 문장은 `_reuse_web_search_record()` 의 `show_only` 감지 phrase 목록 (`"다시 보여"`, `"불러와"` 등) 에 매칭됩니다. 따라서 한 곳의 top-level 필드 추가로 `load_web_search_record_id` reload 와 `방금 검색한 결과 다시 보여줘` 같은 natural-language reload 가 똑같은 `AgentResponse` 형태를 공유하게 됩니다. 그 결과 session-message append (`core/agent_loop.py:7427-7430`) 도 이제 두 경로 모두에서 `message["claim_coverage_progress_summary"]` 를 붙일 수 있고, serializer 도 두 경로 모두에서 `response.claim_coverage_progress_summary` 를 그대로 실어 줍니다.

`_respond_with_active_context()`, `_build_web_search_active_context()`, `_canonicalize_legacy_claim_coverage_slots()`, `canonicalize_legacy_claim_coverage_progress_summary()` 는 건드리지 않았습니다. 이번 slice 는 새 helper 없이 parity 한 줄만 닫는 것입니다.

### 회귀 — `tests/test_smoke.py`

- `test_natural_language_reload_exposes_top_level_claim_coverage_progress_summary` 를 추가했습니다. `WebSearchStore.save(..., claim_coverage_progress_summary="재조사했지만 이용 형태는 아직 단일 출처 상태입니다.")` 로 저장된 record 를 `방금 검색한 결과 다시 보여줘` 자연어 reload 로 불러온 뒤, `response.actions_taken == ["load_web_search_record"]` 경로 고정 + `response.claim_coverage` 안에 `이용 형태` slot + `response.claim_coverage_progress_summary` 가 저장값과 정확히 같음 + `response.active_context["claim_coverage_progress_summary"]` 도 같은 값임을 lock 합니다. 즉 top-level / active_context 두 surface 가 같은 canonical 문자열을 노출하는지 확인합니다.

### 회귀 — `tests/test_web_app.py`

- `test_handle_chat_natural_language_reload_top_level_claim_coverage_progress_summary_parity` 를 추가했습니다. 동일한 stored record 를 store 에 직접 save 한 뒤 `WebAppService.handle_chat({"user_text": "방금 검색한 결과 다시 보여줘", ...})` 로 natural-language reload 를 호출하고, 직렬화된 `result["response"]["claim_coverage_progress_summary"]` 와 `result["response"]["claim_coverage"]` 안의 `이용 형태` slot, 그리고 `result["session"]["active_context"]["claim_coverage_progress_summary"]` 를 함께 검증합니다. 이 테스트는 natural-language reload 가 이제 `load_web_search_record_id` reload 와 동일한 top-level 응답 모양을 갖는지, 그리고 active_context 계약이 유지되는지 lock 합니다.

- `test_handle_chat_natural_language_reload_session_message_preserves_top_level_progress_summary` 를 추가했습니다. 동일한 natural-language reload 를 호출한 뒤 `result["session"]["messages"]` 의 마지막 assistant 메시지에서 `claim_coverage_progress_summary` 가 저장값과 정확히 일치하고, `claim_coverage` 안에 `이용 형태` slot 이 포함됨을 lock 합니다. 이는 `_append_session_message()` 가 top-level `response.claim_coverage_progress_summary` 가 존재할 때만 메시지에 실어 주는 기존 계약 덕분에, top-level 필드가 채워졌다는 사실을 통해 session-message append 경로까지 truthful 하게 통과하는지를 검증합니다.

### 문서 sync

- `docs/PRODUCT_SPEC.md` 의 weak-slot reinvestigation baseline 문장과 `docs/ACCEPTANCE_CRITERIA.md` 의 `Browser MVP` shipped `claim coverage` bullet 에 한 문장씩 덧붙여, `load_web_search_record_id` reload 경로와 natural-language show-only reload 경로 양쪽이 `claim_coverage` 와 `claim_coverage_progress_summary` 를 top-level 응답 payload 및 appended session message 에 동일한 값으로 노출한다는 reload-contract parity 를 명시했습니다. "persisted history JSON 은 재작성되지 않는다" 는 범위 한정 문구는 그대로 유지했습니다. 새 계약 용어, 새 alias 체계, 새 browser contract 는 도입하지 않았습니다.

controller / pipeline / watcher / runtime, 다른 docs family, `work`/`verify` 이전 항목, `e2e/tests/web-smoke.spec.mjs`, browser selector, history-card `.meta` composition 은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `python3 -m py_compile core/agent_loop.py app/serializers.py tests/test_smoke.py tests/test_web_app.py` → 성공.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_entity_reinvestigation_query_reports_claim_progress` → `Ran 1 test … OK`. live entity search reinvestigation 경로 회귀 없음.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_natural_language_reload_exposes_top_level_claim_coverage_progress_summary` → `Ran 1 test … OK`. AgentLoop natural-language reload top-level progress-summary parity 회귀를 lock.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_top_level_claim_coverage_progress_summary_parity` → `Ran 1 test … OK`. WebAppService natural-language reload `response` payload / `active_context` parity 회귀를 lock.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_session_message_preserves_top_level_progress_summary` → `Ran 1 test … OK`. appended session message 의 top-level progress-summary 보존 회귀를 lock.
- 추가로 직전 슬라이스의 `test_load_web_search_record_legacy_progress_summary_text_canonicalized_on_reload` 와 `test_handle_chat_load_web_search_record_id_legacy_progress_summary_text_canonicalized` 도 이 배치에서 같이 `OK` 로 통과함을 확인했습니다 (`Ran 6 tests … OK`). 두 reload 경로가 같은 canonical 텍스트를 공유하게 되었음에도 이전 회귀는 그대로 유지됩니다.
- `git diff --check -- core/agent_loop.py app/serializers.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md work/4/11` → whitespace 경고 없음.
- 브라우저 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright `make e2e-test` 는 이번 라운드에 과하여 실행하지 않았습니다. history-card `.meta` composition order, verification label, source-role rendering, selector 는 이번 변경의 출력 경로가 아니며, 변경 범위는 `AgentResponse` 생성 시점의 한 필드 추가와 그에 대응하는 단위 회귀 세 개뿐입니다.

## 남은 리스크

- 두 reload 경로가 이제 동일한 `AgentResponse` 생성 지점을 공유하는 것은 `_reuse_web_search_record()` 의 show-only 분기가 둘 다 통과한다는 가정에 의존합니다. 미래에 `load_web_search_record_id` 가 show-only phrase 감지를 우회하게 되거나 다른 user_text 로 진입하는 경로가 생기면, 그 경로는 `_respond_with_active_context()` 기반 non-show-only 분기로 넘어갈 수 있고, 거기서는 여전히 top-level `claim_coverage` / `claim_coverage_progress_summary` 가 세팅되지 않습니다. 추가 입력 경로가 생기면 같은 parity 를 별도로 확인해야 합니다.
- `app/serializers.py` 는 이번에 건드리지 않았고, serializer 는 여전히 `response.claim_coverage_progress_summary` 를 그대로 `localize_text(...)` 를 통과시켜 내보냅니다. `localize_text` 의 정책 변화가 있다면 이번 parity 결과가 의도와 다르게 조정될 수 있습니다.
- `_append_session_message()` 는 여전히 `if response.claim_coverage_progress_summary:` 가드 뒤에서만 message 에 필드를 실어 줍니다. 따라서 stored record 가 빈 progress-summary 를 가진 경우 appended message 에 필드가 없는 현재 동작은 그대로 유지됩니다. 빈 progress-summary 를 명시적으로 drop 하는지 유지하는지에 대한 정책은 이 슬라이스 범위 밖입니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `controller/server.py`, `pipeline_gui/backend.py`, `watcher_core.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`, `docs/PRODUCT_SPEC.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`, `core/agent_loop.py`, `storage/web_search_store.py`, `verify/4/10/...`, 기존 `work/4/11/`와 `verify/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았습니다.
