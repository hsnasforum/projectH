# 2026-04-20 reinvestigation cap 5

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 grep, `tests.test_smoke` family rerun, `py_compile`, `git diff --check`만 실제 실행 기준으로 정리했습니다.
- work-log-closeout: `work/4/20/` 아래에 표준 섹션 순서로 이번 bounded slice의 변경/검증/남은 리스크만 기록했습니다.

## 변경 이유
- `CORE_ENTITY_SLOTS`는 5개인데 `_build_entity_second_pass_queries`의 overall cap이 `4`라서, 모든 core slot이 pending(MISSING/WEAK/CONFLICT)이고 각 slot이 1개 probe query만 내는 최악의 경우 마지막 slot 하나가 조용히 재조사에서 탈락하고 있었습니다.
- 이번 라운드는 Milestone 4 reinvestigation threshold의 정확한 숫자 슬라이스로, per-slot 규칙은 그대로 둔 채 overall cap만 `4 -> 5`로 넓혀 5개 core slot 전부가 최소 1회는 second-pass query를 받도록 맞추는 것이 목적이었습니다.

## 핵심 변경
- `core/agent_loop.py:3863`는 이제 `_build_entity_second_pass_queries` 안에서 `if len(second_pass_queries) >= 5:`를 사용합니다. 이전 `>= 4`에서 숫자 한 글자만 바뀌었고, 함수 본문의 다른 줄은 손대지 않았습니다.
- 이 변경으로 `CORE_ENTITY_SLOTS`(개발 / 서비스/배급 / 장르/성격 / 상태 / 이용 형태) 5개가 모두 pending이고 각 slot이 1개 probe query만 낼 때도 5개 slot 전부가 second-pass 대상이 됩니다. 이전에는 5번째 slot이 overall cap 때문에 잘렸습니다.
- `core/agent_loop.py:3847-3852`의 `max_queries_for_slot` per-slot boost와 `core/agent_loop.py:3775-3780` early-return은 의도적으로 수정하지 않았습니다. seq 400이 고정한 per-slot 규칙과 “대부분 STRONG이면 second pass 자체를 생략”하는 경계는 그대로 유지됩니다.
- `tests/test_smoke.py:2418-2439`에 `test_coverage_reinvestigation_overall_cap_is_now_5`를 추가했습니다. 위치는 `test_coverage_reinvestigation_second_pass_conflict_slot_uses_weak_like_probe_boost_rules` 바로 뒤, `test_summarize_slot_coverage_untrusted_only_agreement_stays_weak` 바로 앞입니다.
- 새 회귀는 `_build_entity_claim_confirmation_queries -> []`, `_build_entity_slot_probe_queries -> [f"붉은사막 {slot} 탐침"]`, `_build_entity_claim_records -> []`, `_entity_slot_from_search_query -> ""`로 monkeypatch 한 뒤 `queries = loop._build_entity_second_pass_queries(...)`를 호출하고, `len(queries) == 5`, `len(set(queries)) == 5`, `CORE_ENTITY_SLOTS`의 각 slot이 최소 1개 query에 포함되는지를 고정합니다.
- step 6 grep 결과, code/test 쪽에는 old cap `4`를 invariant로 고정한 다른 assertion은 없었습니다. docs grep은 `docs/NEXT_STEPS.md:23`의 general reinvestigation 설명만 찾았고, literal 4-query cap 문장은 없어서 이번 라운드에서 docs는 수정하지 않았습니다.
- seq 408/411/414/417 CONFLICT chain surface와 seq 420 `_ROLE_PRIORITY` positions는 의도적으로 건드리지 않았습니다.

## 검증
- `rg -n 'second_pass_queries|second-pass-queries|>= 4|cap.*=\s*4|>= 5' core/agent_loop.py tests/test_smoke.py`
  - 결과: `_build_entity_second_pass_queries` 본문과 관련 테스트 호출 지점만 확인됐고, old cap `4`를 별도 invariant로 고정한 assertion은 보이지 않았습니다.
- `rg -n 'second_pass_queries|재조사.*쿼리|reinvestigation.*cap|reinvestigation.*4' docs/`
  - 결과: `docs/NEXT_STEPS.md:23`의 general reinvestigation 설명 1건만 hit 했고, literal 4-query cap 문장은 없었습니다.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.078s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 6 tests in 0.002s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 20 tests in 0.072s`, `OK`
  - 메모: handoff의 예상치는 19였지만, 현재 작업 트리에서 실제 실행된 coverage family는 20건이었습니다. 이번 slice는 coverage-family 테스트를 추가하지 않았습니다.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- Playwright, `python3 -m unittest tests.test_web_app`, `make e2e-test`는 실행하지 않았습니다. 이번 slice는 browser-visible copy나 selector가 아니라 reinvestigation overall cap 한 줄과 smoke regression 1건만 바꿨습니다.

## 남은 리스크
- Milestone 4 남은 후보 E(strong-vs-weak-vs-unresolved further polish)는 이후 라운드 후보로 남아 있습니다.
- step 6 grep에서 literal 4-query cap을 적은 docs 문장은 찾지 못했습니다. `docs/NEXT_STEPS.md:23`의 general reinvestigation 설명은 현재 동작과 직접 충돌하지 않아 그대로 두었고, 오늘(2026-04-20) docs-only round count도 계속 0입니다.
- `prefer_probe_first` threshold(`core/agent_loop.py:3836-3840`), probe list size(`_build_entity_slot_probe_queries` output), `_role_confidence_score` float axis는 overall cap과 별개인 tuning 후보로 남아 있습니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 밖에 그대로 남아 있습니다.
