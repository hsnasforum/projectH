# history-card latest-update natural-reload follow-up-chain remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-natural-reload-follow-up-chain-remaining-response-origin-verification.md` — 최신 `/work` 재검증 결과와 CONTROL_SEQ 95 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 95 implement handoff 를 `history-card latest-update load-by-id follow-up-chain remaining response-origin exact service bundle` 로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-latest-update-natural-reload-follow-up-chain-remaining-response-origin-exact-service-bundle.md`) 가 natural reload latest-update follow-up chain 6개 테스트의 exact `response_origin` tighten을 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 latest-update response-origin family 안에서 다음 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline` 에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work` 는 현재 tree 기준으로 truthful합니다. `tests/test_web_app.py` 의 natural reload latest-update follow-up chain 6개 테스트 모두에 exact `response_origin` assertion 이 실제로 추가되어 있습니다.
  - mixed-source natural reload first follow-up block: `tests/test_web_app.py:19127-19135`
  - mixed-source natural reload second follow-up block: `tests/test_web_app.py:19200-19208`
  - single-source natural reload first follow-up block: `tests/test_web_app.py:19262-19270`
  - single-source natural reload second follow-up block: `tests/test_web_app.py:19325-19333`
  - news-only natural reload first follow-up block: `tests/test_web_app.py:19392-19400`
  - news-only natural reload second follow-up block: `tests/test_web_app.py:19462-19470`
- 위 6개 테스트는 모두 `provider = "web"`, `badge = "WEB"`, `label = "외부 웹 최신 확인"`, `kind = "assistant"`, `model is None`, `answer_mode = "latest_update"` 를 직접 잠그고, variant 별 `verification_label` / `source_roles` 와 기존 `source_paths`, zero-count `claim_coverage_summary`, 빈 `claim_coverage_progress_summary` 확인도 유지합니다. `/work` 의 핵심 설명과 현재 테스트 코드는 일치합니다.
- 현재 같은 family 에서 가장 가까운 다음 current-risk 는 click reload 기반 `load_web_search_record_id` follow-up chain 의 exact-field 공백입니다. 다음 슬라이스는 `history-card latest-update load-by-id follow-up-chain remaining response-origin exact service bundle` 로 정했습니다.
  - mixed-source first follow-up 는 아직 `answer_mode`, `verification_label`, `source_roles` 만 확인합니다: `tests/test_web_app.py:17909-17912`
  - mixed-source second follow-up 는 아직 `badge`, `answer_mode`, `verification_label`, `source_roles` 만 확인합니다: `tests/test_web_app.py:17956-17960`
  - single-source first follow-up 는 아직 `source_paths` 만 확인하고 `response_origin` exactness 가 없습니다: `tests/test_web_app.py:18037-18039`
  - news-only first follow-up 도 아직 `source_paths` 만 확인합니다: `tests/test_web_app.py:18106-18109`
  - single-source second follow-up 는 아직 `badge`, `answer_mode`, `verification_label`, `source_roles` 만 확인합니다: `tests/test_web_app.py:18981-18985`
  - news-only second follow-up 는 아직 `badge`, `answer_mode`, `verification_label`, `source_roles` 만 확인합니다: `tests/test_web_app.py:19060-19064`
- 이 번들 선택이 noisy-community latest-update tightening 보다 낫습니다. natural reload follow-up chain 은 방금 truthful하게 닫혔고, 다음으로 가장 가까운 same-family current-risk 는 non-noisy click reload follow-up chain 의 exact-field 공백입니다. first/second follow-up 을 또 쪼개기보다 mixed/single/news 6개를 한 번에 닫는 편이 더 reviewable 합니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_natural_reload_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_natural_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_natural_reload_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_natural_reload_second_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_natural_reload_follow_up_preserves_response_origin_and_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` → `Ran 6 tests in 0.180s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract 와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten 이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py` 의 natural reload follow-up chain 6개 service test assertion bundle 뿐이라 wider rerun 은 과합니다.

## 남은 리스크
- click reload 기반 latest-update follow-up chain 은 아직 `provider` / `label` / `kind` / `model` exact-field continuity 를 완전히 잠그지 않았습니다.
- noisy-community latest-update family 의 reload / follow-up / second-follow-up exact contract 는 아직 이 verification 범위 밖입니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/verify`, `work/4/11/` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
