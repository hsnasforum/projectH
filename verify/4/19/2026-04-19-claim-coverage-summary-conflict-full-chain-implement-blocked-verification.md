# 2026-04-19 claim coverage summary conflict full chain implement-blocked verification

## 변경 파일
- `verify/4/19/2026-04-19-claim-coverage-summary-conflict-full-chain-implement-blocked-verification.md`

## 사용 skill
- `round-handoff`: `.pipeline/claude_handoff.md` seq 373 (`Claim Coverage Summary CONFLICT — full browser-visible chain`) implement_blocked sentinel을 받아 최신 `/work`/`/verify`와 현재 tree를 대조하고 다음 단일 control slot을 골랐습니다.

## 변경 이유
- seq 373 implement 슬라이스(`app/serializers.py` + `app/static/app.js` + `tests/test_web_app.py` + `e2e/tests/web-smoke.spec.mjs`)가 실제 edit 전에 `BLOCK_REASON_CODE: storage_summary_missing_conflict`로 막혔습니다.
- 같은 날 최신 `/work`(`work/4/19/2026-04-19-agent-loop-conflict-labeling.md`)와 `/verify`(`verify/4/19/2026-04-19-agent-loop-conflict-labeling-verification.md`)는 seq 369 agent_loop CONFLICT 내부 분기 closeout이라, 이번 implement_blocked triage를 in-place로 덮으면 이전 truth가 손상됩니다. 따라서 이번 triage 전용 새 verify 노트를 추가했습니다.
- 블로커가 진짜인지, 또 next control을 Gemini로 돌려야 하는지 operator로 돌려야 하는지 판단을 이 노트에 고정한 뒤 `.pipeline` slot을 움직였습니다.

## 핵심 변경
- implement_blocked 블로커는 실제로 현재 tree에 존재합니다.
  - `storage/web_search_store.py:237-245` `_summarize_claim_coverage`는 `{"strong": 0, "weak": 0, "missing": 0}` 세 키로만 카운터를 초기화하고 `if status in counts:` 가드를 쓰기 때문에, `CoverageStatus.CONFLICT == "conflict"` 상태 항목은 그대로 drop됩니다.
  - `app/serializers.py:263-302` `_serialize_web_search_history`는 이 stored summary(`item.get("claim_coverage_summary")`)를 그대로 사용합니다. 따라서 seq 373이 명시한 `app/serializers.py:282-286` CONFLICT 키를 `item.get(...).get(CoverageStatus.CONFLICT)` 형태로 읽도록 넓히더라도, 세션 기록 history 카드에서는 항상 `conflict: 0`만 나옵니다.
  - 즉 seq 373 SCOPE_LIMITS가 `storage/web_search_store.py`를 제외한 채 "full browser-visible chain"을 주장하는 것은 현재 storage 경계 기준으로 성립하지 않습니다.
- 반면 seq 366 `core/contracts.py`/`core/web_claims.py`, seq 369 `core/agent_loop.py` CONFLICT 분기는 그대로 유효하고 `/verify`가 이미 truthful하게 닫아 두었습니다. 이번 블로커는 다음 슬라이스 scope 판정 문제일 뿐 이전 라운드 truth를 흔들지 않습니다.
- scope 조정에는 최소 세 축이 동시에 존재해 low-confidence prioritization에 해당합니다.
  - A) `storage/web_search_store.py::_summarize_claim_coverage`까지 같은 라운드에 포함해 "full browser-visible chain"의 실제 완결을 맞춘다. scope는 한 파일만 더 늘어납니다.
  - B) serializer/app.js/tests/e2e만 손대고 history list 경로는 영구적으로 `conflict: 0`으로 두되, 라이브 세션 entity-card 경로가 이미 full summary dict를 넘겨 주는지 확인되면 user-visible 이득이 부분적으로 남는다고 정당화한다.
  - C) 순서를 쪼갠다. 먼저 `storage/web_search_store.py` 단일 파일로 storage 카운터를 4키로 넓히는 좁은 라운드를 돌리고, 그 다음에 seq 373의 serializer/app.js/e2e/tests 조합을 그대로 실행한다.
- 같은 날 same-family docs-only 반복 guard는 적용 대상이 아닙니다. seq 366/seq 369가 implement round이고 seq 373도 implement round였기 때문에, 다음 라운드도 implement로 가는 것이 원칙적으로 허용됩니다.
- 이번 triage는 operator-only 결정(approval/truth-sync blocker, safety stop, Gemini unavailable)이 아닙니다. Gemini arbitration이 한 번도 이 scope 질문을 받지 않은 상태라 먼저 `.pipeline/gemini_request.md` seq 374로 Gemini에 넘기는 편이 rule에 맞습니다.

## 검증
- 직접 코드 대조
  - `app/serializers.py:263-302`, `storage/web_search_store.py:237-245`, `storage/web_search_store.py:347-369`를 읽어 serializer가 storage의 3-key summary를 그대로 소비한다는 사실을 확인했습니다.
  - `core/contracts.py:121-130`을 읽어 `CoverageStatus.CONFLICT == "conflict"` literal이 여전히 shipped인지 확인했습니다.
  - `work/4/19/2026-04-19-agent-loop-conflict-labeling.md`, `verify/4/19/2026-04-19-agent-loop-conflict-labeling-verification.md`, `.pipeline/gemini_advice.md` (seq 371), `.pipeline/gemini_request.md` (seq 370, 이미 답변됨), `.pipeline/operator_request.md` (seq 363, 이미 닫힘) 전부 현재 상태로 읽었습니다.
- 명령 재실행
  - 이번 라운드는 triage-only입니다. `tests.test_smoke`, `tests.test_web_app`, Playwright, `make e2e-test` 같은 verification은 이번 verify에서 다시 돌리지 않았습니다.
  - 이유: storage/serializer/app.js/e2e에 실제 edit이 들어가지 않았고, 최신 `/work`(seq 369)가 주장한 `core/agent_loop.py` 변경은 같은 날 선행 verify(`agent-loop-conflict-labeling-verification`)에서 이미 `tests.test_smoke -k coverage` + `py_compile` + `git diff --check`로 닫혀 있었습니다. 이번 triage 범위에서 그 명령을 다시 돌릴 의미가 없었습니다.
- git 상태
  - `app/serializers.py`, `app/static/app.js`, `e2e/tests/web-smoke.spec.mjs`, `storage/` 등은 이전 라운드들부터 이어진 기존 dirty 상태 그대로이며, 이번 triage에서 추가 수정하지 않았습니다.

## 남은 리스크
- Gemini가 A/B/C 중 어느 쪽을 추천하느냐에 따라 다음 implement round의 파일 수와 browser 검증 범위가 달라집니다. 이번 verify는 그 결정을 내리지 않았습니다.
- `storage/web_search_store.py::_summarize_claim_coverage`는 현재 tree에서 여전히 3-key로 남아 있으므로, 그 상태로 history list 기반 CONFLICT 회귀를 작성하면 잘못된 "fixed" 주장이 됩니다. 다음 라운드는 이 파일을 반드시 같이 수정하거나 그것을 배제한 채로 full-chain 주장을 하지 말아야 합니다.
- `app/static/app.js::renderFactStrengthBar` in-answer fact strength 표면과 `core/agent_loop.py` focus_slot wording 확장은 이번 triage의 scope 밖으로 그대로 남겨 두었습니다. seq 369/seq 373 흐름이 이미 후속 후보로 기록해 둔 상태입니다.
- broad `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` failure는 이전 verify에서 이미 dirty state의 별도 truth-sync 라운드 몫으로 기록돼 있고, 이번 triage에서도 그대로입니다.
