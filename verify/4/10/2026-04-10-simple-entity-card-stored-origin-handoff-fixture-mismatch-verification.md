# simple entity-card stored-record kind-model exact 검증 업데이트

## 변경 파일
- `verify/4/10/2026-04-10-simple-entity-card-stored-origin-handoff-fixture-mismatch-verification.md` — latest `/work` stored-record kind/model exact 검수 결과와 CONTROL_SEQ 88 기준 다음 슬라이스 판단으로 갱신했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 88 implement handoff를 simple stored-record remaining response-origin exact service bundle로 갱신합니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-simple-entity-card-stored-record-kind-model-exact-service-bundle.md`) 는 simple entity-card click-reload family의 세 서비스 테스트에 persisted stored record `response_origin["kind"] == "assistant"` 와 `response_origin["model"] is None` exact assertion을 추가했다고 주장합니다.
- 이번 Codex 검증 라운드는 그 코드/검증 주장이 실제로 맞는지와, same-family 다음 슬라이스를 또 한두 필드짜리 micro-slice로 쪼개지 않고 어디까지 한 번에 닫는 것이 맞는지 함께 다시 정해야 했습니다.

## 핵심 변경
- 최신 `/work`는 이번에는 truthful합니다. `tests/test_web_app.py`의 세 simple entity-card 서비스 테스트 모두에서 첫 검색 직후 `service.web_search_store.get_session_record(<session_id>, record_id)` 를 읽고, stored record의 `response_origin.kind == "assistant"` 와 `response_origin.model is None` 을 직접 잠그는 블록이 실제로 추가되었습니다.
  - `test_handle_chat_load_web_search_record_id_entity_card_exact_fields` → `tests/test_web_app.py:8614-8620`
  - `test_handle_chat_entity_card_reload_preserves_stored_response_origin` → `tests/test_web_app.py:16600-16606`
  - `test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → `tests/test_web_app.py:16669-16675`
- 기존 reload 응답 쪽 `kind` / `model` assertion도 그대로 유지되고 있습니다.
  - `tests/test_web_app.py:8641-8642`
  - `tests/test_web_app.py:16625-16626`
  - `tests/test_web_app.py:16695-16696`
- 최신 `/work`의 rationale도 현재 tree와 맞습니다. 직전 `/work`의 `superpowers:using-superpowers` skill 표기와 browser seeded fixture overclaim은 실제로 mismatch였고, 이번 `/work`는 그 mismatch를 근거로 stored-record path를 우선 잠그는 이유를 정직하게 설명합니다.
- same simple fixture direct runtime probe 결과, stored record `response_origin` 은 이미 다음 full shape를 안정적으로 직렬화합니다.
  - `{'provider': 'web', 'badge': 'WEB', 'label': '외부 웹 설명 카드', 'model': None, 'kind': 'assistant', 'answer_mode': 'entity_card', 'source_roles': ['백과 기반'], 'verification_label': '설명형 단일 출처'}`
- 따라서 다음 exact slice는 stored-record remaining response-origin exact service bundle이 맞습니다. 현재 stored record에서 직접 잠긴 것은 `kind` 와 `model` 뿐이고, 같은 세 테스트에는 stored `provider`, `badge`, `label`, `answer_mode`, `verification_label`, `source_roles` exact assertion이 아직 없습니다. 이 여섯 필드를 한 번에 묶으면 simple stored-record family를 의미 있게 닫을 수 있고, 다시 provider/label/badge 등을 따로 떼는 micro-loop를 피할 수 있습니다.

## 검증
- 이번 라운드 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests in 0.070s ... OK`
- 이번 라운드 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드 실행: same simple fixture direct runtime probe (`WebAppService` + single namu.wiki `_FakeWebSearchTool`) → stored record `response_origin` 이 `provider: 'web'`, `badge: 'WEB'`, `label: '외부 웹 설명 카드'`, `model: None`, `kind: 'assistant'`, `answer_mode: 'entity_card'`, `source_roles: ['백과 기반']`, `verification_label: '설명형 단일 출처'` 를 직렬화함
- 이번 라운드 실행: `git status --short` → `M tests/test_web_app.py`, `M verify/4/10/2026-04-10-simple-entity-card-stored-origin-handoff-fixture-mismatch-verification.md`, `?? work/4/11/`
- 이번 라운드에서 코드/문서 대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 재확인. 이번 라운드는 서비스 테스트 assertion bundle이라 product docs 갱신 대상 아님
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체 — latest `/work` change is still the same three narrow service tests only
- 이번 라운드에서 재실행하지 않음: Playwright / `make e2e-test` — browser-visible contract나 shared browser helper 변경이 없었습니다

## 남은 리스크
- simple stored-record path는 이제 `kind` / `model` 을 직접 잠갔지만, stored `provider`, `badge`, `label`, `answer_mode`, `verification_label`, `source_roles` 는 아직 exact assertion이 없습니다. 이 상태로는 저장 레코드 shape가 drift해도 reload 응답 측 assertion만으로는 storage-stage drift를 초기에 pinpoint하지 못할 수 있습니다.
- `e2e/tests/web-smoke.spec.mjs` 의 simple seeded browser records는 여전히 실제 stored record shape와 일부 다릅니다. 다만 이는 현재 stored-record family를 다 닫은 뒤 검토할 test-data sync 축이며, 이번 라운드의 우선 current-risk는 아니었습니다.
- 작업트리는 계속 dirty입니다. 다음 라운드는 `tests/test_web_app.py` 한 파일만 추가 편집하고, 이미 pending 인 `/verify` 및 `work/4/11/` 파일을 되돌리지 않아야 합니다.
