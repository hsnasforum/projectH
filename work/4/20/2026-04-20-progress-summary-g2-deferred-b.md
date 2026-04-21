# 2026-04-20 progress summary G2 deferred B

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- seq 447은 focus improved→STRONG mixed-trust 문구를, seq 450은 non-focus STRONG mixed-trust surfacing을 닫았지만, focus slot이 steady STRONG이면서 `trust_tier == "mixed"`인 경우는 progress summary가 계속 silent였습니다.
- 이번 라운드는 `_build_claim_coverage_progress_summary` 안에 focus-slot 전용 분기 하나만 추가해 같은 family의 남은 user-visible gap을 server-only로 닫는 것이 목적이었습니다.

## 핵심 변경
- `core/agent_loop.py:4585-4592`에 focus-slot steady STRONG mixed-trust 전용 분기 1개를 추가했습니다. unresolved focus loop의 final MISSING return(`:4581-4584`) 바로 뒤이자 non-focus `if improved_slots:` fallback(`:4594`) 바로 앞이며, 들여쓰기는 `if focus_slot:` 내부의 기존 focus loops와 같은 한 단계입니다.
- 새 분기는 `current_map.get(focus_slot, "") == CoverageStatus.STRONG` 및 `current_trust_tier_map.get(focus_slot, "") == "mixed"`일 때만 `"재조사했지만 {focus_slot}{focus_particle} 교차 확인 기준은 충족하지만 공식/위키/데이터 소스가 약합니다."`를 반환합니다. `focus_particle`은 기존 `if focus_slot:` 블록에서 계산된 값을 그대로 재사용했습니다.
- 새 regression `test_build_claim_coverage_progress_summary_focus_slot_steady_strong_mixed_trust_emits_mixed_trust_wording`를 `tests/test_smoke.py:3355-3384`에 추가했고, seq 450 regression `test_build_claim_coverage_progress_summary_surfaces_non_focus_strong_mixed_trust_via_combined_summary`(`:3322-3353`) 바로 다음에 배치했습니다. query `"붉은사막 개발 상황 알려줘"`가 `개발` focus slot으로 매핑되고, previous/current가 모두 `CoverageStatus.STRONG`일 때 mixed-trust 문구가 정확히 반환되는지 고정했습니다.
- 새 regression은 exact sentence equality와 함께 `"아직"`이 결과에 포함되지 않는지도 확인해, pre-slice non-focus fallback이 아니라 새 focus branch가 실제로 먼저 반환됐음을 검증합니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450에서 이미 ship된 helper, serializer, client, Playwright, legend, `status_label` literal set은 이번 라운드에서 의도적으로 수정하지 않았습니다. G3 / G4 / G5 / G6 / G7 / G8 / G9도 그대로 deferred 상태입니다.

## 검증
- `rg -n "교차 확인 기준은 충족하지만 공식/위키/데이터 소스가 약합니다" core/ tests/`
  - 결과: 2건 hit
  - `core/agent_loop.py:4591`
  - `tests/test_smoke.py:3382`
- `rg -n "current_map.get\\(focus_slot" core/agent_loop.py`
  - 결과: 1건 hit
  - `core/agent_loop.py:4586`
- `rg -n "_entity_slot_from_probe_text" core/agent_loop.py`
  - 결과: 5건 hit
  - `3920` helper definition, `3941`/`4324`/`4405` 기존 call site, `4457` `_build_claim_coverage_progress_summary` 내부 call site
  - 이번 slice로 hit 수가 늘어나지 않았고, helper 자체는 read-only였습니다.
- `rg -n "if focus_slot:" core/agent_loop.py`
  - 결과: 1건 hit
  - `core/agent_loop.py:4517`
  - redundant `if focus_slot:` wrapper는 추가하지 않았습니다.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.017s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.059s`, `OK`
  - 새 test name에 `claim_coverage_progress_summary`가 포함되어 count가 26 → 27로 늘었습니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.063s`, `OK`
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.053s`, `OK`
  - seq 441 sanity는 계속 green이었고, partial-match assertion도 깨지지 않았습니다.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `node --check app/static/app.js`, Playwright, `make e2e-test`, full `tests.test_web_app`는 이번 라운드가 server-only이고 client/shared browser helper를 수정하지 않아 실행하지 않았습니다.

## 남은 리스크
- G2-deferred-B가 닫히면서 server summary의 mixed-trust 3개 표면(focus improved→STRONG, focus steady STRONG, non-focus STRONG)은 모두 커버됩니다. 현재 indicator set 기준 `progress_summary` mixed-trust matrix는 complete 상태입니다.
- 다음 후보인 G3 / G4 / G5 / G6 / G7 / G8 / G9는 모두 열려 있습니다. 이 중 G5 / G6는 이번 slice가 건드리지 않은 red test family를 계속 추적합니다.
- unrelated full `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 라운드 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 계속 0입니다.
- dirty worktree의 다른 파일들은 이번 라운드에서 건드리지 않았습니다.
