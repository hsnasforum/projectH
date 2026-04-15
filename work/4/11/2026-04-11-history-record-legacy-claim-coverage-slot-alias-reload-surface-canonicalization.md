# history-record legacy claim_coverage slot-alias reload-surface canonicalization

## 변경 파일

- `core/agent_loop.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/11/2026-04-11-history-record-legacy-claim-coverage-slot-alias-reload-surface-canonicalization.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work`에서 legacy stored `claim_coverage` slot label (`개발사`, `장르`, `플랫폼`, `출시일`) 에 대한 prompt-selection 쪽 compatibility gap은 이미 닫혔습니다. 하지만 같은 legacy 라벨이 `_reuse_web_search_record()` 의 public reload surface (`response.claim_coverage`, `active_context.claim_coverage`) 와 `_annotate_claim_coverage_progress()` / `_build_claim_coverage_progress_summary()` 의 previous/current slot map 비교에서는 여전히 exact string key 로만 사용되고 있었습니다. 결과적으로 stored record 가 legacy 라벨로 저장되어 있으면 reload 시 old slot name 이 그대로 public 표면에 드러났고, 곧이어 follow-up reinvestigation 이 동일 의미의 core slot 을 돌려줄 때 이전 상태가 사실상 "다른 slot" 으로 보여 `미확인 -> 단일 출처` 같은 false improvement 를 보고할 수 있었습니다.

이번 슬라이스는 같은 legacy 가족의 current-risk 를 한 번 더 마무리하는 범위 내 작업입니다. prompt-selection 쪽 compatibility 는 이미 닫혔고, 이 라운드는 reload surface 와 progress 비교 경로도 동일한 canonicalization 을 공유하도록 좁게 닫습니다. 저장된 history JSON 파일은 그대로 두고, read/use 시점의 in-memory compatibility layer 로만 처리해 schema migration, record 재기록, browser 계약 확장 없이 drift 를 제거합니다. controller / pipeline / watcher / runtime, `e2e/tests/web-smoke.spec.mjs`, browser selector, verification label, source-role rendering 은 건드리지 않습니다.

## 핵심 변경

### `core/agent_loop.py`

- 기존 `_build_entity_reinvestigation_suggestions()` 안에 중복돼 있던 legacy alias 맵을 하나의 shared 출처로 옮겼습니다. `AgentLoop._LEGACY_ENTITY_SLOT_ALIASES` class constant 와 두 개의 classmethod helper (`_canonical_legacy_entity_slot(slot)`, `_canonicalize_legacy_claim_coverage_slots(claim_coverage)`) 를 추가했습니다.
  - `_canonical_legacy_entity_slot` 은 단일 slot 문자열용 canonicalizer 입니다. `_build_entity_reinvestigation_suggestions()` 는 이 helper 를 통해 prompt map 조회를 하도록 바뀌었고, 내부 alias 맵 duplication 을 제거했습니다. live entity search 경로의 현재 core-slot prompt 동작은 변하지 않습니다.
  - `_canonicalize_legacy_claim_coverage_slots` 는 list-of-items 를 받아 legacy slot label 을 canonical core-slot 이름으로 rewrite 한 새 list 를 반환하고, dict 가 아닌 item 은 drop 하며, 이미 canonical 한 입력에는 idempotent 하게 동작합니다. 각 item 의 나머지 metadata (`status`, `status_label`, `value`, `support_count`, `source_role`, `rendered_as`, 기타) 는 dict copy 로 그대로 유지됩니다.
- `_reuse_web_search_record()` 의 stored_claim_coverage load 지점을 `self._canonicalize_legacy_claim_coverage_slots(...)` 로 감쌌습니다. 이 한 지점으로 reload 가 돌려주는 `response.claim_coverage`, `_build_web_search_active_context()` 내부의 `claim_coverage`, `active_context.claim_coverage`, 그리고 그 다음 reinvestigation 단계가 `previous_active_context.get("claim_coverage")` 로 꺼내 쓰는 값까지 모두 canonical slot name 으로 표면화됩니다.
- `_annotate_claim_coverage_progress()` 와 `_build_claim_coverage_progress_summary()` 는 입력받은 `previous_claim_coverage` 와 `current_claim_coverage` 를 `self._canonicalize_legacy_claim_coverage_slots(...)` 로 한 번씩 통과시켜 previous/current map 을 만들기 전에 canonical slot 으로 align 하도록 했습니다. 이로써 reload 경로가 아직 canonical 화되지 않은 legacy 목록을 직접 전달하더라도, 혹은 persisted record 가 future drift 로 다시 legacy 라벨을 가져오더라도 progress 비교가 동일한 canonical basis 위에서 이뤄집니다. `이용 형태: weak` 이전 상태와 `이용 형태: weak` 현재 상태를 비교하면 기존처럼 `unchanged` / `재조사했지만 이용 형태는 아직 단일 출처 상태입니다.` 로 수렴합니다.

persisted history JSON file 이나 `WebSearchStore` 저장 경로는 건드리지 않았습니다. alias 는 read/use 시점에만 적용됩니다.

### `tests/test_smoke.py`

`test_stored_response_origin_controls_reloaded_answer_mode` 뒤, 기존 `test_load_web_search_record_legacy_claim_coverage_slots_keep_reinvestigation_suggestions` 뒤에 새로운 AgentLoop regression `test_load_web_search_record_legacy_claim_coverage_slots_reload_surface_and_follow_up_progress_canonicalized` 를 추가했습니다. 이 테스트는:

- `WebSearchStore.save(...)` 로 entity-card record 를 `개발사` weak, `장르` weak, `플랫폼` weak, `출시일` missing 의 legacy slot 라벨과 함께 직접 저장합니다.
- `방금 검색한 결과 다시 보여줘` 자연어 reload 경로를 통해 `AgentLoop.handle(...)` 을 호출한 뒤, `reload_response.actions_taken == ["load_web_search_record"]` 를 확인하고 `response.claim_coverage` 의 slot set 이 정확히 `{"개발", "장르/성격", "이용 형태", "상태"}` 임을 assertion 합니다. 네 legacy 라벨 중 어느 것도 public surface 에 leak 되지 않아야 합니다.
- 같은 `loop` 인스턴스의 `_annotate_claim_coverage_progress()` 와 `_build_claim_coverage_progress_summary()` 를 legacy previous (`플랫폼: weak`, `개발사: weak`, `장르: weak`, `출시일: missing`) + canonical current (`이용 형태: weak`, `개발: weak`, `장르/성격: weak`, `상태: missing`) 조합으로 호출해 `이용 형태` slot 의 `progress_state == "unchanged"`, `progress_label == "유지"`, `previous_status == "weak"`, `is_focus_slot == True` 를 확인하고, summary 가 `재조사했지만 ... 이용 형태는 아직 ... 단일 출처 상태입니다.` 형태를 유지하며 `보강` / `미확인에서` 같은 false improvement 문구를 포함하지 않음을 lock 합니다.

기존 `test_entity_reinvestigation_query_reports_claim_progress` 와 `test_load_web_search_record_legacy_claim_coverage_slots_keep_reinvestigation_suggestions` 는 그대로 두었습니다.

### `tests/test_web_app.py`

`test_handle_chat_entity_card_dual_probe_reload_preserves_active_context_source_paths` 앞, 기존 legacy-slot reinvestigation-suggestions 테스트 뒤에 새로운 WebAppService regression `test_handle_chat_load_web_search_record_id_legacy_claim_coverage_slots_surface_canonical_slots_and_truthful_progress` 를 추가했습니다. 이 테스트는:

- 동일한 legacy slot 라벨 네 개를 가진 entity-card record 를 `WebSearchStore(base_dir=...)` 에 직접 저장합니다.
- `WebAppService.handle_chat({"load_web_search_record_id": record_id, ...})` 경로로 reload 하고, 직렬화된 `result["session"]["messages"][-1]["claim_coverage"]` 의 slot set 이 정확히 `{"개발", "장르/성격", "이용 형태", "상태"}` 임을 확인합니다. 이는 browser 에서 직접 보이는 public 표면에서도 legacy 라벨이 사라졌음을 보장합니다.
- shared progress helper 동작을 동일 test 안에서 검증하기 위해 `AgentLoop.__new__(AgentLoop)` 로 instance state 가 필요 없는 bare helper loop 을 만들고 `_build_claim_coverage_progress_summary()` 를 legacy previous + canonical current 조합으로 호출해 `재조사했지만` / `이용 형태` / `아직` / `단일 출처 상태` literal 을 포함하고 `보강` / `미확인에서` 는 포함하지 않음을 lock 합니다. 이는 `AgentLoop._normalize_legacy_summary_headers` 를 같은 파일에서 이미 static 스타일로 호출하는 기존 패턴과 동일 계열의 접근입니다.

### `docs/PRODUCT_SPEC.md`

`Response Transparency Contract` 의 `weak-slot reinvestigation baseline` 줄을, 이번 slice 가 추가로 닫은 세 surface (reinvestigation prompt 선택, reload response `claim_coverage` 공개 표면, reload-follow-up progress 비교) 가 같은 canonical core-slot 기준으로 동작한다는 한 문장과 "persisted history JSON 은 재작성되지 않고 read/use 시점의 compatibility layer 로만 처리된다" 는 범위 한정 문장으로 확장했습니다.

### `docs/ACCEPTANCE_CRITERIA.md`

`Browser MVP` shipped 계약 `claim coverage` bullet 도 동일한 방향으로 갱신했습니다. stored entity record 가 legacy `claim_coverage` slot label 을 가진 경우에도 reload 응답에 canonical core-slot 이름만 드러나며, reload-follow-up progress 가 truthful `unchanged` / `재조사했지만 ... 아직 단일 출처 상태입니다` 형태를 유지하고 false `미확인 -> 단일 출처` improvement 를 보고하지 않는다는 계약을, persistent history JSON 은 재작성되지 않는다는 범위 한정과 함께 명시했습니다.

controller / pipeline / watcher / runtime 코드, 다른 docs family, `work`/`verify`, `e2e/tests/web-smoke.spec.mjs`, browser selector 는 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` → 성공
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_entity_reinvestigation_query_reports_claim_progress` → `Ran 1 test … OK`. live entity search reinvestigation 경로가 회귀되지 않았음을 확인했습니다.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_load_web_search_record_legacy_claim_coverage_slots_keep_reinvestigation_suggestions` → `Ran 1 test … OK`. 직전 슬라이스가 닫은 suggestion 계약이 그대로 유지됨을 확인했습니다.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_load_web_search_record_legacy_claim_coverage_slots_reload_surface_and_follow_up_progress_canonicalized` → `Ran 1 test … OK`. 이번 슬라이스의 AgentLoop reload-surface + reload-follow-up progress 회귀를 lock 했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_legacy_claim_coverage_slots_keep_reinvestigation_suggestions` → `Ran 1 test … OK`. 기존 WebAppService 회귀가 그대로 통과함을 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_legacy_claim_coverage_slots_surface_canonical_slots_and_truthful_progress` → `Ran 1 test … OK`. 이번 슬라이스의 `load_web_search_record_id` canonical slot / truthful progress 회귀를 lock 했습니다.
- 요구 `unittest` 명령을 두 세트 한 번 더 묶어 실행했을 때 `Ran 5 tests … OK`. 기존 세 테스트 + 신규 두 테스트가 같은 배치에서도 통과함을 재확인했습니다.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md work/4/11` → whitespace 경고 없음.
- 브라우저 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright `make e2e-test` 는 이번 라운드에 과하여 실행하지 않았습니다. history-card `.meta`, verification label, source-role rendering 은 이번 변경의 출력 경로가 아닙니다.

## 남은 리스크

- compatibility layer 는 여전히 in-memory read/use 시점 rewrite 입니다. stored history JSON file 은 legacy slot 라벨을 계속 가지고 있을 수 있으며, persistent schema migration 이 미래에 필요해진다면 별도 라운드가 필요합니다.
- `_LEGACY_ENTITY_SLOT_ALIASES` 는 현재 네 legacy 라벨만 커버합니다. 추후 더 많은 legacy 라벨이 발견되거나 schema 에 새 core slot 이 추가되면 같은 class-level 맵을 확장해야 합니다.
- `_annotate_claim_coverage_progress` 와 `_build_claim_coverage_progress_summary` 의 canonicalization 은 defense-in-depth 성격입니다. reload path 가 이미 canonical 슬롯을 만들어 active_context 에 올려두는 상태에서는 대부분 idempotent 하게 지나가며, 실제로 legacy 라벨이 들어오는 유일한 경로는 stored record → reload surface 한쪽뿐입니다. 나중에 다른 진입점이 생긴다면 그 새 진입점에서도 동일 helper 를 쓰도록 보증해야 합니다.
- `출시일 -> 상태` 매핑은 여전히 release-date 와 availability status 를 한 core slot 에 수렴시킵니다. UX 적으로 두 intent 를 분리해야 할 필요가 생기면 별도 slot 확장 라운드에서 다뤄야 합니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `controller/server.py`, `pipeline_gui/backend.py`, `watcher_core.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`, `docs/PRODUCT_SPEC.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`, `core/agent_loop.py`, `verify/4/10/...`, 기존 `work/4/11/`와 `verify/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았습니다.
