## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-noisy-community-initial-response-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/11/2026-04-11-history-card-latest-update-noisy-community-initial-response-exact-service-bundle.md`가 주장한 noisy-community latest-update initial response의 surface/stored `response_origin` exactness가 실제 코드와 targeted 검증 결과에 부합하는지 truthfully 다시 확인해야 했습니다.
- 확인이 끝난 뒤에는 같은 noisy-community latest-update family 안에서 남은 current-risk 한 개만 다음 Claude 구현 슬라이스로 남겨야 했습니다.

## 핵심 변경
- `tests/test_web_app.py`의 `test_handle_chat_latest_update_noisy_source_excluded_from_body_and_badge`가 실제로 initial response exact-field contract까지 강화되어 있음을 확인했습니다.
- initial response surface `response_origin` exact literal은 `provider`, `badge`, `label`, `kind`, `model`, `answer_mode`, `verification_label`, `source_roles`까지 직접 잠기고 있습니다 (`tests/test_web_app.py:11703`, `tests/test_web_app.py:11715`).
- 같은 테스트 안에서 initial history entry의 `verification_label`, zero-count `claim_coverage_summary`, 빈 `claim_coverage_progress_summary`도 직접 잠기고 있습니다 (`tests/test_web_app.py:11721`, `tests/test_web_app.py:11732`).
- 같은 session id에 대해 `service.web_search_store.get_session_record("latest-update-noisy-session", record_id)`를 읽어 persisted stored `response_origin` exact literal도 직접 잠기고 있습니다 (`tests/test_web_app.py:11734`, `tests/test_web_app.py:11749`).
- 최신 `/work`까지 반영하면 noisy-community latest-update service family는 initial response, natural-reload reload-only, natural-reload first/second follow-up, click-reload show-only, click-reload first/second follow-up을 모두 surface + stored exactness로 직접 검증합니다.
- 반대로 browser smoke 쪽 same-family current-risk는 남아 있습니다. existing Playwright noisy click-reload show-only 시나리오(`e2e/tests/web-smoke.spec.mjs:2361`)는 현재 docs와 service truth가 기대하는 `기사 교차 확인` / `보조 기사` 대신 preseeded fixture와 assertion에서 `공식+기사 교차 확인` / `공식 기반`을 사용하고 있습니다 (`e2e/tests/web-smoke.spec.mjs:2414`, `e2e/tests/web-smoke.spec.mjs:2466`). 반면 docs는 이미 noisy latest-update click-reload browser contract를 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`, negative `보조 커뮤니티` / `brunch`로 설명하고 있습니다 (`README.md:145`, `docs/ACCEPTANCE_CRITERIA.md:1372`, `docs/MILESTONES.md:55`, `docs/TASK_BACKLOG.md:27`). 그래서 다음 handoff는 `history-card latest-update noisy-community click-reload browser truth-sync bundle`로 좁혔습니다.

## 검증
- 코드 대조:
  - `nl -ba tests/test_web_app.py | sed -n '11690,11770p'`
  - `rg -n "보조 커뮤니티|brunch|latest-update|latest_update|history-card" e2e tests/test_smoke.py tests/test_web_app.py`
  - `rg -n "noisy community|보조 커뮤니티|brunch|natural reload|reload-only|초기 검색" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2361,2495p'`
- targeted 회귀:
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_noisy_source_excluded_from_body_and_badge`
  - 결과: `Ran 1 test in 0.023s OK`
- 포맷 확인:
  - `git diff --check -- tests/test_web_app.py work/4/11`
  - 결과: 출력 없음
- 전체 `tests.test_web_app`, Playwright, `make e2e-test`는 이번 라운드 범위가 service-test initial-response exactness truth check라 재실행하지 않았습니다.

## 남은 리스크
- noisy-community latest-update browser family에서는 existing click-reload show-only Playwright fixture/expectation이 service/docs truth와 어긋난 채 남아 있습니다.
- 그 browser truth-sync를 닫기 전까지는 same-family user-visible smoke가 `기사 교차 확인` / `보조 기사` 대신 stale mixed-source expectation을 유지합니다.
- 작업 트리는 여전히 dirty 상태이므로 다음 구현 라운드는 기존 pending `/verify`, `/work`, 그리고 untracked `docs/projectH_pipeline_runtime_docs/`를 되돌리거나 정리하지 않고 지정된 파일 범위만 좁게 수정해야 합니다.
