# history-record plain-follow-up claim_coverage parity regressions

## 변경 파일

- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `work/4/11/2026-04-11-history-record-plain-follow-up-claim-coverage-parity-regressions.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` 는 `_respond_with_active_context()` 에 web-search follow-up propagation 을 추가하여 reload-follow-up 응답이 top-level `claim_coverage` / `claim_coverage_progress_summary` 를 유지하도록 닫았습니다. 실제 shipped 동작은 이 슬라이스 이후에도 올바르게 동작합니다. 그러나 그 `/work` 는 `test_handle_chat_natural_language_reload_then_follow_up_keeps_top_level_claim_coverage` 가 "natural-language reload → 다음 plain follow-up" 경로를 커버한다고 기술했지만, 실제로는 두 번째 호출에도 `load_web_search_record_id` 를 함께 실어 주고 있어서 브라우저가 실제로 타는 plain-follow-up 경로 — 즉 reload 이후 사용자가 record id 를 다시 보내지 않고 일반 질문만 이어가는 흐름 — 를 직접 lock 하지 못했습니다.

구현은 이미 맞고, 남아 있는 current-risk 는 제품 버그가 아니라 현재 shipped user-visible 경로에 대한 proof gap 입니다. 이 슬라이스는 tests-only 로 해당 정확한 plain-follow-up 경로에 대한 회귀를 추가해 `/work`, 실제 coverage, 그리고 현재 구현이 한 지점에서 일치하도록 닫습니다. 구현, 제품 문서, browser selector, pipeline/runtime 범위는 건드리지 않습니다.

## 핵심 변경

### `tests/test_web_app.py`

두 개의 새 회귀를 `test_handle_chat_entity_card_dual_probe_reload_preserves_active_context_source_paths` 앞에 추가했습니다.

- `test_handle_chat_natural_language_reload_plain_follow_up_keeps_top_level_claim_coverage`
  - `WebSearchStore.save(...)` 로 `이용 형태 weak / 개발 weak` claim_coverage 와 `재조사했지만 이용 형태는 아직 단일 출처 상태입니다.` progress_summary 를 갖는 entity-card record 를 seed.
  - Step 1: `user_text="방금 검색한 결과 다시 보여줘"` 로 natural-language reload 를 호출해 web-search `active_context` 를 세팅.
  - Step 2: `user_text="이 결과 한 문장으로 요약해줘"` 에 **`load_web_search_record_id` 를 넣지 않고** plain follow-up 을 호출. 이 경로는 브라우저가 reload 이후 사용자가 record id 를 다시 보내지 않고 연속 질문을 던질 때 정확히 동일한 payload 모양입니다.
  - `result["response"]["claim_coverage"]` 가 `이용 형태` slot 을 포함하는지, `result["response"]["claim_coverage_progress_summary"]` 가 저장값과 완전히 일치하는지, 그리고 `result["session"]["messages"]` 의 마지막 assistant message 에도 같은 top-level 값이 persist 되는지를 lock.
  - 실패 시 현재 payload 를 디버그 메시지로 노출해 회귀가 무엇을 보여주는지 명확히 드러냅니다.

- `test_handle_chat_latest_update_natural_language_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty`
  - 같은 Step 1 / Step 2 구조를 `서울 날씨` latest-update record (`claim_coverage=[]`, `claim_coverage_progress_summary=""`) 로 돌려, plain follow-up 의 `response.claim_coverage` 가 `[]`, `claim_coverage_progress_summary` 는 falsy 로 유지되는지를 lock. 마지막 assistant message 도 `claim_coverage = []`, `claim_coverage_progress_summary` 는 falsy 를 유지하도록 확인.
  - 이는 직전 propagation 슬라이스의 `kind == "web_search"` + 비어 있지 않은 `claim_coverage` gate 가 latest-update / no-claim-coverage 경로를 여전히 건드리지 않는다는 점을 직접 증명합니다.

### `tests/test_smoke.py`

추가적으로 `test_plain_follow_up_without_load_record_id_keeps_top_level_claim_coverage_from_active_context` 를 직전 `test_reload_follow_up_propagates_top_level_claim_coverage_from_active_context` 뒤, `test_entity_reinvestigation_query_reports_claim_progress` 앞에 넣었습니다. 이 smoke 테스트는 WebAppService 계층을 거치지 않고 `AgentLoop` 만으로 같은 plain-follow-up 경로를 증명합니다.

- entity-card 경로: `WebSearchStore.save(...)` 로 seed → `loop.handle(UserRequest("방금 검색한 결과 다시 보여줘", session_id=..., metadata={"web_search_permission": "enabled"}))` 로 reload → 이어서 `loop.handle(UserRequest("이 결과 한 문장으로 요약해줘", session_id=...))` 로 **metadata 에 `load_web_search_record_id` 없이** plain follow-up 을 호출. 두 번째 응답의 `response.claim_coverage` 가 `이용 형태` slot 을 포함하고 `response.claim_coverage_progress_summary` 가 저장값과 완전히 일치하는지 lock.
- latest-update 경로: 같은 세션 패턴으로 `서울 날씨` 기록을 seed → reload → plain follow-up 을 돌리고, `response.claim_coverage == []` 와 `response.claim_coverage_progress_summary is None` 을 lock.

두 경로 모두 같은 한 테스트 안에서 확인해 gate 조건이 entity-card 와 latest-update 를 정확히 구분한다는 대칭성을 한 번에 드러냅니다. 기존 reload-by-id 회귀는 건드리지 않았고, 새 smoke 테스트는 그 회귀와 함께 공존합니다.

### 구현 / 제품 docs

구현 코드와 `docs/PRODUCT_SPEC.md` / `docs/ACCEPTANCE_CRITERIA.md` 는 이 슬라이스에서 건드리지 않았습니다. 직전 `/work` 의 propagation 한 줄 덕분에 plain-follow-up 동작은 이미 shipped 상태이고, 공개 계약 문구 역시 현재 동작과 일치하기 때문에 추가 문서 동기화는 하지 않았습니다.

controller / pipeline / watcher / runtime, `e2e/tests/web-smoke.spec.mjs`, browser selector, `app/static/app.js`, `core/agent_loop.py`, 다른 docs family, `work`/`verify` 이전 항목은 건드리지 않았습니다.

## 검증

- `python3 -m py_compile tests/test_smoke.py tests/test_web_app.py` → 성공.
- 신규 회귀 세 개를 개별 실행해 각각 OK 를 확인:
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_plain_follow_up_keeps_top_level_claim_coverage` → `Ran 1 test … OK`.
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_natural_language_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty` → `Ran 1 test … OK`.
  - `python3 -m unittest -v tests.test_smoke.SmokeTest.test_plain_follow_up_without_load_record_id_keeps_top_level_claim_coverage_from_active_context` → `Ran 1 test … OK`.
- 요구된 4-test 재실행 배치 (`test_reload_follow_up_propagates_top_level_claim_coverage_from_active_context`, `test_handle_chat_reload_follow_up_propagates_top_level_claim_coverage_and_progress_summary`, `test_handle_chat_natural_language_reload_then_follow_up_keeps_top_level_claim_coverage`, `test_handle_chat_latest_update_reload_follow_up_keeps_claim_coverage_surfaces_empty`) 에 이 슬라이스의 세 신규 회귀를 더해 한 배치로 `Ran 7 tests … OK` 를 확인했습니다. 기존 reload-by-id 회귀는 그대로 유지되고, 새 plain-follow-up 회귀가 같은 session 내 record id 없이도 propagation 이 유효함을 직접 드러냅니다.
- `git diff --check -- tests/test_smoke.py tests/test_web_app.py work/4/11` → whitespace 경고 없음.
- 구현 코드, 제품 docs, 브라우저 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright `make e2e-test` 와 전체 `tests.test_smoke` / `tests.test_web_app` 배치 재실행은 이번 라운드에 과하여 돌리지 않았습니다. (직전 `/work` 에서 이미 362-test 배치를 한 번 확인했고, 이번 변경은 테스트 추가뿐입니다. 또한 handoff 가 "`python3 -m unittest tests.test_smoke tests.test_web_app` 전체 실행이 sandbox 에서 socket-bind 오류를 낸 이력이 있다" 고 명시했으므로 이번 라운드에서도 전체 suite 재실행은 일부러 생략했습니다.)

## 남은 리스크

- 새 회귀 두 개가 선택한 follow-up 문구 (`"이 결과 한 문장으로 요약해줘"`) 는 entity reinvestigation 슬롯 키워드 (`개발`, `장르`, `플랫폼`, `출시`, `상태`) 를 포함하지 않고 `"검색"` 같은 새 web-search 트리거도 포함하지 않아 `_respond_with_active_context()` 경로로 통과합니다. 미래에 entity reinvestigation 트리거 키워드 목록이 확장되어 `"요약"` 같은 단어를 포함하게 되면 이 테스트는 서로 다른 경로로 빠질 수 있습니다. 그 경우 트리거 어휘와 테스트 문구를 같이 점검해야 합니다.
- smoke 테스트 쪽의 latest-update 검증은 `latest_follow_up.claim_coverage == []` 와 `latest_follow_up.claim_coverage_progress_summary is None` 두 어서션에 의존합니다. 미래에 AgentResponse 기본값이 바뀌어 빈 list 대신 `None` 을 돌려주거나 반대로 바뀌면 assertion 표현을 조정해야 합니다. 현재 dataclass 기본값은 `claim_coverage: list[...] = field(default_factory=list)` 이고 `claim_coverage_progress_summary: str | None = None` 입니다.
- 이 슬라이스는 tests-only 라 구현 회귀를 직접 막지는 않습니다. 구현에 미래 regression 이 생기면 propagation gate / branch 로직을 다시 점검해야 합니다. 새 회귀들이 propagation 이 사라질 때 가장 먼저 빨갛게 터지도록 배치되어 있습니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `controller/server.py`, `pipeline_gui/backend.py`, `watcher_core.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`, `docs/PRODUCT_SPEC.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`, `core/agent_loop.py`, `storage/web_search_store.py`, `verify/4/10/...`, 기존 `work/4/11/`와 `verify/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았습니다.
