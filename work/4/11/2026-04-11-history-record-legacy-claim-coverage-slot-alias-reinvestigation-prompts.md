# history-record legacy claim_coverage slot-alias reinvestigation prompt normalization

## 변경 파일

- `core/agent_loop.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/11/2026-04-11-history-record-legacy-claim-coverage-slot-alias-reinvestigation-prompts.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` + `/verify`가 `docs/NEXT_STEPS.md` browser smoke checkpoint 카운트와 `web-search history card header badges` composition variants까지 same-day browser-docs truth-sync 라인을 root planning doc 선에서도 전부 닫았습니다. 같은 날 docs-only truth-sync는 이미 여러 번 반복된 상태였기 때문에, 또 한 번 더 작은 docs-only micro-slice를 여는 것보다 바운드된 `app.web` 내부 current-risk reduction 한 개를 닫는 편이 맞았습니다.

남아 있는 current-risk 중 하나는 `_reuse_web_search_record()` → `_build_web_search_active_context()` → `_follow_up_suggestions_for_web_search()` → `_build_entity_reinvestigation_suggestions()` 경로에서, 저장된 entity record가 legacy `claim_coverage` slot label (`개발사`, `장르`, `플랫폼`, `출시일`)을 그대로 들고 있을 때 targeted reinvestigation suggestion이 조용히 사라지고 generic web-search fallback만 남는 상황이었습니다. `tests/test_web_app.py:11220-11223` 기존 fixture가 정확히 그 legacy label들을 저장 record에 실어 두고 있어, reload 경로에서 해당 record가 복원되면 현재 core-slot 이름만 알고 있는 `slot_prompt_map`이 legacy label을 인식하지 못했습니다. 이번 슬라이스는 그 한 가지 내부 경로만 한 방향으로 normalize 합니다.

코드, 테스트, docs 변경 모두 entity-card reinvestigation suggestion 선택이라는 좁은 범위에 한정했습니다. claim-coverage schema, history-card `.meta`, verification label, source-role rendering, live entity search 경로의 현재 core-slot prompt는 건드리지 않았습니다.

## 핵심 변경

### `core/agent_loop.py`

`_build_entity_reinvestigation_suggestions()`에 legacy stored slot alias map을 추가했습니다.

```
legacy_slot_aliases = {
    "개발사": "개발",
    "장르": "장르/성격",
    "플랫폼": "이용 형태",
    "출시일": "상태",
}
```

claim_coverage item 의 `slot` 값을 이 alias map 로 `canonical_slot`으로 변환한 뒤 기존 `slot_prompt_map` 에서 prompt 를 조회하도록 했습니다. alias 에 없는 slot 값은 그대로 사용되므로 현재 live entity search 경로의 core-slot prompt 동작은 변하지 않습니다. `출시일` 은 targeted release-date/status reinvestigation prompt 인 `{query} 출시 상태 검색해봐` (현재 `상태` slot 의 prompt) 로 연결됩니다. 이 변경은 단일 shared helper 한 곳에서 이뤄지므로 `AgentLoop` reload 경로와 `WebAppService.handle_chat` `load_web_search_record_id` 경로가 동일한 한 경로를 공유합니다.

### `tests/test_smoke.py`

`test_stored_response_origin_controls_reloaded_answer_mode` 뒤, `test_entity_reinvestigation_query_reports_claim_progress` 앞에 `test_load_web_search_record_legacy_claim_coverage_slots_keep_reinvestigation_suggestions` 를 추가했습니다. 이 테스트는 `WebSearchStore.save(...)` 로 legacy slot label 네 개(`개발사` weak, `장르` weak, `플랫폼` missing, `출시일` missing) claim_coverage 를 직접 주입하고, `방금 검색한 결과 다시 보여줘` 자연어 reload 경로를 통해 `AgentLoop.handle(...)` 을 호출합니다. MISSING 우선 → WEAK 우선 + 저장 index 순서로 정렬되므로 기대 follow_up_suggestions 앞부분이 `[붉은사막 공식 플랫폼 검색해봐, 붉은사막 출시 상태 검색해봐, 붉은사막 개발사 검색해봐, generic 첫 프롬프트]` 임을 lock 합니다. (targeted suggestion 은 최대 3개로 cap 되므로 `장르` 는 generic fallback 뒤로 밀립니다.)

### `tests/test_web_app.py`

`test_handle_chat_entity_card_dual_probe_reload_preserves_active_context_source_paths` 앞에 `test_handle_chat_load_web_search_record_id_legacy_claim_coverage_slots_keep_reinvestigation_suggestions` 를 추가했습니다. 이 테스트는 `WebSearchStore(base_dir=...)` 로 같은 legacy slot claim_coverage record 를 직접 저장하고, `WebAppService.handle_chat({"load_web_search_record_id": record_id, ...})` 경로로 호출하여 `result["response"]["follow_up_suggestions"][:3]` 가 targeted `공식 플랫폼` / `출시 상태` / `개발사` 삼중으로 나오는지, 그리고 `장르 검색해봐` 가 (cap 으로 인해) 최종 list 에서 빠졌는지 확인합니다. 이는 `WebAppService` 가 동일한 shared helper 를 거쳐 동일 결과를 내는지 보증합니다.

### `docs/PRODUCT_SPEC.md`

`Response Transparency Contract` (`weak-slot reinvestigation baseline`) 줄에 legacy stored `claim_coverage` slot label (`개발사`, `장르`, `플랫폼`, `출시일`) 이 reload / reload-follow-up 경로에서 reinvestigation prompt 선택을 위해 current core slot (`개발`, `장르/성격`, `이용 형태`, `상태`) 으로 normalize 된다는 한 문장을 덧붙였습니다. live entity search 의 현재 core-slot prompt 는 변하지 않았다는 범위 제한도 문구로 드러냈습니다.

### `docs/ACCEPTANCE_CRITERIA.md`

`Browser MVP` shipped 계약 `claim coverage` bullet 에 같은 legacy slot alias normalization 문장을 추가했습니다. user-visible 효과는 history-record reload 경로에서도 targeted reinvestigation suggestion 이 유지된다는 점이며, generic web-search fallback 으로 silent drop 되지 않는다는 contract 로 명시했습니다.

controller / pipeline / watcher / runtime 코드, `e2e/tests/web-smoke.spec.mjs`, pipeline docs, 다른 docs family 는 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` → 성공
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_entity_reinvestigation_query_reports_claim_progress` → `Ran 1 test … OK`, live entity search reinvestigation 경로 회귀 없음 확인.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_load_web_search_record_legacy_claim_coverage_slots_keep_reinvestigation_suggestions tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_legacy_claim_coverage_slots_keep_reinvestigation_suggestions` → `Ran 2 tests … OK`, AgentLoop reload path 와 WebAppService `load_web_search_record_id` path 에서 legacy slot label 이 targeted suggestion 으로 normalize 됨을 확인.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md work/4/11` → whitespace 경고 없음.
- 브라우저 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright `make e2e-test` 는 이번 라운드에 과하여 실행하지 않았습니다. history-card `.meta`, verification label, source-role rendering 어느 쪽도 이번 변경의 출력 경로가 아닙니다.

## 남은 리스크

- `_build_entity_reinvestigation_suggestions` 는 여전히 `slot_prompt_map` 의 현재 core-slot 이름만 source-of-truth 로 삼고, legacy alias 는 reload 전용 compatibility layer 로 한쪽에서만 normalize 합니다. 앞으로 schema 에 새 slot 을 추가하거나 legacy label 추가가 필요해지면 alias map 역시 같은 위치에서 확장해야 합니다.
- `출시일` 을 `상태` prompt 로 매핑한 결과, 사용자에게 반환되는 재조사 제안은 `출시 상태 검색해봐` 로 표면화됩니다. 이는 release-date/status 라는 한 쌍의 intent 를 현재 core-slot prompt 내에서 가장 가까운 targeted 질의로 수렴시킨 것이며, 별도의 `출시일` 전용 프롬프트를 분리하지는 않았습니다. 추후 release-date 전용 문구가 UX 적으로 구분이 필요해지면 별도 slot 확장 라운드에서 다룰 수 있습니다.
- 기존 live entity search 경로의 `claim_coverage` slot 이름은 `core/agent_loop.py` 의 core-slot 생성 로직이 계속 결정하며, 이번 변경은 그 경로를 건드리지 않았습니다. 따라서 현재 live search 가 core-slot 이름을 legacy label 로 reverse-drift 하는지 여부는 이 라운드에서 확인하지 않았고, 해당 감시는 기존 회귀 커버리지에 맡깁니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `controller/server.py`, `pipeline_gui/backend.py`, `watcher_core.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`, `docs/PRODUCT_SPEC.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`, `core/agent_loop.py`, `verify/4/10/...`, 기존 `work/4/11/`와 `verify/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았습니다.
