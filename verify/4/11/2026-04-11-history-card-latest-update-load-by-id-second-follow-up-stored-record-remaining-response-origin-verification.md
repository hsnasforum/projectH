# history-card latest-update load-by-id second-follow-up stored-record remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-load-by-id-second-follow-up-stored-record-remaining-response-origin-verification.md` — 최신 `/work` 재검증 결과와 CONTROL_SEQ 97 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 97 implement handoff 를 noisy-community click-reload response-origin exact bundle 로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-latest-update-load-by-id-second-follow-up-stored-record-remaining-response-origin-exact-service-bundle.md`) 가 click-reload latest-update second-follow-up trio의 stored `response_origin` exactness를 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 latest-update history-card family 안에서 다음 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline` 에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work` 는 현재 tree 기준으로 truthful합니다. click-reload latest-update second-follow-up 세 테스트 모두에 `service.web_search_store.get_session_record(...)` 기반 stored `response_origin` exact assertion 이 실제로 추가되어 있습니다.
  - mixed-source stored block: `tests/test_web_app.py:17961-17977`
  - single-source stored block: `tests/test_web_app.py:19025-19039`
  - news-only stored block: `tests/test_web_app.py:19123-19137`
- 위 세 테스트는 stored `response_origin` 에 대해 모두 `provider = "web"`, `badge = "WEB"`, `label = "외부 웹 최신 확인"`, `kind = "assistant"`, `model is None`, `answer_mode = "latest_update"` 를 직접 잠그고, variant 별 `verification_label` / `source_roles` 도 고정합니다. 기존 surface `origin`, `source_paths`, zero-count `claim_coverage_summary`, 빈 `claim_coverage_progress_summary` 확인은 그대로 유지됩니다.
- `/work` 의 “`session["web_search_history"]` entry 에는 전체 `response_origin` 객체가 없어서 store read 가 불가피했다”는 설명도 현재 구현과 맞습니다.
  - `storage/web_search_store.py:274-292` 의 `get_session_record()` 는 전체 stored record 를 그대로 돌려줍니다.
  - 반면 `storage/web_search_store.py:295-312` 의 `list_session_record_summaries()` 는 session history summary 에 `answer_mode`, `verification_label`, `source_roles` 만 노출하고, 전체 `response_origin` object 는 실어 주지 않습니다.
  - 따라서 second-follow-up 테스트에서 persisted `response_origin` exactness 를 잠그려면 `/work` 설명대로 direct store read 가 필요한 상태입니다.
- 다음 슬라이스는 `history-card latest-update noisy-community click-reload remaining response-origin exact service bundle` 로 정했습니다.
  - non-noisy click-reload latest-update path 는 이제 show-only, first follow-up stored, first/second follow-up surface, second-follow-up stored 까지 닫혔습니다.
  - 현재 가장 가까운 same-family current-risk 는 noisy-community click-reload path 의 surface exactness 공백입니다.
  - noisy show-only reload 는 아직 `answer_mode` 와 negative exclusion 만 확인합니다: `tests/test_web_app.py:11816-11824`
  - noisy click-reload first follow-up 는 아직 `badge`, `answer_mode`, `verification_label`, `source_roles` 만 확인합니다: `tests/test_web_app.py:19770-19779`
  - noisy click-reload second follow-up 도 아직 `badge`, `answer_mode`, `verification_label`, `source_roles` 만 확인합니다: `tests/test_web_app.py:19847-19857`
  - 이 세 경로는 같은 noisy-community click-reload flow 안의 reload + first follow-up + second follow-up 이라, 한 번에 닫는 3-test bundle 이 micro-split 보다 더 reviewable 합니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_reload_second_follow_up_preserves_response_origin_and_source_paths` → `Ran 3 tests in 0.114s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract 와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten 이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py` 의 click-reload latest-update second-follow-up stored-record service test 3건뿐이라 wider rerun 은 과합니다.

## 남은 리스크
- noisy-community latest-update click-reload reload / first follow-up / second follow-up 경로는 아직 `provider` / `label` / `kind` / `model` exact-field continuity 를 직접 잠그지 않았습니다.
- noisy-community latest-update natural-reload family 와 stored-record exactness 는 아직 이 verification 범위 밖입니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/verify`, `work/4/11/` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
