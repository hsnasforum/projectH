# history-card latest-update natural-reload remaining response-origin exact 검증

## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-natural-reload-remaining-response-origin-verification.md` — latest `/work` 재검증 결과와 CONTROL_SEQ 94 기준 다음 슬라이스 판단을 기록했습니다.
- `.pipeline/claude_handoff.md` — CONTROL_SEQ 94 implement handoff를 `history-card latest-update natural-reload follow-up-chain remaining response-origin exact service bundle`로 갱신했습니다.

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` (`work/4/11/2026-04-11-history-card-latest-update-natural-reload-remaining-response-origin-exact-service-bundle.md`) 가 baseline natural reload latest-update trio의 stored `response_origin` + reload-surface exact-field tighten을 실제로 추가했는지 다시 확인해야 했습니다.
- 그 검증이 truthful하게 닫히면, 같은 latest-update response-origin family 안에서 다음 한 슬라이스를 current-risk 기준으로 하나만 좁혀 `.pipeline`에 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work` 는 현재 tree 기준으로 truthful합니다. `tests/test_web_app.py` 의 세 baseline natural reload latest-update 서비스 테스트 모두에 stored-record exact assertion 이 실제로 추가되어 있습니다.
  - mixed-source natural reload stored block: `tests/test_web_app.py:8217-8233`
  - single-source natural reload stored block: `tests/test_web_app.py:8325-8339`
  - news-only natural reload stored block: `tests/test_web_app.py:8438-8452`
- 같은 세 테스트의 reload-surface exact assertion 도 그대로 유지되고 있습니다.
  - mixed-source natural reload block: `tests/test_web_app.py:8246-8255`
  - single-source natural reload block: `tests/test_web_app.py:8352-8361`
  - news-only natural reload block: `tests/test_web_app.py:8465-8474`
- `/work` 의 rationale 도 현재 코드와 맞습니다. latest-update web response origin literal은 `_build_web_search_origin()` 에서 `provider = "web"`, `badge = "WEB"`, `label = mode_label`, `model = None`, `kind = "assistant"`, `answer_mode`, `source_roles`, `verification_label` 로 만들어지고 (`core/agent_loop.py:5304-5312`), web-search record save 시 그 payload 가 그대로 저장되며 (`core/agent_loop.py:6097-6107`, `storage/web_search_store.py:228-243`), baseline natural reload 도 같은 record 를 재사용하는 경로라서 stored payload 와 reload surface 를 함께 잠근 이번 `/work` 설명은 정직합니다.
- 다음 exact slice 는 `history-card latest-update natural-reload follow-up-chain remaining response-origin exact service bundle` 로 정했습니다.
  - current tree 의 natural reload first/second follow-up 6개 테스트는 모두 `badge`, `answer_mode`, `verification_label`, `source_roles`, `source_paths`만 잠그고, `provider` / `label` / `kind` / `model` exactness 는 아직 없습니다.
  - mixed-source first follow-up: `tests/test_web_app.py:19127-19134`
  - mixed-source second follow-up: `tests/test_web_app.py:19196-19203`
  - single-source first follow-up: `tests/test_web_app.py:19254-19260`
  - single-source second follow-up: `tests/test_web_app.py:19313-19319`
  - news-only first follow-up: `tests/test_web_app.py:19376-19383`
  - news-only second follow-up: `tests/test_web_app.py:19442-19449`
  - 다음 라운드는 이 여섯 테스트에서 response-origin exact surface continuity 를 한 번에 닫는 편이 맞습니다. first follow-up 과 second follow-up 을 또 둘로 나누는 것보다, 같은 natural reload chain 안에서 하나의 reviewable bundle 로 닫는 편이 더 정직합니다.
- 이 슬라이스가 noisy-community latest-update tightening 보다 낫습니다.
  - baseline natural reload path 는 이번 라운드에서 stored + reload 두 층이 닫혔습니다.
  - 다음으로 가장 가까운 same-family current-risk 는 edge/noisy filter 확장보다, 같은 baseline path 의 first/second follow-up chain 에 남아 있는 exact-field 공백입니다.

## 검증
- 실행: `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_mixed_source_latest_update_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_single_source_latest_update_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_news_only_latest_update_reload_exact_fields` → `Ran 3 tests in 0.050s OK`
- 실행: `git diff --check -- tests/test_web_app.py work/4/11` → 출력 없음
- 이번 라운드에서 재대조: `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` → current shipped contract 와 충돌하는 문서 드리프트는 보지 못했습니다. 이번 범위는 service-test assertion tighten 이므로 docs 갱신 대상은 아닙니다.
- 이번 라운드에서 재실행하지 않음: `python3 -m unittest -v tests.test_web_app` 전체, Playwright, `make e2e-test` — latest `/work` 변경은 `tests/test_web_app.py` 의 세 natural reload latest-update 서비스 테스트 assertion bundle 뿐이라 wider rerun 은 과합니다.

## 남은 리스크
- natural reload first/second follow-up latest-update chain 은 아직 `provider` / `label` / `kind` / `model` exact-field continuity 를 열어 둔 상태입니다.
- noisy-community latest-update family 의 history-card / natural reload / follow-up / second-follow-up exact contract 는 아직 이 verification 범위 밖입니다.
- entity-card 외 다른 family 의 remaining natural reload continuity 공백은 이번 라운드에서 다시 우선순위를 올리지 않았습니다.
- 저장소 상태는 계속 dirty합니다. 현재 pending `tests/test_web_app.py`, 기존 `/verify` 및 `work/4/11/` 파일들을 되돌리지 않는 전제가 다음 라운드에도 유지되어야 합니다.
