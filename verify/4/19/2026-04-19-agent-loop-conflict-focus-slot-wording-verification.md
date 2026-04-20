# 2026-04-19 agent-loop conflict focus-slot wording verification

## 변경 파일
- `verify/4/19/2026-04-19-agent-loop-conflict-focus-slot-wording-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-agent-loop-conflict-focus-slot-wording.md`)의 code 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`claim-coverage-panel-hint-conflict-explanation-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 385 (`Agent Loop CONFLICT-Specific Focus-Slot Wording — fixed template polish`)는 Gemini advice 384가 지정한 정확한 Korean 템플릿(`"재조사했지만 {slot}{focus_particle} 출처들이 서로 어긋난 채 남아 있습니다."`)을 `_build_claim_coverage_progress_summary` focus-slot unresolved branch에만 넣고, rank/label/probe/improved/regressed/browser/docs는 건드리지 않는 code-only 슬라이스였습니다.
- 이번 `/work`가 `core/agent_loop.py` + `tests/test_smoke.py` 두 파일의 scoped 변경과 3개 포커스드 regression 통과를 주장했으므로, 각 변경이 현재 tree와 일치하는지와 scope_limit를 넘지 않았는지 이번 verify에서 고정해야 다음 control 선택이 안전합니다.
- 선행 verify(`claim-coverage-panel-hint-conflict-explanation-verification`)는 seq 382 code+docs mixed 라운드 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `core/agent_loop.py:4415-4422`에서 unresolved-bucket append가 `(slot, self._claim_coverage_status_label(current_status), current_status)` 3-tuple을 담습니다. 상위 `if current_status in {CoverageStatus.CONFLICT, CoverageStatus.WEAK, CoverageStatus.MISSING}:` 가드는 그대로 유지됩니다.
  - `core/agent_loop.py:4460-4467` focus-slot unresolved iteration이 `for slot, current_label, cur_status in unresolved_slots:`로 3-tuple을 unpack하고, `if slot == focus_slot:` 안에서 `if cur_status == CoverageStatus.CONFLICT:`면 `f"재조사했지만 {slot}{focus_particle} 출처들이 서로 어긋난 채 남아 있습니다."`를 반환하고, 아니면 기존 `f"재조사했지만 {slot}{focus_particle} 아직 {current_label} 상태입니다."`를 그대로 반환합니다.
  - `focus_particle = self._select_korean_particle(focus_slot, "은는")` 로직은 기존 위치에서 재사용됩니다. `select_korean_directional_particle` 등 다른 particle helper는 새 CONFLICT 문장에서 사용되지 않으며, 이는 새 템플릿이 `{directional}` 토큰을 포함하지 않는 Gemini 384 고정 문장과 정합합니다.
  - `core/agent_loop.py:4424-4442` `improved_slots` 분기와 `:4443-4459` `regressed_slots` 분기는 수정되지 않았습니다. `_claim_coverage_status_rank`, `_claim_coverage_status_label`, `_build_entity_slot_probe_queries`도 그대로입니다.
  - `tests/test_smoke.py:2375` `test_build_claim_coverage_progress_summary_focus_slot_conflict_stays_unresolved`는 기존에 기대하던 `"정보 상충 상태"` 문장 대신 새 CONFLICT 템플릿 문장을 exact match로 검사하도록 갱신됐고, `tests/test_smoke.py:2402` `test_build_claim_coverage_progress_summary_focus_slot_unresolved_wording_branches_by_status`가 추가돼 CONFLICT/WEAK/MISSING 각 focus-slot 상태의 정확한 문구 3개를 한 테스트에서 잠급니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `core/contracts.py`, `core/web_claims.py`, `storage/web_search_store.py`, `app/serializers.py`, `app/static/app.js`, `app/static/contracts.js`, `app/static/style.css`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, 그리고 모든 `docs/*.md`는 이번 라운드에서 수정되지 않았습니다.
  - response-body section header emission(`[교차 확인]` / `[단일 출처]` / `[미확인]`)은 변경되지 않았고, `docs/ACCEPTANCE_CRITERIA.md:49`의 "does not emit a dedicated `[정보 상충]` response-body header tag" 주장은 그대로 truthful합니다.
- 이번 라운드로 CONFLICT same-family chain은 서버 emit 문장까지 포함해 모든 observable surface에서 정합한 상태입니다.
  - contract: `core/contracts.py` CoverageStatus.CONFLICT, `app/static/contracts.js` CoverageStatus.CONFLICT
  - server aggregation: `core/web_claims.py` conflict emission, `core/agent_loop.py` label/rank/unresolved/probe + focus-slot CONFLICT-specific wording (새 템플릿)
  - storage: `storage/web_search_store.py::_summarize_claim_coverage` 4-key
  - serializer: `app/serializers.py:282-287` 4-key `claim_coverage_summary`
  - browser history-card summary: `formatClaimCoverageCountSummary` 4-segment
  - browser in-answer bar: `renderFactStrengthBar` 4-badge + `.fact-count.conflict` CSS
  - browser live-session summary: `formatClaimCoverageSummary → summarizeClaimCoverageCounts`
  - browser panel hint: `renderPanelHint(...)` 4-tag 설명
  - 문서: `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md:35/48/49/1375`, `docs/TASK_BACKLOG.md:25`, `docs/MILESTONES.md:51/52/151`
  - Playwright locks: history-card CONFLICT summary(seq 376), in-answer bar CONFLICT badge(seq 377), live-session answer meta CONFLICT summary(seq 378), panel hint 4-tag(seq 382)
  - 서버-방출 focus-slot 문구: CONFLICT 전용 템플릿(seq 385)
- focused rerun이 모두 통과했습니다.
  - `python3 -m unittest tests.test_smoke -k coverage` → 이번 verify에서 독립 실행, `Ran 13 tests in 0.053s`, `OK`.
  - `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` → `/work`가 이미 실행, 출력 없음, exit `0`.
  - `git diff --check -- core/agent_loop.py tests/test_smoke.py` → 이번 verify에서 독립 실행, 출력 없음, exit `0`.
- 같은 날 same-family docs-only round count는 seq 381의 1회 그대로입니다. seq 382는 code+docs mixed, 이번 seq 385는 code-only이므로 `3+ docs-only same-family` guard는 계속 멀리 있습니다.

## 검증
- 직접 코드 대조
  - 대상: `core/agent_loop.py:4414-4467`, `tests/test_smoke.py:2375`와 `:2402`.
  - 결과: `/work`가 설명한 2개 파일 변경이 현재 tree와 일치하고, improved/regressed/rank/label/probe 그리고 browser/docs surface는 실제로 untouched입니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 13 tests in 0.053s`, `OK`.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright 스위트: 이번 라운드는 서버가 만드는 Korean 문장 한 branch만 바뀌었고, browser helper/fixture/renderer contract 변경이 없습니다. `.claude/rules/browser-e2e.md`의 "narrowest relevant" 기준으로 Playwright 재실행은 불필요했습니다.
  - 전체 `python3 -m unittest tests.test_web_app`: 이번 라운드는 Python 경로 중 `core/agent_loop.py`와 `tests/test_smoke.py`만 건드렸고, `tests.test_web_app`의 기존 실패 family는 선행 verify들에서 이미 별도 dirty-state truth-sync 라운드 몫으로 분리돼 있습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared helper 변경도 없으므로 생략합니다.

## 남은 리스크
- CONFLICT same-family current-risk는 이번 라운드까지로 서버 emit 문장까지 포함해 observable 모든 surface에서 truthfully 닫혔습니다. 같은 family 안에서 다음으로 실행할 bounded slice는 더 이상 보이지 않습니다.
- Milestone 4 남은 sub-axis 후보는 모두 pre-pinning이 필요한 상태로 남습니다.
  - `source role labeling/weighting`: role weighting threshold, trust-level class, role-detail 포맷 중 어느 한 파일/한 표면을 고정해야 bounded slice가 됩니다.
  - reinvestigation trigger threshold / probe retry: `core/agent_loop.py` 혹은 `core/web_claims.py` 안의 구체 상수 하나를 고정해야 합니다.
  - `strong vs weak vs unresolved separation beyond CONFLICT`: strong-badge downgrade 조건, weak-vs-unresolved wording 등 구체 surface가 필요합니다.
  - response-body `[정보 상충]` header tag emission: 새 behavior라 docs line 49 / agent_loop emission / test 파장 때문에 bounded mini-slice라기보다 별도 설계가 필요합니다.
- 이 네 후보 중 어느 것을 다음 슬라이스로 고를지는 Gemini 380 / Gemini 384 판단 기준으로도 pre-pinning이 필요했습니다. 따라서 다음 control slot은 Gemini arbitration으로 여는 편이 rule에 맞습니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
