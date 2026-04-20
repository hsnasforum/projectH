# 2026-04-19 focus slot weak missing wording verification

## 변경 파일
- `verify/4/19/2026-04-19-focus-slot-weak-missing-wording-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-focus-slot-weak-missing-wording.md`)의 code 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`remaining-conflict-docs-truth-sync-bundle-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 405 (`Milestone 4 Focus-Slot Unresolved WEAK/MISSING Explicit Wording — non-CONFLICT separation polish`)는 Gemini advice 404가 지정한 WEAK / MISSING 전용 Korean 템플릿으로 generic `"아직 {current_label} 상태입니다."` fallback을 대체하는 code-only 슬라이스였습니다.
- 이번 `/work`가 `_build_claim_coverage_progress_summary` focus-slot unresolved 분기의 WEAK/MISSING return path 변경 + `tests/test_smoke.py` target assertion 3개(target test + step 3 grep으로 발견한 `:2557`, `:3243-3245`) 수정을 주장했으므로, 각 변경이 현재 tree와 일치하는지와 scope_limit을 넘지 않았는지 이번 verify에서 고정해야 다음 control 선택이 안전합니다.
- 선행 verify(`remaining-conflict-docs-truth-sync-bundle-verification`)는 seq 402 docs-only final bundle 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `core/agent_loop.py:4465-4480` focus-slot unresolved iteration이 이제 세 explicit 분기를 가집니다:
    - `cur_status == CoverageStatus.CONFLICT` → `f"재조사했지만 {slot}{focus_particle} 출처들이 서로 어긋난 채 남아 있습니다."` (seq 385 템플릿 그대로)
    - `cur_status == CoverageStatus.WEAK` → `f"재조사했지만 {slot}{focus_particle} 아직 한 가지 출처의 정보로만 확인됩니다."` (new)
    - else (MISSING + unexpected fall-through) → `f"재조사했지만 {slot}{focus_particle} 아직 관련 정보를 찾지 못했습니다."` (new)
  - `current_label`은 `for slot, current_label, cur_status in unresolved_slots:`의 unpack에는 그대로 남아 있지만 WEAK/MISSING return path 안에서는 더 이상 interpolate되지 않습니다. 3-tuple shape는 handoff 지시대로 보존됐습니다.
  - `unresolved_slots.append((slot, self._claim_coverage_status_label(current_status), current_status))` shape, unresolved-bucket membership set `{CONFLICT, WEAK, MISSING}`, `improved_slots` / `regressed_slots` branch, `focus_particle = self._select_korean_particle(focus_slot, "은는")`, `_claim_coverage_status_rank`, `_claim_coverage_status_label`, `_build_entity_slot_probe_queries`, seq 400 `_build_entity_reinvestigation_suggestions::status_priority` / `max_queries_for_slot`는 이번 라운드에서 수정되지 않았습니다.
  - `tests/test_smoke.py`의 `test_build_claim_coverage_progress_summary_focus_slot_unresolved_wording_branches_by_status` WEAK assertion(`:2672`)과 MISSING assertion(`:2678`)이 새 explicit wording으로 flip됐습니다. CONFLICT assertion은 그대로입니다.
  - step 3 grep 결과 추가 발견: `test_load_web_search_record_legacy_claim_coverage_slots_reload_surface_and_follow_up_progress_canonicalized`의 `tests/test_smoke.py:2557`과 `test_entity_reinvestigation_query_reports_claim_progress`의 `tests/test_smoke.py:3243-3245`가 live focus-slot WEAK wording에 의존하고 있어 새 explicit wording으로 맞춰졌습니다. 이 두 조정은 1차 `-k coverage` 실행이 드러낸 failure를 해결하는 데 필요했고 truthful합니다.
  - grep에서 남은 old generic wording hit(`:2738`, `:2820`, `:2899`, `:3040`)은 stored `claim_coverage_progress_summary` fixture literal이라 live focus-slot 문장이 아니며 수정 대상이 아닙니다. 스토리지 기록은 legacy wording을 그대로 보존해 read-time canonicalization 시나리오를 검증합니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `core/contracts.py`, `core/web_claims.py`(seq 388/391/394/397 `_ROLE_PRIORITY` 포함), `storage/web_search_store.py`, `app/serializers.py`, `app/static/contracts.js`, `app/static/app.js`, `app/static/style.css`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, 그리고 모든 `docs/*.md`는 이번 라운드에서 수정되지 않았습니다.
- `docs/PRODUCT_SPEC.md:369`와 `docs/ACCEPTANCE_CRITERIA.md:35`에는 여전히 `재조사했지만 ... 아직 단일 출처 상태입니다` 예시가 남아 있습니다. 두 문장 모두 `legacy stored claim_coverage_progress_summary normalization`을 설명하는 clause 안에서 legacy record canonicalization 예시로 쓰인 것으로, 이번 라운드에서 쓰기 시 새 wording이 저장되더라도 기존 legacy 기록을 canonicalize하는 맥락의 예시로 읽으면 여전히 유효합니다. 따라서 이번 라운드 기준 즉시 docs 수정 필요는 아니며, 시간이 지나 legacy 기록 비중이 줄어들 때 재검토하는 편이 truthful합니다.
- 같은 날 same-family docs-only round count는 seq 381 + seq 401 + seq 402로 3에 있습니다. 이번 seq 405는 code-only이므로 docs-only count는 그대로 3으로 유지됩니다. 다음 슬라이스가 pure docs-only 라운드면 `3+ docs-only same-family` guard를 넘기 때문에, code 라운드 또는 code+docs mixed 라운드로만 갈 수 있습니다.

## 검증
- 직접 코드 대조
  - 대상: `core/agent_loop.py:4465-4480`, `tests/test_smoke.py:2557`, `:2672`, `:2678`, `:3243-3245`, 참고용으로 `:2738`, `:2820`, `:2899`, `:3040`(stored fixture literal).
  - 결과: `/work`가 설명한 branch/assertion 변경이 현재 tree와 일치하고, CONFLICT template / rank / label / probe / role priority / browser / docs가 실제로 untouched입니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: 이번 verify 독립 실행, `Ran 16 tests in 0.087s`, `OK`. seq 400 verify의 16건과 동일 수이며 이번 assertion flip 후에도 pass 유지.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: 이번 verify 독립 실행, `Ran 5 tests in 0.001s`, `OK`. seq 397 이후 claims 수 5건 변화 없음.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright: 이번 라운드는 server-emitted Korean 문장 두 분기만 바뀌었고 browser-visible copy/shared helper/fixture는 변경되지 않았습니다. `.claude/rules/browser-e2e.md`의 "isolated Playwright rerun 우선" 기준 아래에서 생략이 truthful.
  - 전체 `python3 -m unittest tests.test_web_app`: 이번 라운드는 `tests.test_web_app` 경로를 전혀 건드리지 않았고, 기존 실패 family(37 errors)는 선행 verify들에서 별도 dirty-state truth-sync 라운드 몫으로 분리돼 있습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared helper 변경도 없으므로 생략합니다.

## 남은 리스크
- Milestone 4 남은 sub-axis 후보는 여전히 pre-pinning이 필요합니다.
  - source-role weighting 남은 tier tie: COMMUNITY(0) = PORTAL(0) = BLOG(0). 이 세 tier를 더 쪼갤지, 아니면 weighting axis를 완전히 닫을지 판단 필요.
  - reinvestigation trigger threshold / probe retry tuning 추가 상수: `_build_entity_slot_probe_queries` probe list size, `max_queries_for_slot` upper limit, `prefer_probe_first` 조건 tightening 등 중 어느 것을 고를지 pinning 필요.
  - response-body `[정보 상충]` tag emission: user-visible ripple이 크고 docs/tests/Playwright 조정을 동반하는 별도 설계 판단 필요.
  - strong-vs-weak-vs-unresolved separation further polish: entity-card strong-badge downgrade edge case, STRONG-tied-with-STRONG tie-break 등 남은 polish surface 선정 필요.
- docs-only round count가 이미 3에 도달했으므로 다음 라운드는 pure docs-only가 될 수 없습니다. code 라운드 또는 code+docs mixed 라운드로만 진행 가능.
- `docs/PRODUCT_SPEC.md:369`와 `docs/ACCEPTANCE_CRITERIA.md:35`의 legacy stored-progress example은 현재 해석으로 truthful하나, 장래에 legacy 기록 비중이 충분히 감소하면 예시를 갱신할 필요가 생길 수 있습니다. 이번 라운드의 즉시 docs-sync 대상은 아닙니다.
- 이 네 후보 중 어느 것도 file+surface+boundary pre-pinning 없이 다음 슬라이스로 고를 수 없으므로, rule상 operator 전에 Gemini arbitration을 먼저 여는 편이 맞습니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
