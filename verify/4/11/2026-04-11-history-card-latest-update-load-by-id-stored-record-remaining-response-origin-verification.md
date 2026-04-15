# history-card latest-update load-by-id stored-record remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-load-by-id-stored-record-remaining-response-origin-verification.md` — latest `/work` 재검증 결과와 CONTROL_SEQ 93 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 93 implement handoff를 `history-card latest-update natural-reload remaining response-origin exact service bundle`로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-latest-update-load-by-id-stored-record-remaining-response-origin-exact-service-bundle.md`) 가 latest-update history-card by-id 경로의 persisted `response_origin` exact-field tighten을 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 latest-update response-origin family 안에서 다음 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline`에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work` 는 현재 tree 기준으로 truthful합니다. `tests/test_web_app.py` 의 세 by-id latest-update 서비스 테스트에 persisted stored-record exact assertion 이 실제로 추가되어 있습니다.
  - single-source by-id stored block: `tests/test_web_app.py:8475-8489`
  - mixed-source by-id stored block: `tests/test_web_app.py:8574-8590`
  - news-only by-id stored block: `tests/test_web_app.py:8673-8687`
- 같은 세 테스트의 reload-surface exact assertion 도 그대로 유지되고 있습니다.
  - single-source by-id reload block: `tests/test_web_app.py:8502-8511`
  - mixed-source by-id reload block: `tests/test_web_app.py:8603-8612`
  - news-only by-id reload block: `tests/test_web_app.py:8700-8709`
- `/work` 의 rationale 도 현재 코드와 맞습니다. latest-update web response origin literal은 `_build_web_search_origin()` 에서 `provider = "web"`, `badge = "WEB"`, `label = mode_label`, `model = None`, `kind = "assistant"`, `answer_mode`, `source_roles`, `verification_label` 로 만들어지고 (`core/agent_loop.py:5304-5312`), web-search record save 시 그 payload 가 그대로 저장되며 (`core/agent_loop.py:6097-6107`, `storage/web_search_store.py:228-243`), show-only reload 는 `stored_origin` 이 있으면 그것을 그대로 `reload_origin` 으로 재사용합니다 (`core/agent_loop.py:6370-6395`). 따라서 by-id stored payload 자체를 직접 잠근 이번 `/work` 설명은 정직합니다.
- 다음 exact slice 는 `history-card latest-update natural-reload remaining response-origin exact service bundle` 로 정했습니다.
  - baseline natural reload trio 는 아직 `provider` / `badge` / `label` / `kind` / `model` exact assertion 이 없고, stored-record exact assertion 도 없습니다.
  - mixed-source natural reload test는 현재 `answer_mode`, `verification_label`, `source_roles`만 잠급니다: `tests/test_web_app.py:8155-8247`
  - single-source natural reload test도 같은 수준입니다: `tests/test_web_app.py:8249-8330`
  - news-only natural reload test도 같은 수준입니다: `tests/test_web_app.py:8332-8422`
  - 다음 라운드는 이 세 자연어 reload 테스트에서 reload-surface exact literals와 `service.web_search_store.get_session_record(...)` 기반 stored-record exact literals를 한 번에 닫는 편이 맞습니다. 같은 stored-origin reuse 계약 위에 올라타는 두 층을 또 둘로 쪼개는 것보다, 자연스러운 한 묶음으로 닫는 편이 더 reviewable 합니다.
- 이 슬라이스가 noisy-community latest-update tightening 보다 낫습니다.
  - by-id history-card path 는 이번 라운드에서 이미 surface + stored 두 층이 닫혔습니다.
  - 다음으로 가장 가까운 same-family current-risk 는 edge/noisy filter가 아니라, 사용자가 같은 세션에서 바로 쓰는 baseline natural reload (`방금 검색한 결과 다시 보여줘`) 경로의 exactness 공백입니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_single_source_latest_update_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_mixed_source_latest_update_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_news_only_latest_update_exact_fields` → `Ran 3 tests in 0.052s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract 와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten 이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py` 의 세 by-id latest-update 서비스 테스트 assertion bundle 뿐이라 wider rerun 은 과합니다.

## 남은 리스크
- baseline natural reload latest-update trio 는 아직 reload-surface exact literal과 stored-record exact literal을 모두 열어 둔 상태입니다.
- noisy-community latest-update family 의 by-id / follow-up / second-follow-up exact contract 는 아직 이 verification 범위 밖입니다.
- entity-card 외 다른 family 의 remaining stored-record exactness 는 이번 라운드에서 다시 우선순위를 올리지 않았습니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/verify` 및 `work/4/11/` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
