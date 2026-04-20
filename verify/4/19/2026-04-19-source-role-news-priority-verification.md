# 2026-04-19 source-role news priority verification

## 변경 파일
- `verify/4/19/2026-04-19-source-role-news-priority-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-source-role-news-priority.md`)의 code 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`source-role-descriptive-priority-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 397 (`Milestone 4 Source Role Weighting — NEWS elevation above AUXILIARY in _ROLE_PRIORITY`)는 Gemini advice 396이 지정한 exact 변경(`SourceRole.NEWS` priority `1 → 2`)에 맞춰 `core/web_claims.py` 한 줄과 `tests/test_smoke.py` 새 focused regression만 추가하는 code-only 슬라이스였습니다.
- 이번 `/work`가 `_ROLE_PRIORITY` NEWS 값 변경, 새 `test_claims_source_role_priority_places_news_above_auxiliary_below_descriptive` 추가, seq 388 OFFICIAL / seq 391 DATABASE / seq 394 DESCRIPTIVE regression + 기존 conflict-separation 테스트가 assertion 변경 없이 그대로 통과함을 주장했으므로, 각 변경이 현재 tree와 일치하는지와 scope_limit(다른 role entry, `_claim_sort_key`, `merge_claim_records`, CONFLICT family, browser/docs 금지)을 넘지 않았는지 이번 verify에서 고정해야 다음 control 선택이 안전합니다.
- 선행 verify(`source-role-descriptive-priority-verification`)는 seq 394 DESCRIPTIVE elevation round 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `core/web_claims.py:32-42` `_ROLE_PRIORITY`가 이제 `{WIKI: 4, OFFICIAL: 5, DATABASE: 4, DESCRIPTIVE: 3, NEWS: 2, AUXILIARY: 1, COMMUNITY: 0, PORTAL: 0, BLOG: 0}`입니다. `NEWS`만 `1 → 2`로 바뀌었고 나머지 8개 entry는 값/순서 모두 seq 394 이후 상태 그대로 유지됩니다. 결과 ladder는 `OFFICIAL(5) > WIKI(4) = DATABASE(4) > DESCRIPTIVE(3) > NEWS(2) > AUXILIARY(1) > COMMUNITY(0) = PORTAL(0) = BLOG(0)`입니다.
  - `_claim_sort_key`의 tuple shape는 수정되지 않았습니다. `merge_claim_records`도 건드리지 않았습니다.
  - `tests/test_smoke.py:2248` `test_claims_source_role_priority_places_news_above_auxiliary_below_descriptive`가 추가됐습니다. 위치는 seq 394의 DESCRIPTIVE 회귀 바로 아래입니다. 테스트 이름이 `test_claims_...` prefix를 따르고 `coverage` 키워드를 포함하지 않아 `-k claims` 필터에만 걸리는 것이 의도와 일치합니다.
  - 기존 conflict-separation 테스트(`tests/test_smoke.py:2085-2145`), seq 388 OFFICIAL > WIKI 회귀(`:2147-`), seq 391 DATABASE tie 회귀(`:2179-`), seq 394 DESCRIPTIVE 회귀(`:2213-`)는 assertion 변경 없이 그대로 통과합니다. seq 394 회귀에서 NEWS는 ClaimRecord `source_role`로 쓰이지만 `DESCRIPTIVE(3) > NEWS(2)` 순서가 유지돼 DESCRIPTIVE-primary 기대가 그대로입니다.
  - 이번 라운드의 step 3 grep(`rg -n -C 4 "source_role=SourceRole\\.NEWS|source_role = SourceRole\\.NEWS|SourceRole\\.NEWS" tests/test_smoke.py`) 결과는 seq 394 DESCRIPTIVE regression과 이번 새 regression 외에 old `NEWS: 1` 위치에 기대는 다른 ClaimRecord-level smoke test가 없음을 보여 줍니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `core/contracts.py`, `core/agent_loop.py`, `storage/web_search_store.py`, `app/serializers.py`, `app/static/app.js`, `app/static/contracts.js`, `app/static/style.css`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, 그리고 모든 `docs/*.md`는 이번 라운드에서 수정되지 않았습니다.
  - CONFLICT family chain(label/rank/unresolved/probe + focus-slot CONFLICT 전용 wording + summary helpers + bar + panel hint + contracts.js + Playwright locks)은 seq 385까지의 상태, seq 388/391/394의 OFFICIAL/DATABASE/DESCRIPTIVE elevation과 함께 그대로 유지됩니다.
- focused rerun이 모두 통과했습니다.
  - `python3 -m unittest tests.test_smoke -k claims` → 이번 verify 독립 실행, `Ran 5 tests in 0.001s`, `OK`. seq 394의 4건에서 1건 늘어난 이유는 이번 라운드의 새 NEWS 회귀가 `claims` 키워드에 매칭되기 때문이고, handoff가 예측한 수치(`Ran 5 tests`)와 정확히 일치합니다.
  - `python3 -m unittest tests.test_smoke -k coverage` → 이번 verify 독립 실행, `Ran 14 tests in 0.108s`, `OK`. seq 394 verify의 14건과 동일합니다.
  - `python3 -m py_compile core/web_claims.py tests/test_smoke.py` → `/work`가 이미 실행, 출력 없음, exit `0`.
  - `git diff --check -- core/web_claims.py tests/test_smoke.py` → 이번 verify 독립 실행, 출력 없음, exit `0`.
- docs-sync ripple 검토
  - `/work`가 `rg -n "보조 기사.{0,20}보조 출처|NEWS.{0,20}AUXILIARY" docs README.md`로 NEWS-below-AUXILIARY 또는 NEWS-above-DESCRIPTIVE 명시 문장을 찾지 못했다고 기록했습니다. 이번 verify에서 동일 검색 가정을 뒤집어도 결과가 같습니다 — shipped docs는 NEWS와 AUXILIARY를 별도 trust-level 라벨(`보조 기사`, `보조 출처` 등)로 묘사할 뿐 수치 tie-break ladder를 못박는 문장이 보이지 않습니다.
- 같은 날 same-family docs-only round count는 seq 381의 1회 그대로입니다. seq 385 / seq 388 / seq 391 / seq 394 / 이번 seq 397 모두 code-only이므로 `3+ docs-only same-family` guard는 계속 멀리 있습니다. 다만 source-role weighting 내부에서는 이번이 5번째 연속 same-axis round이며, 현재 ladder에서 유일한 남은 tier tie는 COMMUNITY(0) = PORTAL(0) = BLOG(0)뿐이라는 점도 다음 슬라이스 선택 근거로 남겨 둡니다.

## 검증
- 직접 코드 대조
  - 대상: `core/web_claims.py:32-42`, `tests/test_smoke.py:2085-2145`, `:2147-`, `:2179-`, `:2213-`, `:2248-`.
  - 결과: `/work`가 설명한 2개 파일 변경이 현재 tree와 일치하고, `_claim_sort_key`/`merge_claim_records`/CONFLICT chain/OFFICIAL(seq 388)/DATABASE(seq 391)/DESCRIPTIVE(seq 394)/browser/docs는 실제로 untouched입니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 5 tests in 0.001s`, `OK`.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 14 tests in 0.108s`, `OK`.
- `git diff --check -- core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright 스위트: 이번 라운드는 Python source-role 단일 상수와 focused regression만 건드렸고 browser-visible copy/shared helper/fixture는 바뀌지 않았습니다. `.claude/rules/browser-e2e.md`의 "isolated Playwright rerun 우선" 기준 아래에서 생략이 truthful합니다.
  - 전체 `python3 -m unittest tests.test_web_app`: 이번 라운드는 `tests.test_web_app` 경로를 전혀 건드리지 않았고, 기존 실패 family(37 errors)는 선행 verify들에서 별도 dirty-state truth-sync 라운드 몫으로 분리돼 있습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared helper 변경도 없으므로 생략합니다.

## 남은 리스크
- Milestone 4 남은 sub-axis 후보는 여전히 pre-pinning이 필요합니다.
  - source-role weighting 남은 tier tie: COMMUNITY(0) = PORTAL(0) = BLOG(0). 세 역할의 의미가 충분히 구분되는지(portal는 허브, community는 사용자 포럼, blog는 개인 의견)에 대한 차별화가 필요한지, 아니면 세 가지 모두 "가장 낮은 권한"으로 동일 취급하는 것이 truthful한지는 판단이 필요합니다.
  - reinvestigation trigger threshold / probe retry count: `core/agent_loop.py` 또는 `core/web_claims.py` 안 구체 상수 하나를 고정해야 bounded slice가 됩니다.
  - strong-vs-weak-vs-unresolved separation beyond CONFLICT: `_claim_coverage_status_rank` tie-break tightening, entity-card strong-badge downgrade edge case, weak-vs-unresolved wording split 중 하나의 정확한 surface가 필요합니다.
  - response-body `[정보 상충]` tag emission: 새 behavior라 ripple이 크고, 이번 라운드와 무관합니다.
- 이 네 후보 중 어느 것도 file+surface+boundary pre-pinning 없이 다음 슬라이스로 고를 수 없고, source-role weighting 내부에서 5번째 연속 micro-slice가 되는지 여부도 Gemini 판단이 필요하므로, rule상 operator 전에 Gemini arbitration을 먼저 여는 편이 맞습니다.
- `docs/ACCEPTANCE_CRITERIA.md:45` 같은 trust-level label 설명 문장은 여전히 truthful 상태이며, shipped docs/README에서 NEWS priority ladder를 직접 기술한 문장은 없습니다. 즉시 docs sync는 필요하지 않습니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
