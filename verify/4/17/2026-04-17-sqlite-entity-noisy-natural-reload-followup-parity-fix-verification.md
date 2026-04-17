## 변경 파일
- 없음

## 사용 skill
- round-handoff

## 변경 이유
- `seq 268` Gemini advice는 새 Claude 구현보다 먼저 `work/4/17/2026-04-17-sqlite-entity-noisy-natural-reload-followup-parity-fix.md`를 retro-verify 하라고 권고했습니다.
- 이번 `/verify`는 해당 `/work`가 적은 product-code 수정(`core/agent_loop.py`)과 좁은 sqlite 회귀 검증이 현재 트리에서도 사실인지 다시 잠그고, 그 결과를 기준으로 다음 control이 정말 Claude 구현이어야 하는지까지 판단하기 위해 남깁니다.

## 핵심 변경
- `/work`의 핵심 주장은 현재 트리 기준으로 맞습니다.
  - `core/agent_loop.py`의 `_reuse_web_search_record` follow-up 경로에는 stored web-search summary prepend 복원 로직이 그대로 남아 있습니다.
  - `tests/test_web_app.py`에는 sqlite backend noisy entity-card natural-reload follow-up / second-follow-up 회귀 2건이 그대로 존재합니다.
- `/work`가 적은 좁은 sqlite 회귀 검증과 same-family Python 회귀 묶음을 이번 round에서 다시 실행했고 모두 통과했습니다.
  - focused sqlite service regression 2건: `2/2 ok`
  - focused sqlite Playwright exact title 2건: 각 `1 passed`
  - same-family service regression 6건: `6/6 ok`
  - reload family regression bundle: `83/83 ok`
  - noisy family regression bundle: `60/60 ok`
  - smoke reload bundle: `5/5 ok`
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`도 출력 없이 종료되어, 이번 `/work`가 적은 코드 범위에 whitespace/blocking diff 문제는 없었습니다.
- 다만 이 round로도 새 Claude implement handoff를 바로 열 수 있는 상태는 아닙니다.
  - Gemini advice가 지정한 high-risk code-change retro-verify는 이제 닫혔지만,
  - 더 최신 same-family `/work`인 `work/4/17/2026-04-17-sqlite-browser-history-card-natural-reload-chain-parity.md`는 여전히 matching `/verify`가 없습니다.
  - 따라서 지금 새 Claude 구현 slice를 열면 최신 same-family `/work`를 건너뛰거나, 이미 구현된 범위를 다시 시키는 stale handoff가 될 위험이 큽니다.

## 검증
```bash
python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_sqlite_backend_entity_card_noisy_single_source_natural_reload_follow_up_keeps_stored_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_sqlite_backend_entity_card_noisy_single_source_natural_reload_second_follow_up_keeps_stored_summary
# Ran 2 tests in 0.277s
# OK

cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line
# 1 passed (4.4s)

cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line
# 1 passed (4.2s)

python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_follow_up_preserves_claim_coverage_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_second_follow_up_preserves_claim_coverage_count_summary tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up
# Ran 6 tests in 0.417s
# OK

python3 -m unittest -v tests.test_web_app -k "reload"
# Ran 83 tests in 11.151s
# OK

python3 -m unittest -v tests.test_web_app -k "noisy"
# Ran 60 tests in 2.242s
# OK

python3 -m unittest -v tests.test_smoke -k "reload"
# Ran 5 tests in 0.060s
# OK

git diff --check -- core/agent_loop.py tests/test_web_app.py
# no output
```

## 남은 리스크
- `work/4/17/2026-04-17-sqlite-browser-history-card-natural-reload-chain-parity.md`는 same-family 최신 `/work`인데 아직 matching `/verify`가 없습니다. 현재 시점의 진짜 다음 일은 새 Claude 구현보다 이 truth-sync 공백을 어떻게 처리할지 정하는 쪽에 가깝습니다.
- 이번 round는 entity noisy natural-reload follow-up parity fix와 그 직결 same-family Python/sqlite 회귀만 다시 잠갔습니다. JSON-default Playwright 전체 suite, sqlite browser full suite, `make e2e-test`는 실행하지 않았습니다.
- sendrequest helper fix 관련 environment-bind 이슈를 다시 blocker로 세우지는 않았습니다. 해당 `/work`는 이미 matching `/verify`가 있으므로, 지금 남은 핵심 공백은 sandbox bind보다 newer same-family `/work`의 truth-sync 여부입니다.
