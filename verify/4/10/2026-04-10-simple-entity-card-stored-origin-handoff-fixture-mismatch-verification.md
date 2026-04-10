# simple entity-card click-reload provider exact 검증 업데이트

## 변경 파일
- `verify/4/10/2026-04-10-simple-entity-card-stored-origin-handoff-fixture-mismatch-verification.md` — CONTROL_SEQ 85 기준 최신 `/work` 검증 결과와 다음 exact slice 판단으로 재정리했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 85 implement handoff를 simple click-reload label exact service bundle로 갱신합니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/10/2026-04-10-history-card-simple-entity-card-click-reload-provider-exact-service-bundle.md`) 는 simple click-reload service family의 세 테스트 (`tests/test_web_app.py:8570`, `:16546`, `:16604`) 에 `reload_origin["provider"] == "web"` literal lock을 추가했다고 주장합니다.
- 이번 Codex 검증 라운드는 그 세 테스트가 실제로 수정되었는지, `/work`가 적은 최소 검증이 실제로 통과하는지, 그리고 provider lock 이후 같은 family에서 남은 가장 작은 current-risk reduction이 무엇인지 다시 정해야 했습니다.

## 핵심 변경
- 최신 `/work` 주장은 truthful합니다. 현재 `tests/test_web_app.py:8570`, `tests/test_web_app.py:16546`, `tests/test_web_app.py:16604` 모두 기존 `badge` / `answer_mode` / `verification_label` / `source_roles` literal 블록 뒤에 `self.assertEqual(reload_origin["provider"], "web")` 가 실제로 존재합니다.
- 최신 `/work` 가 건드린 범위도 truthful합니다. fixture, browser anchor, docs, pipeline files, dual-probe / zero-strong / actual-search / latest-update families는 이번 슬라이스에서 바뀌지 않았습니다.
- direct runtime probe를 같은 simple fixture로 재현한 결과, simple `show-only reload` 와 `follow-up` 모두 `response_origin` 에 `provider: "web"` 뿐 아니라 `label: "외부 웹 설명 카드"`, `kind: "assistant"`, `model: None` 도 함께 안정적으로 방출합니다.
- 같은 family의 다음 smallest current-risk reduction 은 `response_origin["label"] == "외부 웹 설명 카드"` exact lock입니다. 현재 검색 기준으로 simple click-reload family service tests에는 `label` literal assertion이 없고, browser side에는 seeded record literal만 존재합니다 (`e2e/tests/web-smoke.spec.mjs:1407`).

## 검증
- 이번 라운드 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests ... OK`
- 이번 라운드 실행: `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음
- 이번 라운드 실행: same fixture direct runtime probe (`WebAppService` + single namu.wiki `_FakeWebSearchTool`) → `reload` / `followup` 모두 `response_origin` 에 `provider: 'web'`, `badge: 'WEB'`, `label: '외부 웹 설명 카드'`, `kind: 'assistant'`, `model: None`, `answer_mode: 'entity_card'`, `verification_label: '설명형 단일 출처'`, `source_roles: ['백과 기반']` 확인
- 이번 라운드에서 코드/계약 대조: `tests/test_web_app.py:8570`, `:16546`, `:16604` 의 simple click-reload provider exact lock 확인
- 이번 라운드에서 코드/계약 대조: `e2e/tests/web-smoke.spec.mjs:1407` 의 simple browser seeded `label: "외부 웹 설명 카드"` 존재 확인
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체 — latest `/work` change is three narrow service assertions only
- 이번 라운드에서 재실행하지 않음: Playwright / `make e2e-test` — browser-visible contract나 shared browser helper 변경이 없었습니다

## 남은 리스크
- simple click-reload service family에서 `provider` 는 이제 잠겼지만 `response_origin["label"]` 은 아직 `tests/test_web_app.py:8570`, `:16546`, `:16604` 어디에서도 literal lock이 없습니다. 이 상태로는 same-family service contract가 `provider` 는 유지하되 label wording만 drift하는 경우를 조기에 잡지 못합니다.
- `kind` 와 `model` 도 여전히 unlocked 이지만, 이번 검증 기준 가장 작은 next slice 는 이미 runtime probe와 browser seeded literal로 안정성이 확인된 `label == "외부 웹 설명 카드"` field입니다. `kind` / `model` 까지 같이 묶으면 scope가 넓어집니다.
- 저장소 작업트리가 매우 더럽습니다. 다음 라운드는 `tests/test_web_app.py` 한 파일만 건드리고 unrelated pending edits를 되돌리지 않아야 합니다.
