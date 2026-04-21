# 2026-04-20 role confidence G4

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- `_build_entity_claim_records`의 `role_confidence` map은 seq 420 `_ROLE_PRIORITY`와 어긋나 있었습니다. OFFICIAL은 최고 tier-5인데 `0.9`, WIKI는 tier-4인데 `0.95`, DATABASE는 explicit key가 없어 `0.4` fallback으로 떨어졌습니다.
- 이번 라운드는 server-only로 이 float-axis만 정렬해 `_claim_sort_key`의 tier-3 tiebreak가 OFFICIAL > WIKI == DATABASE hierarchy를 더 truthfully 따르도록 맞추는 것이 목적이었습니다.

## 핵심 변경
- `core/agent_loop.py:4103-4112`의 `_build_entity_claim_records` `role_confidence` map을 조정했습니다. OFFICIAL은 `:4104`에서 `0.95`, WIKI는 `:4105`에서 `0.9`, 새 DATABASE key는 `:4106`에서 `0.9`로 들어갔고, 나머지 key들과 `.get(source_role, 0.4)` fallback은 그대로 유지했습니다.
- 이번 변경은 `_ROLE_PRIORITY`의 rank-5 / rank-4 parity를 confidence에 맞춘 것입니다. 즉 OFFICIAL top, WIKI == DATABASE parity가 유지되어 `_claim_sort_key`의 third element `int(record.confidence * 1000)`가 role hierarchy와 더 일관되게 작동합니다.
- `trust_tier` derivation은 `confidence`를 보지 않습니다. seq 438의 trusted-role set `{OFFICIAL, DATABASE, WIKI}` 계약은 이번 라운드에서 수정하지 않았고, 이 slice는 confidence float만 정렬했습니다.
- 새 regression `test_build_entity_claim_records_role_confidence_aligns_with_role_priority_hierarchy`를 `tests/test_smoke.py:2600-2645`에 추가했습니다. `test_coverage_reinvestigation_overall_cap_is_now_5` 바로 뒤, `_build_entity_claim_records`를 가장 가깝게 쓰는 cluster 다음 위치에 두었고, OFFICIAL/WIKI/DATABASE의 `ClaimRecord.confidence`와 `OFFICIAL > WIKI == DATABASE` invariant를 함께 고정했습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453 shipped surface는 의도적으로 건드리지 않았습니다. `_entity_claim_sort_key`, `core/web_claims.py::_ROLE_PRIORITY`, claim coverage progress summary, serializer, client, Playwright, legend, `status_label` literal set은 모두 미편집입니다. G3 / G5 / G6 / G7 / G8 / G9도 계속 deferred 상태입니다.

## 검증
- `rg -n "SourceRole\\.(OFFICIAL|WIKI|DATABASE)" core/agent_loop.py`
  - 결과: 13건 hit
  - `4104-4106` 새 `role_confidence` map의 OFFICIAL/WIKI/DATABASE
  - `4133-4135`, `4645-4647` 기존 role_priority maps
  - `4268-4270` trusted-role set ordering
  - `3839`, `3850`, `3971` 기존 OFFICIAL branch
  - post-edit 기준 OFFICIAL=`0.9`나 WIKI=`0.95` 매핑은 남지 않았습니다.
- `rg -n "role_confidence" core/ tests/`
  - 결과: 3건 hit
  - `core/agent_loop.py:4103` map declaration
  - `core/agent_loop.py:4126` `confidence=role_confidence`
  - `tests/test_smoke.py:2600` 새 regression name
- `rg -n "0\\.4" core/agent_loop.py`
  - 결과: 3건 hit
  - `4109` `SourceRole.PORTAL: 0.45`
  - `4111` `SourceRole.AUXILIARY: 0.4`
  - `4112` `.get(source_role, 0.4)`
  - explicit `0.4` literal count는 변하지 않았습니다.
- `rg -n "SourceRole\\.COMMUNITY" core/agent_loop.py`
  - 결과: 2건 hit
  - `4139`, `4651` 기존 role_priority maps
  - `role_confidence` map에는 새 COMMUNITY key를 추가하지 않았습니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - 새 test name에는 `claims` substring이 없어 baseline 7이 유지됐습니다.
- `python3 -m unittest tests.test_smoke.SmokeTest.test_build_entity_claim_records_role_confidence_aligns_with_role_priority_hierarchy`
  - 결과: `Ran 1 test in 0.000s`, `OK`
  - 새 regression 자체를 직접 재실행해 green을 확인했습니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.099s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.029s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.129s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.089s`, `OK`
  - confidence float 조정만 있었고, seq 441 sanity는 그대로 green이었습니다.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- Playwright, `make e2e-test`, full `tests.test_web_app`는 이번 라운드가 server-only이고 client/shared browser helper를 수정하지 않아 실행하지 않았습니다.

## 남은 리스크
- COMMUNITY는 여전히 `role_confidence` map에 explicit key가 없고 `0.4` fallback으로 남습니다. `_ROLE_PRIORITY`가 COMMUNITY를 AUXILIARY와 같은 tier-1로 두고 있어 값은 우연히 맞지만, 현재는 implicit parity입니다. 이후 문서성/가독성 차원에서 explicit `COMMUNITY=0.4`를 검토할 수 있습니다.
- role_priority / confidence 정렬은 현재 snapshot에서는 맞지만, `role_confidence`가 `_ROLE_PRIORITY` ordering을 따라야 한다는 lint/property-style enforcement는 아직 없습니다. 후속 slice에서 invariant regression을 더 일반화할 수 있습니다.
- G3 threshold tuning, G5 / G6 red-test families, G7 vocabulary enforcement, G8 memory foundation, G9 naming-collision cleanup은 모두 다음 arbitration 후보로 남아 있습니다.
- unrelated full `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 라운드 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 계속 0입니다.
- dirty worktree의 다른 파일들은 이번 라운드에서 건드리지 않았습니다.
