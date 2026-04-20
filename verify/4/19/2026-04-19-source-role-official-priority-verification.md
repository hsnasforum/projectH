# 2026-04-19 source-role official priority verification

## 변경 파일
- `verify/4/19/2026-04-19-source-role-official-priority-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-source-role-official-priority.md`)의 code 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`agent-loop-conflict-focus-slot-wording-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 388 (`Milestone 4 Source Role Weighting — OFFICIAL elevation above WIKI in _ROLE_PRIORITY`)는 Gemini advice 387이 지정한 exact 변경(`SourceRole.OFFICIAL` priority `3 → 5`)에 맞춰 `core/web_claims.py` 한 줄과 `tests/test_smoke.py` 기존 assertion flip + 새 focused regression을 묶는 code-only 슬라이스였습니다.
- 이번 `/work`가 `_ROLE_PRIORITY` OFFICIAL 값 변경, tied-support WIKI/OFFICIAL conflict 테스트 assertion flip, 새 OFFICIAL > WIKI regression 추가를 주장했으므로, 각 변경이 현재 tree와 일치하는지 + handoff scope_limit(다른 role entry, `_claim_sort_key`, `merge_claim_records`, CONFLICT family, browser/docs 금지)을 넘지 않았는지 이번 verify에서 고정해야 다음 control 선택이 안전합니다.
- 선행 verify(`agent-loop-conflict-focus-slot-wording-verification`)는 seq 385 CONFLICT wording round 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `core/web_claims.py:32-42` `_ROLE_PRIORITY`가 이제 `{WIKI: 4, OFFICIAL: 5, DATABASE: 3, DESCRIPTIVE: 2, NEWS: 1, AUXILIARY: 1, COMMUNITY: 0, PORTAL: 0, BLOG: 0}`입니다. `OFFICIAL` 값만 `3 → 5`로 바뀌었고, 나머지 8개 entry는 값과 순서가 모두 동일합니다.
  - `_claim_sort_key`의 tuple shape(`(support_count, _ROLE_PRIORITY.get(...), int(confidence*1000), len(value), value)`)는 수정되지 않았습니다. `merge_claim_records`도 건드리지 않았습니다.
  - `tests/test_smoke.py:2085-2145` conflict-separation 테스트가 primary-value assertion만 `"오픈월드 액션 어드벤처 게임"` → `"생존 제작 RPG"`로 뒤집고 inline comment를 "Primary selection follows the elevated OFFICIAL > WIKI tie-break in `_ROLE_PRIORITY` while the slot still reads `CONFLICT`."로 갱신했습니다. `status == CoverageStatus.CONFLICT`(line 2131), `candidate_count == 2`(line 2138), coverage_no_conflict == STRONG(line 2142-2145) assertion은 그대로 유지됩니다.
  - `tests/test_smoke.py:2147` `test_claims_summarize_slot_coverage_prefers_official_over_wiki_when_support_ties`가 추가돼 `_ROLE_PRIORITY[SourceRole.OFFICIAL] > _ROLE_PRIORITY[SourceRole.WIKI]`와 tied `support_count=1`에서 primary가 OFFICIAL-backed value/role로 결정되는지를 직접 pin합니다. 테스트 이름 prefix가 `test_claims_...`로 잡혀 `-k claims` 필터에도 정확히 걸립니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `core/contracts.py`, `core/agent_loop.py`, `storage/web_search_store.py`, `app/serializers.py`, `app/static/app.js`, `app/static/contracts.js`, `app/static/style.css`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, 그리고 모든 `docs/*.md`는 이번 라운드에서 수정되지 않았습니다.
  - CONFLICT family chain(label/rank/unresolved/probe + focus-slot CONFLICT 전용 wording + summary helpers + bar + panel hint + contracts.js)은 seq 385까지의 상태 그대로 유지됩니다.
- focused rerun이 모두 통과했습니다.
  - `python3 -m unittest tests.test_smoke -k claims` → 이번 verify 독립 실행, `Ran 2 tests in 0.000s`, `OK`.
  - `python3 -m unittest tests.test_smoke -k coverage` → 이번 verify 독립 실행, `Ran 14 tests in 0.085s`, `OK`. 이전 seq 385 verify의 13건에서 1건 늘어난 이유는 새 `test_claims_summarize_slot_coverage_prefers_official_over_wiki_when_support_ties`가 테스트명 안에 `coverage` 단어를 포함해 `-k coverage` 필터에도 매칭되기 때문입니다(새 테스트 로직이 coverage pipeline을 사용하므로 의도와도 맞습니다).
  - `python3 -m py_compile core/web_claims.py tests/test_smoke.py` → `/work`가 이미 실행, 출력 없음, exit `0`.
  - `git diff --check -- core/web_claims.py tests/test_smoke.py` → 이번 verify 독립 실행, 출력 없음, exit `0`.
- docs-sync ripple 검토
  - `/work`가 `rg -n "백과 기반.{0,20}공식 기반|WIKI.{0,20}OFFICIAL" docs README.md`로 OFFICIAL-below-WIKI 명시 문장을 찾지 못했다고 기록했습니다. 이번 verify에서 동일 검색 가정을 뒤집어도 결과가 같습니다 — shipped docs는 OFFICIAL과 WIKI를 별도 trust-level 라벨(`공식 기반 (신뢰도 높음)`, `백과 기반` 등)로 묘사할 뿐, tie-break 순서를 수치 계층으로 못박는 문장이 보이지 않습니다. 다만 `docs/ACCEPTANCE_CRITERIA.md:45` "source role with trust level (`공식 기반 (신뢰도 높음)`, `보조 커뮤니티 (신뢰도 낮음)`, etc.)" 같은 문장은 여전히 truthful 상태이므로 이번 라운드에서 수정 필요는 없습니다.
- 같은 날 same-family docs-only round count는 seq 381의 1회 그대로입니다. seq 385는 code-only, 이번 seq 388도 code-only이므로 `3+ docs-only same-family` guard는 계속 멀리 있습니다.

## 검증
- 직접 코드 대조
  - 대상: `core/web_claims.py:32-42`, `tests/test_smoke.py:2085-2145`, `tests/test_smoke.py:2147-`.
  - 결과: `/work`가 설명한 2개 파일 변경이 현재 tree와 일치하고, `_claim_sort_key`/`merge_claim_records`/CONFLICT chain/browser/docs는 실제로 untouched입니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 2 tests in 0.000s`, `OK`.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 14 tests in 0.085s`, `OK`.
- `git diff --check -- core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright 스위트: 이번 라운드는 Python source-role tie-break 상수 하나와 focused regression만 건드렸고 browser-visible copy/shared helper/fixture는 바뀌지 않았습니다. `.claude/rules/browser-e2e.md`의 "isolated Playwright rerun 우선" 기준 아래에서 생략이 truthful합니다.
  - 전체 `python3 -m unittest tests.test_web_app`: 이번 라운드는 `tests.test_web_app` 경로를 전혀 건드리지 않았고, 기존 실패 family(37 errors)는 선행 verify들에서 별도 dirty-state truth-sync 라운드 몫으로 분리돼 있습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared helper 변경도 없으므로 생략합니다.

## 남은 리스크
- Milestone 4 남은 sub-axis 후보는 여전히 pre-pinning이 필요합니다.
  - reinvestigation trigger threshold / probe retry count: `core/agent_loop.py` 또는 `core/web_claims.py` 안 구체 상수 하나를 고정해야 bounded slice가 됩니다.
  - strong-vs-weak-vs-unresolved separation beyond CONFLICT: `_claim_coverage_status_rank` tie-break tightening, entity-card strong-badge downgrade edge case, weak-vs-unresolved wording split 중 하나의 정확한 surface가 필요합니다.
  - source-role weighting 추가 조정: DATABASE vs OFFICIAL 간 관계, DESCRIPTIVE/NEWS/AUXILIARY 간 tie-break 등은 이번 라운드에서 건드리지 않았고 별도 슬라이스 후보입니다. 이번 OFFICIAL 단독 승격이 실제 사용자 시나리오에서 의도한 primary flip을 만들고 있는지에 대한 user-observable monitoring이 붙지 않았으므로, 추가 weighting 라운드 전에 Gemini가 다음 pair(예: OFFICIAL vs DATABASE, DATABASE vs WIKI)를 직접 고르는 편이 안전합니다.
  - response-body `[정보 상충]` tag emission: 새 behavior라 ripple이 크고, 이번 라운드와 무관합니다.
- `docs/ACCEPTANCE_CRITERIA.md:45` 같은 trust-level label 설명 문장은 여전히 truthful 상태입니다. 현재 shipped에서 OFFICIAL과 WIKI의 tie-break 수치 계층을 명시한 docs 문장은 보이지 않아 즉시 docs sync는 필요하지 않습니다. 다음 weighting 라운드가 docs에 "source role trust 계층" 개념을 새로 기술하면 그때 bounded docs sync를 같이 넣는 편이 좋습니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
- 다음 슬라이스는 위 네 후보 중 어느 것도 file+surface+boundary pre-pinning 없이 고를 수 없으므로, rule상 operator 전에 Gemini arbitration을 먼저 여는 편이 맞습니다.
