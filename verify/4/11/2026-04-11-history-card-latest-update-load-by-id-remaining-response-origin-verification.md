# history-card latest-update load-by-id remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-load-by-id-remaining-response-origin-verification.md` — latest `/work` 재검증 결과와 CONTROL_SEQ 92 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 92 implement handoff를 `history-card latest-update load-by-id stored-record remaining response-origin exact service bundle`로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-latest-update-load-by-id-remaining-response-origin-exact-service-bundle.md`) 가 latest-update history-card by-id show-only 경로의 `response_origin` exact-field tighten을 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 latest-update history-card response-origin family 안에서 남은 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline` 에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work` 는 현재 tree 기준으로 truthful합니다. `tests/test_web_app.py` 의 세 by-id latest-update 서비스 테스트가 모두 exact-field bundle을 실제로 잠그고 있습니다.
  - single-source by-id reload block: `tests/test_web_app.py:8488-8495`
  - mixed-source by-id reload block: `tests/test_web_app.py:8571-8578`
  - news-only by-id 신규 test + reload block: `tests/test_web_app.py:8580-8659`
- `/work` 의 rationale 도 현재 코드와 맞습니다. latest-update web response origin literal은 `_build_web_search_origin()` 에서 `provider = "web"`, `badge = "WEB"`, `label = mode_label`, `model = None`, `kind = "assistant"`, `answer_mode`, `source_roles`, `verification_label` 로 만들어지고 (`core/agent_loop.py:5304-5312`), web-search record save 시 그 payload 가 그대로 저장되며 (`core/agent_loop.py:6097-6107`, `storage/web_search_store.py:228-243`), show-only `load_web_search_record_id` 경로는 `stored_origin` 이 있으면 그것을 그대로 `reload_origin` 으로 재사용합니다 (`core/agent_loop.py:6370-6395`). 따라서 by-id show-only 세트에서 exact literal을 직접 잠근 이번 `/work` 설명은 정직합니다.
- 다음 exact slice 는 `history-card latest-update load-by-id stored-record remaining response-origin exact service bundle` 로 정했습니다.
  - 방금 닫힌 by-id latest-update trio (`tests/test_web_app.py:8424-8659`) 는 reload surface exact-field 는 잠겼지만, 세 session (`reload-by-id-single-session`, `reload-by-id-mixed-session`, `reload-by-id-news-session`) 모두 `service.web_search_store.get_session_record(...)` 기반 persisted `response_origin` exact assertion 은 아직 없습니다.
  - 반면 same-family follow-up latest-update trio 는 이미 stored-record exact-field 를 잠가 둔 상태입니다 (`tests/test_web_app.py:16873-17012`, `tests/test_web_app.py:17088-17125` 부근).
  - 따라서 남은 가장 가까운 same-family current-risk 는 direct history-card by-id reload 가 실제로 의존하는 persisted stored payload 자체를 single-source / mixed-source / news-only 세 variant 에서도 정확히 고정하는 것입니다.
- 이 슬라이스가 natural reload 또는 noisy-community latest-update tightening 보다 낫습니다.
  - by-id path 는 사용자가 history card 를 눌러 즉시 다시 불러오는 직접 경로이고, 방금 닫힌 reload surface 와 같은 테스트 묶음 안에서 persisted contract 까지 한 번에 닫을 수 있습니다.
  - noisy-community / natural latest-update 경로는 여전히 후보이지만, 현재 tree 에서는 같은 by-id 경로의 저장층 공백이 더 직접적인 same-family risk 로 보입니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_single_source_latest_update_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_mixed_source_latest_update_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_news_only_latest_update_exact_fields` → `Ran 3 tests in 0.062s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract 와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten 이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py` 의 세 by-id latest-update 서비스 테스트 assertion bundle 뿐이라 wider rerun 은 과합니다.

## 남은 리스크
- by-id latest-update trio 는 reload surface exact-field 는 잠겼지만 stored-record exact assertion 은 아직 없습니다.
- noisy-community latest-update family 의 show-only / stored / follow-up exact contract 는 아직 이 verification 범위 밖입니다.
- natural (non-history-card) latest-update reload 경로의 literal drift 여부는 아직 확인하지 않았습니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/verify` 및 `work/4/11/` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
