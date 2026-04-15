# history-card latest-update noisy-community click-reload remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-noisy-community-click-reload-remaining-response-origin-verification.md` — 최신 `/work` 재검증 결과와 CONTROL_SEQ 98 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 98 implement handoff 를 noisy-community click-reload stored-record exact bundle 로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-latest-update-noisy-community-click-reload-remaining-response-origin-exact-service-bundle.md`) 가 noisy-community latest-update click-reload 3개 테스트의 exact `response_origin` surface tighten을 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 latest-update noisy-community family 안에서 다음 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline` 에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work` 는 현재 tree 기준으로 truthful합니다. noisy-community latest-update click-reload 3개 테스트 모두에 exact `response_origin` surface assertion 이 실제로 추가되어 있습니다.
  - show-only reload block: `tests/test_web_app.py:11816-11827`
  - click-reload first follow-up block: `tests/test_web_app.py:19777-19785`
  - click-reload second follow-up block: `tests/test_web_app.py:19858-19866`
- 위 3개 테스트는 모두 `provider = "web"`, `badge = "WEB"`, `label = "외부 웹 최신 확인"`, `kind = "assistant"`, `model is None`, `answer_mode = "latest_update"`, `verification_label = "기사 교차 확인"`, `source_roles = ["보조 기사"]` 를 직접 잠그면서, 기존 negative exclusion (`보조 커뮤니티`, `brunch`) 과 positive retained source-path/summary assertions 를 그대로 유지합니다. `/work` 설명과 현재 테스트 코드는 일치합니다.
- 다음 슬라이스는 `history-card latest-update noisy-community click-reload stored-record remaining response-origin exact service bundle` 로 정했습니다.
  - 현재 noisy-community click-reload 3개 테스트에는 아직 direct store read 가 없습니다. `get_session_record(...)` 는 이 세 session id 주변에 전혀 등장하지 않습니다: `tests/test_web_app.py:11796-11812`, `tests/test_web_app.py:19766-19775`, `tests/test_web_app.py:19846-19856`
  - show-only reload 는 현재 session history entry 의 zero-count summary 만 보고, persisted `response_origin` object 는 직접 잠그지 않습니다: `tests/test_web_app.py:11834-11846`
  - click-reload second follow-up 도 현재 `latest_entry` 의 summary fields 만 확인합니다: `tests/test_web_app.py:19875-19889`
  - `storage/web_search_store.py:274-292` 의 `get_session_record()` 는 whole stored record 를 돌려주지만, `storage/web_search_store.py:295-312` 의 session history summary 는 `answer_mode`, `verification_label`, `source_roles` 만 노출하고 전체 `response_origin` object 는 포함하지 않습니다. 따라서 noisy-community persisted `response_origin` exactness 를 잠그려면 non-noisy second-follow-up round 와 같은 direct store read bundle 이 필요한 상태입니다.
  - 이 번들은 noisy-community click-reload show-only reload + first follow-up + second follow-up 의 남은 persistence gap 을 한 번에 닫는 3-test bundle 이라, natural-reload noisy 로 먼저 옮기는 것보다 same-family current-risk reduction 에 더 직접적입니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up` → `Ran 3 tests in 0.095s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract 와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten 이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py` 의 noisy-community click-reload service test 3건뿐이라 wider rerun 은 과합니다.

## 남은 리스크
- noisy-community latest-update click-reload 3개 테스트는 persisted stored `response_origin` exactness 를 아직 직접 잠그지 않았습니다.
- noisy-community latest-update natural-reload family 의 surface/stored exactness 는 아직 이 verification 범위 밖입니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/verify`, `work/4/11/` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
