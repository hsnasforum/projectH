# history-record legacy claim_coverage progress-summary slot-alias canonicalization

## 변경 파일

- `core/agent_loop.py`
- `storage/web_search_store.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/11/2026-04-11-history-record-legacy-claim-coverage-progress-summary-slot-alias-canonicalization.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` + `/verify` 에서 legacy stored `claim_coverage` slot 라벨 (`개발사`, `장르`, `플랫폼`, `출시일`) 을 item 수준에서 canonical core-slot 으로 정돈하는 compatibility layer 는 이미 닫혔습니다. `_reuse_web_search_record()` 의 reload surface, `_annotate_claim_coverage_progress()` / `_build_claim_coverage_progress_summary()` 의 previous/current 비교, `_build_entity_reinvestigation_suggestions()` 의 prompt 선택은 모두 동일한 shared helper 를 통해 canonical slot 기준으로 동작합니다.

하지만 같은 가족의 user-visible drift 가 한 층 더 남아 있었습니다. 저장된 `claim_coverage_progress_summary` 텍스트 자체 (예: `재조사했지만 플랫폼은 아직 단일 출처 상태입니다.`) 는 `_reuse_web_search_record()` 가 그대로 forwarding 하고, `WebSearchStore.list_session_record_summaries()` 가 그대로 emit 하고, `app/serializers.py` 가 그대로 pass-through 하며, `app/static/app.js` 가 history-card `.meta` 에 그대로 append 합니다. 결과적으로 canonical `claim_coverage` item 은 `이용 형태` 로 표면화되는데도, 같은 응답의 `claim_coverage_progress_summary` 와 history-card `.meta` progress 텍스트는 여전히 legacy slot 이름 (`플랫폼`, `개발사`, `장르`, `출시일`) 을 노출할 수 있었습니다.

이 슬라이스는 해당 remaining public-text drift 를 read/use 시점의 한 가지 compatibility 경로로 한 번에 닫습니다. persisted history JSON file 은 그대로 두고, stored progress-summary 텍스트가 공개 표면 (reload response `active_context`, `session.web_search_history` history-card metadata) 으로 나갈 때에만 legacy slot 토큰을 canonical core-slot 이름으로 in-memory 재작성합니다. schema migration, record 재기록, browser selector 변경, history-card `.meta` composition 변경, verification label / source-role rendering 변경, latest-update / 다른 runtime 가족 범위 확장 없이 좁게 닫습니다.

## 핵심 변경

### 단일 source-of-truth 매핑 및 progress-summary helper — `storage/web_search_store.py`

- module-level 공개 상수 `LEGACY_ENTITY_SLOT_ALIASES = {"개발사": "개발", "장르": "장르/성격", "플랫폼": "이용 형태", "출시일": "상태"}` 를 추가해 legacy alias 매핑을 단일 출처로 끌어올렸습니다. 이전 슬라이스의 `AgentLoop._LEGACY_ENTITY_SLOT_ALIASES` 는 이제 같은 dict 를 참조하도록 정리했고, item canonicalizer 와 progress-summary canonicalizer 가 동일 매핑을 공유합니다.
- module-level 함수 `canonicalize_legacy_claim_coverage_progress_summary(text)` 를 새로 추가했습니다. 각 legacy 라벨마다 미리 컴파일된 `re.Pattern` 을 돌려 치환하며, `장르` 처럼 canonical (`장르/성격`) 가 legacy 를 prefix 로 포함하는 경우에는 negative lookahead `장르(?!/성격)` 로 guard 하여 이미 canonical 상태인 입력에 재적용해도 `장르/성격/성격` 같은 drift 가 생기지 않게 했습니다. 나머지 세 라벨은 canonical 이 legacy 를 포함하지 않으므로 단순 `re.escape` 치환으로 충분했고, 두 번째 호출에서 no-op 이 됩니다. 공백 / None / 빈 문자열 입력은 `""` 로 정규화됩니다.
- `WebSearchStore.list_session_record_summaries()` 가 `"claim_coverage_progress_summary"` 를 emit 할 때 `canonicalize_legacy_claim_coverage_progress_summary(record.get("claim_coverage_progress_summary"))` 를 통과시키도록 바꿨습니다. `save()`, `list_session_records()`, `get_session_record()`, `_normalize_loaded_record()` 는 건드리지 않았습니다. 즉 persisted JSON 원본은 그대로 남고, `list_session_record_summaries()` 가 만들어 내는 summary dict 의 `claim_coverage_progress_summary` 필드만 canonical 텍스트로 내려갑니다. 이 필드는 `app/serializers.py` 가 `session.web_search_history` 에 그대로 실어 내보내는 경로이므로, history-card `.meta` 에 흘러 들어가는 텍스트가 한 곳에서 일관되게 정돈됩니다.

### Reload surface 정돈 — `core/agent_loop.py`

- `storage.web_search_store` 로부터 `LEGACY_ENTITY_SLOT_ALIASES` 와 `canonicalize_legacy_claim_coverage_progress_summary` 를 import 하도록 했습니다. `AgentLoop._LEGACY_ENTITY_SLOT_ALIASES` 는 이제 같은 dict 를 참조만 하므로 `_canonical_legacy_entity_slot()` / `_canonicalize_legacy_claim_coverage_slots()` 동작은 변하지 않습니다. single-source-of-truth 원칙을 지키려는 의도입니다.
- `_reuse_web_search_record()` 에서 `stored_progress_summary = str(record.get("claim_coverage_progress_summary") or "").strip()` 를 `stored_progress_summary = canonicalize_legacy_claim_coverage_progress_summary(record.get("claim_coverage_progress_summary"))` 로 교체했습니다. 이 단일 변경으로 reload 경로가 `claim_coverage_progress_summary` 를 `_build_web_search_active_context(..., claim_coverage_progress_summary=...)` 에 canonical 텍스트로 전달하게 되고, 곧이어 `_public_active_context()` 를 통해 `AgentResponse.active_context["claim_coverage_progress_summary"]` 에 canonical 텍스트가 실립니다. show-only reload 와 respond-with-active-context reload 양쪽 경로가 동일하게 동작합니다.
- `app/serializers.py` 는 이미 상위 계층 (store → active_context → session history) 에서 canonical 값을 받도록 되어 있으므로 serializer 파일은 이 슬라이스에서 수정하지 않았습니다. 경계마다 중복 canonicalization 을 넣지 않고 한 번만 정규화합니다.

### 회귀 — `tests/test_smoke.py`

- `test_load_web_search_record_legacy_progress_summary_text_canonicalized_on_reload` 를 추가했습니다. `WebSearchStore.save(..., claim_coverage_progress_summary="재조사했지만 플랫폼은 아직 단일 출처 상태입니다.")` 로 저장된 legacy 텍스트가 `방금 검색한 결과 다시 보여줘` 자연어 reload 경로를 통해 `response.active_context["claim_coverage_progress_summary"]` 에 canonical `이용 형태` 로 surface 되는지, 그리고 persisted JSON file 의 `claim_coverage_progress_summary` 는 legacy 문자열 그대로 유지되는지를 함께 확인합니다. `response.actions_taken == ["load_web_search_record"]` 경로 고정과 `재조사했지만` / `아직` / `단일 출처 상태` literal 정합도 같이 lock 합니다.

### 회귀 — `tests/test_web_app.py`

- `test_handle_chat_load_web_search_record_id_legacy_progress_summary_text_canonicalized` 를 추가했습니다. 동일한 legacy progress-summary 텍스트를 store 에 직접 save 한 뒤 `WebAppService.handle_chat({"load_web_search_record_id": record_id})` 로 reload 를 호출하고, `result["session"]["active_context"]["claim_coverage_progress_summary"]` 와 `result["session"]["web_search_history"][*]["claim_coverage_progress_summary"]` (record_id 일치 entry) 양쪽에서 canonical `이용 형태` 텍스트가 나오며 legacy `플랫폼` 이 leak 되지 않는지를 lock 합니다. persisted JSON file 도 legacy 텍스트를 보존함을 확인합니다.
- `test_web_search_store_list_summaries_canonicalizes_legacy_progress_summary_text` 를 추가했습니다. 한 개의 record 가 네 legacy slot 이름 (`개발사`, `플랫폼`, `출시일`, `장르`) 을 모두 포함하는 복합 progress-summary 텍스트를 들고 있을 때 `list_session_record_summaries()` 가 `이용 형태`, `장르/성격`, `상태 미확인`, `개발` 을 모두 canonical 로 바꾸고, `플랫폼` / `출시일` / `개발사` / bare `장르` 어느 것도 leak 하지 않음을 assert 합니다. 추가로 `canonicalize_legacy_claim_coverage_progress_summary(canonical)` 가 idempotent 하게 동일 문자열을 반환하는지와 persisted JSON 원문 유지를 확인해 "read/use 시점 compat layer 만 적용, 저장 파일은 불변" 계약을 lock 합니다.

### 문서 sync

- `docs/PRODUCT_SPEC.md` 의 `Response Transparency Contract` 의 weak-slot reinvestigation baseline 문장을 확장해, legacy slot alias normalization 이 이제 stored `claim_coverage_progress_summary` 공개 텍스트 (reload 경로의 `active_context`, `session.web_search_history` history-card metadata) 까지 포함한다는 점과 canonical 예시 (`재조사했지만 이용 형태는 아직 단일 출처 상태입니다.`) 를 드러냈습니다. "persisted history JSON 은 재작성되지 않는다" 는 범위 한정은 그대로 유지했습니다.
- `docs/ACCEPTANCE_CRITERIA.md` 의 `Browser MVP` shipped 계약 `claim coverage` bullet 에도 같은 취지로 한 문장을 추가했습니다. 같은 record 가 legacy `claim_coverage_progress_summary` 텍스트를 들고 있을 때 reload 응답 `active_context` 와 `session.web_search_history` history-card metadata 모두에서 canonical 문구가 보인다는 점, 그리고 persisted JSON 은 read/use 시점에만 canonical 로 rewrite 된다는 점을 명시했습니다.

controller / pipeline / watcher / runtime, `e2e/tests/web-smoke.spec.mjs`, browser selector, `app/static/app.js`, 다른 docs family, `work`/`verify` 이전 항목은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `python3 -m py_compile core/agent_loop.py storage/web_search_store.py app/serializers.py tests/test_smoke.py tests/test_web_app.py` → 성공.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_entity_reinvestigation_query_reports_claim_progress` → `Ran 1 test … OK`. live entity search reinvestigation 경로 회귀 없음.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_load_web_search_record_legacy_progress_summary_text_canonicalized_on_reload` → `Ran 1 test … OK`. 이번 슬라이스의 AgentLoop natural-reload text canonicalization 회귀를 lock.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_legacy_progress_summary_text_canonicalized` → `Ran 1 test … OK`. `load_web_search_record_id` 경로에서 `active_context` 와 `session.web_search_history` 양쪽 canonical surface 를 lock.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_web_search_store_list_summaries_canonicalizes_legacy_progress_summary_text` → `Ran 1 test … OK`. store-level canonicalization + idempotency + persisted-file immutability 를 lock.
- 추가로 이전 슬라이스들의 회귀 (`test_load_web_search_record_legacy_claim_coverage_slots_keep_reinvestigation_suggestions`, `test_load_web_search_record_legacy_claim_coverage_slots_reload_surface_and_follow_up_progress_canonicalized`, 해당 WebAppService 테스트 두 개, 그리고 기존 `test_web_search_store_list_summaries_includes_claim_coverage_summary` / `test_web_search_history_serializer_includes_claim_coverage_summary`) 를 함께 재실행해 `Ran 6 tests … OK` 를 확인했습니다.
- 요구된 verification 커맨드 두 세트 (compile + `test_entity_reinvestigation_query_reports_claim_progress`) 와 추가된 세 회귀를 한 배치로 `Ran 4 tests … OK` 로 재확인했습니다.
- `git diff --check -- core/agent_loop.py storage/web_search_store.py app/serializers.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md work/4/11` → whitespace 경고 없음.
- 브라우저 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright `make e2e-test` 는 이번 라운드에 과하여 실행하지 않았습니다. history-card `.meta` composition order, verification label, source-role rendering, selector 는 이번 변경의 출력 경로가 아니며, 변경 범위는 store-level 문자열 canonicalization 과 reload-response active_context 한 쌍뿐입니다.

## 남은 리스크

- compatibility layer 는 여전히 read/use 시점의 in-memory rewrite 입니다. persisted history JSON file 은 legacy progress-summary 텍스트를 계속 보존할 수 있으며, persistent schema migration 이 미래에 필요해지면 별도 라운드가 필요합니다.
- `canonicalize_legacy_claim_coverage_progress_summary()` 는 현재 네 legacy 토큰만 다루며, 새로운 legacy 라벨이 발견되거나 core slot 이 추가되면 동일 `LEGACY_ENTITY_SLOT_ALIASES` 맵 한 곳에서 확장해야 합니다. 두 canonicalizer (item 용 / text 용) 가 같은 상수를 공유하므로 drift 위험은 낮지만, 새 정규식 guard 가 필요한 경우 (예: 새 canonical 이 legacy 를 포함하는 경우) `_build_legacy_progress_summary_patterns()` 의 prefix 감지 로직을 같이 점검해야 합니다.
- 이 슬라이스는 regex 기반 치환이므로 stored progress-summary 텍스트에 legacy 토큰이 사람이 쓴 자연어 문장 안에 우연히 들어 있으면 그 자리도 rewrite 됩니다. 실제로는 progress-summary 는 `_build_claim_coverage_progress_summary()` 가 생성한 고정 템플릿 문자열이므로 문맥상 안전하지만, 다른 진입점에서 임의 문자열을 progress-summary 로 주입하는 미래 변화는 이 가정을 깰 수 있습니다.
- serializer (`app/serializers.py`) 는 이번에 건드리지 않았고, 상위 계층이 canonical 값을 주입한다는 단일 가정에 의존합니다. 만약 미래에 serializer 가 store 가 아닌 다른 경로에서 legacy 텍스트를 직접 받는 새 입력을 갖게 된다면 그 진입점에서도 같은 helper 를 적용해야 합니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `controller/server.py`, `pipeline_gui/backend.py`, `watcher_core.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`, `docs/PRODUCT_SPEC.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`, `core/agent_loop.py`, `storage/web_search_store.py`, `verify/4/10/...`, 기존 `work/4/11/`와 `verify/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았습니다.
