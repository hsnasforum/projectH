# simple entity-card stored-record remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-simple-entity-card-stored-record-remaining-response-origin-verification.md` — latest `/work` 재검증 결과와 CONTROL_SEQ 89 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 89 implement handoff를 `history-card latest-update reload-follow-up remaining response-origin exact service bundle`로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-simple-entity-card-stored-record-remaining-response-origin-exact-service-bundle.md`) 가 simple entity-card stored record 경로에 남아 있던 `response_origin` 리터럴 exact assertion을 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 history-card response-origin exactness 축에서 다음 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline`에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`는 현재 tree 기준으로 truthful합니다. `tests/test_web_app.py`의 세 simple entity-card 서비스 테스트에서 stored record `response_origin` exact assertion이 실제로 존재합니다.
  - `test_handle_chat_load_web_search_record_id_entity_card_exact_fields`의 stored block: `tests/test_web_app.py:8614-8628`
  - `test_handle_chat_entity_card_reload_preserves_stored_response_origin`의 stored block: `tests/test_web_app.py:16608-16622`
  - `test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin`의 stored block: `tests/test_web_app.py:16685-16699`
- 같은 세 테스트의 reload 응답 exact assertion도 그대로 유지되고 있습니다.
  - `tests/test_web_app.py:8641-8650`
  - `tests/test_web_app.py:16633-16642`
  - `tests/test_web_app.py:16711-16720`
- 따라서 simple entity-card stored-record response-origin family는 이번 dirty tree 안에서 의미 있게 닫혔다고 보는 편이 맞습니다. latest `/work`가 말한 `provider`, `badge`, `label`, `answer_mode`, `verification_label`, `source_roles` 추가도 현재 코드와 일치합니다.
- 다음 exact slice는 `history-card latest-update reload-follow-up remaining response-origin exact service bundle`로 정했습니다.
  - latest-update follow-up trio는 아직 permissive합니다.
  - `tests/test_web_app.py:16723-16815`
  - `tests/test_web_app.py:16818-16900`
  - `tests/test_web_app.py:16902-16992`
  - 위 세 테스트는 `verification_label`과 `source_roles`만 exact하게 잠그고, `answer_mode`는 `assertIn(..., ("latest_update", first_origin["answer_mode"]))`로 느슨하게 확인하며 `provider`, `badge`, `label`, `kind`, `model` exact assertion이 없습니다.
- 이 슬라이스가 closest alternative보다 낫습니다.
  - latest-update natural reload exact-field trio (`tests/test_web_app.py:8155-8246`, `tests/test_web_app.py:8249-8329`, `tests/test_web_app.py:8332-8422`)는 이미 `answer_mode` exact equality를 갖고 있어 looseness가 follow-up trio보다 작습니다.
  - core runtime contract도 latest-update web response origin을 `provider = "web"`, `badge = "WEB"`, `label = "외부 웹 최신 확인"`, `model = None`, `kind = "assistant"`로 고정합니다 (`core/agent_loop.py:5275-5279`, `core/agent_loop.py:5304-5312`). 따라서 현재 더 직접적인 current-risk는 follow-up path의 remaining literal drift입니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests in 0.068s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py`의 세 서비스 테스트 assertion bundle뿐이어서 wider rerun은 과합니다.

## 남은 리스크
- latest-update history-card follow-up trio는 아직 remaining response-origin literal drift를 허용합니다. `badge`, `provider`, `label`, `kind`, `model`, exact `answer_mode`가 다음 슬라이스 전까지 service layer에서 잠겨 있지 않습니다.
- latest-update natural reload exact-field trio도 여전히 `verification_label` / `source_roles` 중심이라 follow-up trio 이후 별도 service tighten 후보가 남을 수 있습니다.
- 다른 response-origin family (dual-probe / zero-strong / actual-search / noisy latest-update)는 이번 라운드에서 다시 검수하지 않았습니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/work`·`/verify` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
