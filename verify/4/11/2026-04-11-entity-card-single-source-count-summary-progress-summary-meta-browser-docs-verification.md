## 변경 파일
- `verify/4/11/2026-04-11-entity-card-single-source-count-summary-progress-summary-meta-browser-docs-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/11/2026-04-11-history-record-plain-follow-up-claim-coverage-parity-regressions.md`가 tests-only proof-gap closeout을 주장하므로, 실제 새 회귀가 exact path를 잠그는지와 적어 둔 검증 범위가 truthful한지 다시 확인해야 했습니다.
- 이번 라운드는 구현 변경이 아니라 proof coverage 보강 round이므로, 새 테스트 3개와 그 테스트가 묶이는 기존 4-test batch만 좁게 재실행하는 편이 맞았습니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 대부분 맞았습니다. 새 회귀 3개는 실제로 들어가 있었고, plain follow-up exact path도 올바르게 잠그고 있었습니다. [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9822)의 entity-card regression과 [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9938)의 latest-update regression은 Step 2 payload에서 `load_web_search_record_id`를 넣지 않는 plain follow-up 경로를 직접 사용했고, [tests/test_smoke.py](/home/xpdlqj/code/projectH/tests/test_smoke.py#L2365)의 smoke regression도 같은 exact path를 AgentLoop 레벨에서 잠그고 있었습니다.
- `/work`가 고치려던 proof gap도 실제로 닫혔습니다. 이전 round에서 문제였던 [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9627)의 "plain follow-up" 오기술은 그대로 남아 있지만, 이번 round가 그 옆에 exact plain-follow-up 회귀를 추가해 현재 shipped behavior와 proof surface를 일치시켰습니다.
- 다만 최신 `/work`는 fully truthful하지 않았습니다. 검증 섹션이 "직전 `/work` 에서 이미 362-test 배치를 한 번 확인했다"는 문장을 다시 근거로 사용했는데, 직전 `/verify`가 이미 그 362-test full suite pass claim을 현재 sandbox에서는 재현하지 못했다고 명시해 두었습니다. 이번 round 자체는 전체 `tests.test_smoke` / `tests.test_web_app`를 다시 돌리지 않았고, 저도 이번 verification에서 그 claim을 확인하지 않았습니다. 따라서 최신 `/work`의 테스트 추가 자체와 3-test/7-test rerun 서술은 맞지만, full-suite 생략 근거 문구 하나는 여전히 과장입니다.
- 다음 control은 `history-record click-reload plain-follow-up claim_coverage parity regressions`로 고정했습니다. 이유는 current shipped behavior는 natural-language reload 뒤 plain follow-up까지 proof로 닫혔지만, 버튼형 click reload 뒤 plain follow-up은 아직 exact named regression이 없습니다. 기존 click-reload 계열 검증은 [tests/test_web_app.py](/home/xpdlqj/code/projectH/tests/test_web_app.py#L8940)처럼 follow-up 요청에도 다시 `load_web_search_record_id`를 넣는 경로가 중심입니다. 반면 ad-hoc local replay에서는 click reload 뒤 plain follow-up(`load_web_search_record_id` 없음)도 entity-card는 top-level `claim_coverage` 2건과 동일 progress-summary를 유지하고 latest-update는 빈 surface를 유지함을 확인했습니다. 즉 남은 것은 제품 버그가 아니라 same-family proof gap 한 점입니다.

## 검증
- `python3 -m py_compile tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_plain_follow_up_keeps_top_level_claim_coverage tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_natural_language_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty tests.test_smoke.SmokeTest.test_plain_follow_up_without_load_record_id_keeps_top_level_claim_coverage_from_active_context`
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_reload_follow_up_propagates_top_level_claim_coverage_from_active_context tests.test_web_app.WebAppServiceTest.test_handle_chat_reload_follow_up_propagates_top_level_claim_coverage_and_progress_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_then_follow_up_keeps_top_level_claim_coverage tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_reload_follow_up_keeps_claim_coverage_surfaces_empty tests.test_web_app.WebAppServiceTest.test_handle_chat_natural_language_reload_plain_follow_up_keeps_top_level_claim_coverage tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_natural_language_reload_plain_follow_up_keeps_claim_coverage_surfaces_empty tests.test_smoke.SmokeTest.test_plain_follow_up_without_load_record_id_keeps_top_level_claim_coverage_from_active_context`
- `python3 - <<'PY' ...` ad-hoc local replay 1회: click reload (`load_web_search_record_id` only) 뒤 plain follow-up (`load_web_search_record_id` 없음)에서 entity-card는 `claim_coverage` 2건과 동일 progress-summary 유지, latest-update는 empty surface 유지 확인
- `git diff --check -- tests/test_smoke.py tests/test_web_app.py work/4/11`
- 결과:
  - `py_compile` 성공
  - 신규 회귀 3건 배치 `Ran 3 tests … OK`
  - 기존 4-test batch + 신규 3건 합본 `Ran 7 tests … OK`
  - click-reload plain follow-up ad-hoc replay는 entity-card/ latest-update 양쪽 모두 현재 구현이 의도대로 동작함을 확인
  - `git diff --check` 성공
  - 최신 `/work`가 tests-only round였으므로 Playwright와 전체 `tests.test_smoke` / `tests.test_web_app` full rerun은 이번 verification 범위에서 재실행하지 않았습니다

## 남은 리스크
- 현재 biggest remaining same-family risk는 click reload 뒤 plain follow-up exact path의 named regression 부재입니다. natural-language reload 계열은 이번 round로 proof gap이 닫혔지만, 버튼형 reload 뒤 이어지는 일반 채팅은 여전히 ad-hoc 확인에 기대고 있습니다.
- 최신 `/work`의 full-suite 생략 근거 문구는 직전 `/verify`와 충돌합니다. 앞으로 same-family tests-only closeout에서는 이전 round의 미확인 full-suite claim을 생략 근거로 다시 재사용하지 않는 편이 truthful합니다.
- 저장소는 계속 dirty 상태이며 `controller/*`, `pipeline_gui/*`, `watcher_core.py`, pipeline/runtime docs family는 이번 검증 범위 밖입니다. 다음 라운드도 `app.web` history-record reload/follow-up contract 안에 묶는 편이 안전합니다.
