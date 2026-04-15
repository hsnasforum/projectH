# history-card latest-update follow-up remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-follow-up-remaining-response-origin-verification.md` — latest `/work` 재검증 결과와 CONTROL_SEQ 90 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 90 implement handoff를 `history-card latest-update stored-record remaining response-origin exact service bundle`로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-latest-update-follow-up-remaining-response-origin-exact-service-bundle.md`) 가 latest-update history-card reload-follow-up 경로의 `response_origin` exact-field tighten을 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 latest-update history-card response-origin family 안에서 다음 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline`에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`는 현재 tree 기준으로 truthful합니다. `tests/test_web_app.py`의 세 latest-update follow-up 서비스 테스트 모두에 latest-update exact-field assertion이 실제로 추가되었습니다.
  - mixed-source follow-up: `tests/test_web_app.py:16769-16816`
  - single-source follow-up: `tests/test_web_app.py:16856-16904`
  - news-only follow-up: `tests/test_web_app.py:16950-16992`
- 위 세 블록은 이제 공통으로 `reload_origin["provider"] == "web"`, `reload_origin["badge"] == "WEB"`, `reload_origin["label"] == "외부 웹 최신 확인"`, `reload_origin["kind"] == "assistant"`, `reload_origin["model"] is None`, `reload_origin["answer_mode"] == "latest_update"`를 exact-field로 잠그고, variant별 `verification_label` / `source_roles`도 exact하게 유지합니다.
- `/work`의 rationale도 현재 코드와 맞습니다. core runtime은 latest-update web response origin literal을 이미 고정합니다 (`core/agent_loop.py:5304-5312`), 그리고 latest `/work`가 건드린 follow-up trio는 실제로 그 literal을 직접 검증하는 상태가 되었습니다.
- 다음 exact slice는 `history-card latest-update stored-record remaining response-origin exact service bundle`로 정했습니다.
  - 현 단계에서 remaining same-family current-risk는 latest-update persisted record 자체가 아직 직접 잠겨 있지 않다는 점입니다.
  - `storage/web_search_store.py:201-228` 은 `response_origin` 을 `dict(response_origin or {})` 로 그대로 저장합니다.
  - `core/agent_loop.py:6097-6107` 은 web-search 결과 저장 시 그 `response_origin` 을 그대로 store에 넘깁니다.
  - `core/agent_loop.py:6370-6395` 는 show-only history-card reload에서 `stored_origin` 이 있으면 그것을 바로 `reload_origin` 으로 재사용합니다.
  - 따라서 persistence contract를 직접 잠그는 편이 another show-only micro-tightening보다 same-family current-risk reduction에 더 가깝습니다.
- 이 슬라이스가 closest alternative보다 낫습니다.
  - basic `load_web_search_record_id` show-only latest-update exact-field 테스트 (`tests/test_web_app.py:8424-8490`, `tests/test_web_app.py:8492-8568`) 도 아직 `answer_mode` / `verification_label` / `source_roles` 중심으로만 남아 있지만, 그것은 이미 저장된 record를 읽어 온 뒤의 응답면 검증입니다.
  - 반면 stored-record exactness는 click-reload와 follow-up 양쪽보다 upstream인 persistence boundary를 직접 잠그므로 먼저 닫는 편이 더 방어적입니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_reload_follow_up_preserves_stored_response_origin tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_reload_follow_up_preserves_stored_response_origin` → `Ran 3 tests in 0.080s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py`의 세 latest-update follow-up 서비스 테스트 assertion bundle뿐이어서 wider rerun은 과합니다.

## 남은 리스크
- latest-update family의 stored-record exact-field 계약은 아직 직접 잠겨 있지 않습니다. 현 시점 테스트는 reload 응답 exactness만 강화했고 persisted `response_origin` 자체는 검수하지 않았습니다.
- basic `load_web_search_record_id` show-only latest-update exact-field 테스트도 아직 `provider` / `badge` / `label` / `kind` / `model` literal을 직접 잠그지 않습니다.
- 세 latest-update follow-up 테스트의 `first_origin` 로컬은 현재 사용되지 않지만, 이번 라운드는 functionality truth 검증이 목적이어서 정리하지 않았습니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/verify` 및 `work/4/11/` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
