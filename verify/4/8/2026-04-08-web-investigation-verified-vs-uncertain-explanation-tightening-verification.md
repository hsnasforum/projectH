## 변경 파일
- `verify/4/8/2026-04-08-web-investigation-verified-vs-uncertain-explanation-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-web-investigation-verified-vs-uncertain-explanation-tightening.md`가 claimed tag-annotation wording, docs sync, focused rerun 결과를 current tree가 실제로 만족하는지 다시 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `verified-vs-uncertain explanation tightening` handoff 기준이어서, 이번 latest `/work`까지 반영한 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 핵심 구현과 rerun 주장은 재현됐습니다.
  - `core/agent_loop.py:4537-4574`는 entity-card / latest-update 생성 경로에서 `확인된 사실 [교차 확인]:`, `단일 출처 정보 [단일 출처] (추가 확인 필요):`, `확인되지 않은 항목 [미확인]:`를 실제로 출력합니다.
  - `app/static/app.js:2329-2385`는 claim-coverage hint를 `[교차 확인]`, `[단일 출처]`, `[미확인]` 설명과 함께 렌더링합니다.
  - `docs/PRODUCT_SPEC.md:287-315`, `docs/ACCEPTANCE_CRITERIA.md:37-42`, `README.md:134`는 새 wording과 현재 browser contract를 반영합니다.
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`는 `Ran 330 tests in 68.117s`, `OK`로 재현됐고, latest `/work`에 적힌 Playwright 2개 시나리오도 각각 `1 passed`로 재현됐습니다.
- 다만 latest `/work`의 `모든 관련 assertion을 새 문구에 맞춰 업데이트`라는 표현은 fully truthful하지 않습니다.
  - entity-card stored-history reload 경로는 아직 `core/agent_loop.py:6251-6253`에서 `record["summary_text"]`를 그대로 재사용합니다.
  - `tests/test_web_app.py:14892-14985`는 이 show-only reload behavior를 현재도 명시적으로 잠그고 있습니다.
  - `e2e/tests/web-smoke.spec.mjs:1777-1851`, `e2e/tests/web-smoke.spec.mjs:4294-4327`, `e2e/tests/web-smoke.spec.mjs:6293-6328`에는 여전히 legacy `확인된 사실:` fixture / expectation이 남아 있습니다.
  - 추가 rerun한 Playwright `history-card entity-card 다시 불러오기 후 noisy single-source claim(출시일/2025/blog.example.com)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다`도 `1 passed`로 통과해, browser reload가 아직 legacy stored summary wording을 그대로 보여주는 current truth를 확인했습니다.
- 따라서 current shipped truth는 다음과 같습니다.
  - 새로 생성되는 web-investigation 응답은 tagged section header contract를 사용합니다.
  - 그러나 기존 stored entity-card history record를 reload / natural reload follow-up에 재사용할 때는 legacy untagged header가 그대로 노출될 수 있습니다.
  - 현재 docs는 generated path truth에는 맞지만, stored-history reload path까지는 아직 완전히 맞지 않습니다.
- `.pipeline/claude_handoff.md`는 same-family current-risk reduction으로 `Web Investigation entity-card stored-history tagged-header normalization` 한 개로 갱신했습니다.
  - 이유: `clearer slot-level reinvestigation UX`는 same-family user-visible improvement이지만, stored-history reload header inconsistency는 current shipped flow risk이므로 tie-break상 먼저 닫는 편이 맞습니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-web-investigation-verified-vs-uncertain-explanation-tightening.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-acceptance-criteria-product-spec-agreement-reinvestigation-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '286,318p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '34,70p'`
- `nl -ba README.md | sed -n '140,190p'`
- `nl -ba docs/MILESTONES.md | sed -n '1,220p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '1,220p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '1,220p'`
- `rg -n "확인된 사실 \\[교차 확인\\]|단일 출처 정보 \\[단일 출처\\]|확인되지 않은 항목 \\[미확인\\]|\\[교차 확인\\] 여러 출처가 합의한 사실|\\[단일 출처\\] 1개 출처에서만 확인된 정보|\\[미확인\\] 추가 조사가 필요한 항목" core/agent_loop.py app/static/app.js tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md -n -S`
- `git diff -- core/agent_loop.py app/static/app.js tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md README.md`
- `nl -ba core/agent_loop.py | sed -n '4528,4585p'`
- `nl -ba app/static/app.js | sed -n '2320,2395p'`
- `nl -ba core/agent_loop.py | sed -n '6248,6325p'`
- `nl -ba tests/test_web_app.py | sed -n '14892,14985p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1768,1860p;1890,1932p;2870,3015p;4288,4338p;6285,6410p'`
- `rg -n '확인된 사실:' . -S`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `git diff --check`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel은 status tag와 행동 힌트를 올바르게 렌더링합니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 클릭 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 유지됩니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 noisy single-source claim\\(출시일/2025/blog.example.com\\)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance가 유지됩니다" --reporter=line`

## 남은 리스크
- entity-card stored-history reload / natural reload follow-up는 existing record JSON의 legacy `summary_text`를 그대로 재사용하므로, current docs가 말하는 tagged header contract와 실제 browser-visible output이 어긋날 수 있습니다.
- `docs/PRODUCT_SPEC.md:293`의 `clearer slot-level reinvestigation UX`는 여전히 same-family follow-up으로 남아 있습니다. 다만 tie-break상 stored-history current-risk reduction 다음이 더 맞습니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `.pipeline/README.md`, `windows-launchers/README.md`, unrelated `work/` / `verify/` notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
