## 변경 파일
- `verify/4/11/2026-04-11-history-record-click-reload-plain-follow-up-claim-coverage-parity-regressions-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/11/2026-04-11-history-record-click-reload-plain-follow-up-claim-coverage-parity-regressions.md`가 click reload 뒤 plain follow-up exact path용 tests-only 회귀 2건을 추가했다고 기록했으므로, 실제 코드/테스트와 재실행 결과가 그 주장과 맞는지 다시 확인해야 했습니다.
- 검증을 마친 뒤에는 같은 history-record reload family 안에서 다음 한 슬라이스만 정확히 고정해야 했습니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 트리와 일치합니다. `tests/test_web_app.py:10025`와 `tests/test_web_app.py:10146`에 새 회귀 2건이 실제로 존재하고, 둘 다 Step 2 follow-up payload에서 `load_web_search_record_id`를 다시 보내지 않는 exact plain-follow-up 경로를 잠급니다.
- click reload 진입 설명도 코드와 맞습니다. `app/handlers/chat.py:543-544`는 `load_web_search_record_id`만 있으면 `"최근 웹 검색 기록을 다시 불러와 주세요."`를 auto-inject하고, `core/agent_loop.py:6401-6448`의 show-only reload 분기는 `"불러와"` 같은 문구를 감지해 `actions_taken=["load_web_search_record"]`를 반환합니다. 이어서 follow-up은 `core/agent_loop.py:6722-6883`의 active-context 응답 경로에서 entity-card일 때만 top-level `claim_coverage` / `claim_coverage_progress_summary`를 다시 노출하고, latest-update처럼 저장된 `claim_coverage`가 비어 있으면 해당 surface를 비워 둡니다.
- `/work`가 설명한 plain follow-up reasoning도 현재 구현과 모순되지 않습니다. `_should_treat_as_entity_reinvestigation()`은 이전 query와 관련된 slot probe가 있을 때만 true가 되므로(`core/agent_loop.py:4280-4291`), `"이 결과 한 문장으로 요약해줘"` 같은 일반 follow-up은 reinvestigation 경로보다 active-context answer 경로에 남는 쪽으로 해석하는 것이 코드상 타당합니다. 이 부분은 코드 판독 기반 판단이며, 아래 rerun 결과와도 일치했습니다.
- 현재 남은 same-family proof gap은 브라우저 계약 쪽입니다. 기존 Playwright click-reload follow-up 시나리오들은 여전히 follow-up 요청에 `load_web_search_record_id`를 다시 싣습니다. 예를 들어 entity-card는 `e2e/tests/web-smoke.spec.mjs:1751-1758`, latest-update는 `e2e/tests/web-smoke.spec.mjs:2217-2224`, noisy entity-card는 `e2e/tests/web-smoke.spec.mjs:10040-10041`이 그렇습니다. 반면 실제 UI는 reload 버튼에서만 `load_web_search_record_id`를 보내고(`app/static/app.js:3064-3069`), 일반 후속 제출은 `buildSharedRequestSettings()` 기반 payload라 그 필드를 포함하지 않습니다(`app/static/app.js:412-419`). 따라서 다음 control은 browser click-reload 뒤 actual plain follow-up contract를 잠그는 방향으로 정했습니다.

## 검증
- `python3 -m py_compile tests/test_smoke.py tests/test_web_app.py` → 성공
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_click_reload_plain_follow_up_keeps_top_level_claim_coverage` → `Ran 1 test ... OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_click_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty` → `Ran 1 test ... OK`
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_reload_follow_up_propagates_top_level_claim_coverage_from_active_context tests.test_web_app.WebAppServiceTest.test_handle_chat_reload_follow_up_propagates_top_level_claim_coverage_and_progress_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_then_follow_up_keeps_top_level_claim_coverage tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_reload_follow_up_keeps_claim_coverage_surfaces_empty tests.test_smoke.SmokeTest.test_plain_follow_up_without_load_record_id_keeps_top_level_claim_coverage_from_active_context tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_plain_follow_up_keeps_top_level_claim_coverage tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_natural_language_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty tests.test_web_app.WebAppServiceTest.test_handle_chat_click_reload_plain_follow_up_keeps_top_level_claim_coverage tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_click_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty` → `Ran 9 tests ... OK`
- `git diff --check -- tests/test_smoke.py tests/test_web_app.py work/4/11` → 성공
- 이번 라운드는 tests-only `/work` 검증이므로 Playwright나 전체 `tests.test_smoke` / `tests.test_web_app` full rerun은 재실행하지 않았습니다.

## 남은 리스크
- backend/service level proof는 닫혔지만, 브라우저의 실제 `다시 불러오기` 클릭 뒤 일반 입력창으로 보내는 plain follow-up payload shape는 아직 Playwright가 고정하지 않습니다. 현재 e2e는 page-scope `sendRequest(...)`로 `load_web_search_record_id`를 다시 넣는 follow-up에 치우쳐 있습니다.
- 저장소는 계속 dirty 상태이며 pipeline/runtime/controller 관련 변경이 동시에 열려 있습니다. 다음 슬라이스도 `app.web` history reload browser contract 안에만 묶는 편이 안전합니다.
