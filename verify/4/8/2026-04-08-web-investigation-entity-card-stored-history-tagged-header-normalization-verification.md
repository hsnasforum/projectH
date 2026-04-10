## 변경 파일
- `verify/4/8/2026-04-08-web-investigation-entity-card-stored-history-tagged-header-normalization-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-web-investigation-entity-card-stored-history-tagged-header-normalization.md`가 실제 코드와 rerun 결과를 truthfully 반영하는지 다시 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `verified-vs-uncertain explanation tightening` 라운드 기준이어서, 이번 latest `/work`를 반영한 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful하다고 확인했습니다.
  - `core/agent_loop.py:5583-5604`에 legacy entity-card section header를 현재 tagged contract로 올리는 `_normalize_legacy_summary_headers()`가 실제로 추가되어 있습니다.
  - `core/agent_loop.py:6274-6276`에서 stored `summary_text` reload 시 위 helper를 거쳐 normalize한 뒤 응답 본문에 사용합니다.
  - `tests/test_web_app.py:14984-14991`는 reload 본문이 정규화된 tagged header를 포함하는지 잠그고 있습니다.
  - `e2e/tests/web-smoke.spec.mjs:1850`, `e2e/tests/web-smoke.spec.mjs:6326`, `e2e/tests/web-smoke.spec.mjs:6401`도 browser-visible tagged header contract를 잠급니다.
- rerun verification도 모두 통과했습니다.
  - `python3 -m py_compile core/agent_loop.py tests/test_web_app.py`
  - focused unittest 6건
  - isolated Playwright 3건
  - `git diff --check`
- current docs truth도 이번 라운드 이후에는 구현과 맞습니다.
  - `docs/PRODUCT_SPEC.md:290` / `docs/PRODUCT_SPEC.md:315`의 tagged-header implemented wording은 이제 entity-card stored-history reload까지 포함해 truthful합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:42`의 response-body tagged header contract도 current behavior와 일치합니다.
- previous same-family current-risk reduction은 이번 라운드로 닫혔다고 판단했고, next slice는 `Web Investigation claim-coverage focus-slot reinvestigation copy tightening`으로 고정했습니다.
  - `docs/PRODUCT_SPEC.md:293`의 `clearer slot-level reinvestigation UX`가 아직 남아 있습니다.
  - current engine은 이미 `core/agent_loop.py:4248-4318`에서 focus-slot progress summary를 만들고, `tests/test_web_app.py:5346-5444`에서 `progress_label`, `previous_status_label`, `is_focus_slot` serialization을 잠급니다.
  - 하지만 current browser surface는 `app/static/app.js:2329-2384`에서 `재조사 대상 ·`, `변화: ...`, global hint를 따로 흩어 보여 주기 때문에, 사용자가 focus slot이 실제로 보강됐는지 또는 아직 단일 출처/미확인인지 한 줄로 읽기 어렵습니다.
  - `latest-update` stored-history legacy header normalization은 현재 tree에서 동일한 concrete gap이 확인되지 않아 다음 slice로 올리지 않았습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:1403-1405`의 regression-fixture / evaluation-coverage 항목은 verification gap이지만, 다음 기본 slice로 올릴 shipped user-visible contract는 아니라고 판단했습니다.
- `.pipeline/claude_handoff.md`를 위 판단에 맞춰 stale 상태에서 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,240p' work/4/8/2026-04-08-web-investigation-entity-card-stored-history-tagged-header-normalization.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-web-investigation-verified-vs-uncertain-explanation-tightening-verification.md`
- `nl -ba core/agent_loop.py | sed -n '4248,4320p;5578,5608p;6270,6299p'`
- `nl -ba app/static/app.js | sed -n '2311,2387p;3122,3182p'`
- `nl -ba tests/test_web_app.py | sed -n '5418,5445p;14792,15010p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1725,1852p;6266,6405p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '286,318p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '37,42p;1403,1405p'`
- `nl -ba docs/MILESTONES.md | sed -n '109,114p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '100,104p'`
- `python3 -m py_compile core/agent_loop.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_reload_preserves_stored_summary_text tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 noisy single-source claim\\(출시일/2025/blog.example.com\\)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim\\(출시일/2025/blog.example.com\\)이 자연어 reload 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim\\(출시일/2025/blog.example.com\\)이 자연어 reload 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다" --reporter=line`
- `git diff --check`
- full browser suite(`make e2e-test`)는 이번 risk 범위상 재실행하지 않았습니다.

## 남은 리스크
- full browser suite는 다시 돌리지 않았으므로, claim-coverage panel과 무관한 다른 browser scenario drift는 이번 검증 범위 밖입니다.
- next slice는 existing `claim_coverage` payload(`progress_label`, `previous_status_label`, `is_focus_slot`, `rendered_as`)만으로 UX를 명확히 할 수 있다는 가정 위에 잡았습니다. 만약 브라우저 copy만으로 충분하지 않으면 작은 additive payload sync가 필요할 수 있지만, ranking/selection logic 변경으로 넓히면 안 됩니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검수 범위 밖이라 손대지 않았습니다.
