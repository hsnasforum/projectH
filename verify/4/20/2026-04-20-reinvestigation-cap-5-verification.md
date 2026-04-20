# 2026-04-20 reinvestigation cap 5 verification

## 변경 파일
- `verify/4/20/2026-04-20-reinvestigation-cap-5-verification.md`

## 사용 skill
- `round-handoff`: seq 423 `/work`(`work/4/20/2026-04-20-reinvestigation-cap-5.md`)의 Milestone 4 reinvestigation overall cap 4 → 5 변경 주장을 `core/agent_loop.py` 실제 상태와 `tests/test_smoke.py` 새 회귀로 교차 확인하고, handoff가 요구한 narrowest 재검증만 실행해 truthful 여부를 확정했습니다. 동시에 seq 424 `.pipeline/operator_request.md` dispatcher-state stop이 seq 423 shipping으로 자연 해제되었음을 기록했습니다.

## 변경 이유
- seq 423 `.pipeline/claude_handoff.md`(Gemini 422 Option D 기반)가 구현되어 새 `/work` 노트가 제출되었습니다. 이 라운드의 목표는 `_build_entity_second_pass_queries` 내부 overall cap 한 줄을 `>= 4` → `>= 5`로 넓혀 `CORE_ENTITY_SLOTS`(5 slots)와 parity를 맞추고, 각 slot이 1개 probe query만 내는 최악 케이스에서 마지막 slot이 silent drop되지 않도록 고정하는 것이었습니다.
- 동시에 직전 late-verify 라운드가 남긴 `.pipeline/operator_request.md` seq 424(`dispatcher_state_truth_sync`)는 seq 423 implement 슬라이스를 preserve할지 여부를 물었는데, Codex가 seq 423을 정상 진행·완료한 시점에서 사실상 `PRESERVE_SEQ_423` 선택이 이벤트로 확정되어 stop은 self-heal된 상태입니다.

## 핵심 변경
- `core/agent_loop.py:3863` 이 이제 `if len(second_pass_queries) >= 5:` 입니다. 직전 위치·들여쓰기(12 spaces)·break·주변 루프(`for variant in ordered_variants:`, `max_queries_for_slot`, `prefer_probe_first`, `:3775-3780` early-return, `:3782-3788` `slot_priority`)는 변경되지 않았습니다. 문자 수준으로는 `4` → `5` 한 글자만 바뀌어 handoff 지시와 일치합니다.
- `tests/test_smoke.py:2418-2439` 에 `test_coverage_reinvestigation_overall_cap_is_now_5` 가 정확히 삽입되었습니다. 위치는 `test_coverage_reinvestigation_second_pass_conflict_slot_uses_weak_like_probe_boost_rules`(`:2316-2416`) 직후, `test_summarize_slot_coverage_untrusted_only_agreement_stays_weak`(이전 `:2418` → 삽입 후 `:2440` 부근)의 직전 위치로, handoff의 pin 경로와 동일합니다.
- 새 회귀는 monkeypatch 4종(`_build_entity_claim_confirmation_queries`, `_build_entity_slot_probe_queries`, `_build_entity_claim_records`, `_entity_slot_from_search_query`)으로 5 슬롯 전부를 MISSING 상태로 유지한 뒤, `queries = loop._build_entity_second_pass_queries(...)` 호출 결과에 대해 `len(queries) == 5`, `len(set(queries)) == 5`, `CORE_ENTITY_SLOTS` 각 slot 문자열이 최소 1개 query에 포함되는지 고정합니다. 쿼리 순서는 assert하지 않아 `slot_priority` 정렬을 scope 밖에 두는 handoff 지시를 지킵니다.
- `max_queries_for_slot` per-slot boost(`:3847-3852`)와 early-return(`:3775-3780`)은 의도적으로 미수정. seq 400 per-slot invariant와 "대부분 STRONG이면 second pass 생략" 경계는 그대로 유지됩니다.
- handoff가 금지한 surface는 보존됐습니다: seq 385/400/405 focus-slot 템플릿, seq 408 5-tuple + response-body header, seq 411 source-line + role_priority sync, seq 414 `_build_entity_claim_coverage_items` + `formatClaimRenderedAs` conflict 분기, seq 417 Playwright CONFLICT end-to-end 시나리오, seq 420 `_ROLE_PRIORITY` positions. `core/web_claims.py`, `app/`, `storage/`, `e2e/`, docs, agent-config 파일은 이번 라운드에서 수정되지 않았습니다.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `423` — 이미 shipped 됐고 새로운 `/work`로 consumed.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `421` — seq 422 advice로 이미 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `422` — seq 423 handoff로 이미 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — dispatcher-state 질문이 seq 423 shipping으로 이벤트 자연 해제. 남은 blocker 없음.

## 검증
- 직접 코드/테스트 대조
  - `core/agent_loop.py:3863` 의 `if len(second_pass_queries) >= 5:` 현재 상태 확인.
  - `tests/test_smoke.py:2418-2439` 의 `test_coverage_reinvestigation_overall_cap_is_now_5` 구조 확인 (4개 monkeypatch + 3 assert + slot 루프 assert).
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.082s`, `OK`. 기존 5 + 신규 1. `test_coverage_reinvestigation_second_pass_conflict_slot_uses_weak_like_probe_boost_rules` 등 기존 per-slot 회귀 모두 유지.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 20 tests in 0.102s`, `OK`. handoff 기대치는 19였지만 현재 작업 트리에서 실제 coverage family는 20건 매칭. 이번 라운드는 coverage family 테스트를 추가하지 않았습니다(`/work` 메모와 일치).
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- Playwright, `tests.test_web_app`, `make e2e-test` 는 이번 verify 에서 돌리지 않았습니다. 이번 slice 는 integer cap + smoke regression 만 바꿔 browser-visible contract / shared helper / selector 를 건드리지 않았고, 동일 축의 `-k claims`(6), `-k coverage`(20) 도 OK 로 확인했습니다.

## 남은 리스크
- Milestone 4 남은 후보 E(strong-vs-weak-vs-unresolved further polish — STRONG-tied-with-STRONG tie-break, entity-card strong-badge downgrade edge, 비-CONFLICT 전이 wording polish 중 하나)는 여전히 별도 라운드 몫입니다. D 가 소비되었으므로 E 가 사실상 유일한 남은 후보이지만, 정확한 file + `:line` + symbol + surface + numeric/textual 경계가 단독으로 pinned 되어 있지 않아 slice_ambiguity 성격입니다.
- `prefer_probe_first` threshold(`core/agent_loop.py:3836-3840`), probe list size(`_build_entity_slot_probe_queries` output), `_role_confidence_score` float axis 는 overall cap 과 별개로 남아 있으며 별도 tuning round 후보입니다.
- `docs/NEXT_STEPS.md:23` 의 general reinvestigation 설명은 literal 4-query cap 문장이 아니고 현재 동작과 직접 충돌하지 않아 이번 라운드에서 docs 는 수정하지 않았습니다. 오늘(2026-04-20) docs-only round count 는 계속 0.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family, `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` 실패는 이번 slice 밖이며 별도 truth-sync 라운드 몫입니다.
- seq 424 `.pipeline/operator_request.md`(dispatcher_state_truth_sync)는 seq 423 shipping 으로 자연 해제되었습니다. 다음 control 은 slice_ambiguity 조건(E 의 exact pin 필요)이라 `.pipeline/gemini_request.md`(seq 425) 로 arbitration 을 먼저 여는 편이 rule 에 맞고, operator_request 는 더 이상 real operator-only decision / approval blocker / 안전 정지 / Gemini 부재 중 어느 조건에도 해당하지 않습니다.
