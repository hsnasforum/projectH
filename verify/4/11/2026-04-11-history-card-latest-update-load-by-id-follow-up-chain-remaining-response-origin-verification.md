# history-card latest-update load-by-id follow-up-chain remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-load-by-id-follow-up-chain-remaining-response-origin-verification.md` — 최신 `/work` 재검증 결과와 CONTROL_SEQ 96 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 96 implement handoff 를 다음 same-family stored-record 슬라이스로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-latest-update-load-by-id-follow-up-chain-remaining-response-origin-exact-service-bundle.md`) 가 click-reload latest-update follow-up chain 6개 테스트의 exact `response_origin` surface tighten을 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 latest-update history-card family 안에서 다음 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline` 에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work` 는 현재 tree 기준으로 truthful합니다. click-reload latest-update follow-up chain 6개 테스트 모두에 exact `response_origin` surface assertion 이 실제로 추가되어 있습니다.
  - mixed-source first follow-up block: `tests/test_web_app.py:17909-17917`
  - mixed-source second follow-up block: `tests/test_web_app.py:17961-17969`
  - single-source first follow-up block: `tests/test_web_app.py:18049-18057`
  - single-source second follow-up block: `tests/test_web_app.py:19008-19016`
  - news-only first follow-up block: `tests/test_web_app.py:18128-18136`
  - news-only second follow-up block: `tests/test_web_app.py:19091-19099`
- 위 6개 테스트는 모두 `provider = "web"`, `badge = "WEB"`, `label = "외부 웹 최신 확인"`, `kind = "assistant"`, `model is None`, `answer_mode = "latest_update"` 를 직접 잠그고, variant 별 `verification_label` / `source_roles` 와 기존 `source_paths` 검증을 유지합니다. second-follow-up trio는 기존 zero-count `claim_coverage_summary` / 빈 `claim_coverage_progress_summary` 확인도 그대로 유지합니다.
- `/work` 의 “stored-record 계약은 이미 앞선 라운드에서 잠겼다”는 설명은 first follow-up stored coverage 기준으로는 맞습니다.
  - mixed-source stored first follow-up block: `tests/test_web_app.py:16995-17007`
  - single-source stored first follow-up block: `tests/test_web_app.py:17100-17110`
  - news-only stored first follow-up block: `tests/test_web_app.py:17210-17220`
- 다만 same-family current-risk 기준으로는 click-reload second-follow-up stored exactness 가 아직 남아 있습니다. 현재 second-follow-up trio는 `history_entry` 의 zero-count summary 만 확인하고, 그 안의 stored `response_origin` exact field 는 아직 직접 잠그지 않습니다.
  - mixed-source second follow-up history block: `tests/test_web_app.py:17975-17986`
  - single-source second follow-up history block: `tests/test_web_app.py:19021-19032`
  - news-only second follow-up history block: `tests/test_web_app.py:19105-19116`
- 다음 슬라이스는 `history-card latest-update load-by-id second-follow-up stored-record remaining response-origin exact service bundle` 로 정했습니다.
  - current surface follow-up chain 은 이번 `/work` 로 닫혔습니다.
  - first follow-up stored exactness 는 이미 기존 세 테스트가 덮고 있습니다.
  - 남은 가장 가까운 same-family persistence risk 는 second-follow-up history entry 의 stored `response_origin` exactness 공백입니다.
  - 이 번들이 noisy-community tightening 보다 낫습니다. non-noisy click-reload chain 이 더 단순한 shipped history-card path이고, current tree 에서 바로 남아 있는 gap 이 persistence 쪽이기 때문입니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_follow_up_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_reload_second_follow_up_preserves_response_origin_and_source_paths` → `Ran 6 tests in 0.166s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract 와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten 이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py` 의 click-reload follow-up chain 6개 service test assertion bundle 뿐이라 wider rerun 은 과합니다.

## 남은 리스크
- click-reload latest-update second-follow-up trio는 session `web_search_history` entry 안의 stored `response_origin` exactness 를 아직 직접 잠그지 않았습니다.
- noisy-community latest-update family 의 natural-reload / click-reload follow-up chain exact contract 는 아직 이 verification 범위 밖입니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/verify`, `work/4/11/` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
