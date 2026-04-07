## 변경 파일
- `verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-fixture-truth-sync-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-fixture-truth-sync-tightening.md`가 dual-probe natural-reload source-path fixture truth-sync를 실제 트리에서 truthful하게 닫았는지 다시 확인해야 했습니다.
- same-day latest `/verify`인 `verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-response-origin-truth-sync-tightening-verification.md`가 다음 same-family slice를 dual-probe natural-reload source-path fixture truth-sync로 고정했으므로, 이번 round가 그 exact slice를 실제로 닫았는지와 다음 same-family current-risk를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 구현 주장은 current tree와 일치했습니다. `e2e/tests/web-smoke.spec.mjs:4168-4175`, `e2e/tests/web-smoke.spec.mjs:4193-4194`, `e2e/tests/web-smoke.spec.mjs:4406-4413`, `e2e/tests/web-smoke.spec.mjs:4430-4432`는 dual-probe natural-reload source-path scenarios 41/43의 pre-seeded `response_origin`과 history item을 `설명형 다중 출처 합의` + `["공식 기반", "백과 기반"]`로 sync하고 있었습니다.
- focused rerun도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_search_natural_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_follow_up_preserves_response_origin`는 `OK (2 tests, 0.119s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload에서 source path가 context box에 유지됩니다" --reporter=line`는 `1 passed (7.0s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다" --reporter=line`는 `1 passed (7.0s)`였습니다. `git diff --check -- e2e/tests/web-smoke.spec.mjs`도 clean이었습니다.
- 다음 exact slice는 `history-card entity-card dual-probe source-path fixture truth-sync tightening`으로 좁혔습니다. 같은 verification family의 history-card source-path scenarios가 아직 stale single-source fixture를 유지하기 때문입니다. `e2e/tests/web-smoke.spec.mjs:1991-1998`, `e2e/tests/web-smoke.spec.mjs:2015-2017`, `e2e/tests/web-smoke.spec.mjs:2955-2962`, `e2e/tests/web-smoke.spec.mjs:2979-2981`는 pre-seeded record와 history item을 아직 `설명형 단일 출처` + `백과 기반`으로 두고 있고, service-side stored-record fixture도 `tests/test_web_app.py:8528-8533`, `tests/test_web_app.py:15373-15378`에서 같은 stale shape를 유지합니다.
- 반면 same family의 runtime truth anchor는 이미 있습니다. `tests/test_web_app.py:9024-9117`의 history-card reload exact-field test는 actual runtime 저장 record 기준으로 `first_origin` equality를 잠그고, direct probe에서도 manually seeded stale dual-probe record reload/follow-up가 그대로 `설명형 단일 출처` + `백과 기반`을 내보냈습니다. 따라서 다음 slice는 shipped runtime 코드 수정이 아니라, history-card dual-probe source-path service/browser synthetic record를 current runtime truth에 맞게 sync하는 same-family current-risk reduction으로 잡는 편이 맞습니다.

## 검증
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-fixture-truth-sync-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-response-origin-truth-sync-tightening-verification.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4119,4484p'`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_search_natural_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_follow_up_preserves_response_origin`
  - `OK (2 tests, 0.119s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload에서 source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (7.0s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (7.0s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - clean
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1942,2050p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2909,3027p'`
- `nl -ba tests/test_web_app.py | sed -n '8498,8570p'`
- `nl -ba tests/test_web_app.py | sed -n '9024,9117p'`
- `nl -ba tests/test_web_app.py | sed -n '15354,15415p'`
- `python3 - <<'PY' ...`
  - `stored_dual_probe_reload_origin= {'provider': 'web', 'badge': 'SYSTEM', 'label': '시스템 응답', 'model': None, 'kind': 'assistant', 'answer_mode': 'entity_card', 'source_roles': ['백과 기반'], 'verification_label': '설명형 단일 출처'}`
  - `stored_dual_probe_followup_origin= {'provider': 'web', 'badge': 'SYSTEM', 'label': '시스템 응답', 'model': None, 'kind': 'assistant', 'answer_mode': 'entity_card', 'source_roles': ['백과 기반'], 'verification_label': '설명형 단일 출처'}`
  - `stored_dual_probe_source_paths= ['https://www.pearlabyss.com/200', 'https://www.pearlabyss.com/300', 'https://namu.wiki/w/test']`

## 남은 리스크
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 round는 dual-probe natural-reload source-path fixture truth-sync 1건에 대한 focused rerun이었고, shared helper 변경 신호는 보이지 않았습니다.
- Playwright isolated scenarios는 smoke 서버 포트를 공유하므로 이번에도 serial rerun 기준으로 확인했습니다.
- 다음 same-family current-risk는 history-card dual-probe source-path service/browser synthetic record가 still-pass 상태로 stale single-source `response_origin`을 들고 있다는 점입니다. history-card reload exact-field anchor는 이미 actual runtime truth를 잠그고 있으므로, source-path scenarios와 stored-record tests도 같은 impossible synthetic record를 더 이상 유지하지 않도록 맞출 필요가 있습니다.
