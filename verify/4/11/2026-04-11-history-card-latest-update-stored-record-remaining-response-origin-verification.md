# history-card latest-update stored-record remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-stored-record-remaining-response-origin-verification.md` — latest `/work` 재검증 결과와 CONTROL_SEQ 91 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 91 implement handoff를 `history-card latest-update load-by-id remaining response-origin exact service bundle`로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-latest-update-stored-record-remaining-response-origin-exact-service-bundle.md`) 가 latest-update history-card follow-up trio의 persisted `response_origin` exact-field tighten을 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 latest-update history-card response-origin family 안에서 다음 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline`에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`는 현재 tree 기준으로 truthful합니다. `tests/test_web_app.py`의 세 latest-update follow-up 서비스 테스트 모두에 persisted stored-record exact assertion이 실제로 추가되었습니다.
  - mixed-source follow-up stored block: `tests/test_web_app.py:16782-16798`
  - single-source follow-up stored block: `tests/test_web_app.py:16887-16901`
  - news-only follow-up stored block: `tests/test_web_app.py:16997-17011`
- 같은 세 테스트의 reload-follow-up exact assertion도 그대로 유지되고 있습니다.
  - `tests/test_web_app.py:16812-16820`
  - `tests/test_web_app.py:16915-16923`
  - `tests/test_web_app.py:17025-17033`
- `/work`의 rationale도 현재 코드와 맞습니다. web-search 결과 저장 시 `response_origin` 이 그대로 store에 기록되고 (`core/agent_loop.py:6097-6107`), 저장소는 그 payload를 `dict(response_origin or {})` 로 직렬화하며 (`storage/web_search_store.py:201-228`), show-only history-card reload는 `stored_origin` 이 있으면 그것을 그대로 `reload_origin` 으로 재사용합니다 (`core/agent_loop.py:6370-6395`). 따라서 follow-up trio에서 stored-record를 직접 잠근 것은 same-family current-risk reduction으로 정직합니다.
- 다음 exact slice는 `history-card latest-update load-by-id remaining response-origin exact service bundle`로 정했습니다.
  - basic `load_web_search_record_id` show-only latest-update tests는 아직 remaining literal drift를 허용합니다.
  - single-source `load_web_search_record_id` test는 `answer_mode`, `verification_label`, `source_roles`만 잠급니다: `tests/test_web_app.py:8424-8490`
  - mixed-source `load_web_search_record_id` test도 같은 수준입니다: `tests/test_web_app.py:8492-8568`
  - current tree에는 같은 non-noisy basic news-only `load_web_search_record_id` exact-field test가 없습니다.
- 이 슬라이스가 closest alternative보다 낫습니다.
  - noisy-community history-card reload family는 이미 noisy exclusion / verification-label parity 중심 계약이 넓게 존재해, 현재 남은 gap이 "basic latest-update show-only path literal exactness"보다 더 upstream current-risk로 보이지 않습니다.
  - 반면 basic `load_web_search_record_id` show-only path는 사용자가 history card를 눌러 즉시 다시 불러오는 가장 직접적인 경로이고, persisted record를 그대로 읽는 흐름 위에서 동작하지만 아직 `provider` / `badge` / `label` / `kind` / `model` exactness를 직접 잠그지 못했습니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests in 0.064s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py`의 세 latest-update follow-up 서비스 테스트 assertion bundle뿐이어서 wider rerun은 과합니다.

## 남은 리스크
- basic `load_web_search_record_id` show-only latest-update path는 아직 `provider` / `badge` / `label` / `kind` / `model` exact assertion이 없습니다.
- 같은 basic show-only path에 대응하는 non-noisy news-only latest-update exact-field test도 아직 없습니다.
- 세 latest-update follow-up 테스트의 `first_origin` 로컬은 현재 사용되지 않지만, 이번 라운드는 functionality truth 검증이 목적이어서 정리하지 않았습니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/verify` 및 `work/4/11/` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
