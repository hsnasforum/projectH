# 2026-04-19 reinvestigation conflict suggestions probe cap

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 `tests.test_smoke` 중심 검증과 tests/docs grep만 다시 실행하고, Playwright/`tests.test_web_app`를 왜 생략했는지 범위 기준으로 정리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 라운드의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- `_build_entity_reinvestigation_suggestions`의 `status_priority`는 `MISSING`/`WEAK`만 다뤄서 CONFLICT slot이 entity-card 재조사 suggestion에서 조용히 탈락하고 있었습니다.
- `_build_entity_second_pass_queries`의 `max_queries_for_slot`은 WEAK만 2-query boost를 받아, trusted sources가 서로 충돌하는 CONFLICT slot도 재조사 2차 쿼리가 1개로 제한되고 있었습니다.
- 이번 슬라이스 목표는 handoff 그대로 CONFLICT를 suggestion eligibility와 second-pass query cap 양쪽에만 포함시키는 것이었고, probe guard/CONFLICT wording/source-role weighting/browser/docs는 건드리지 않는 것이었습니다.

## 핵심 변경
- `core/agent_loop.py::_build_entity_reinvestigation_suggestions`의 `status_priority`는 이제 `CoverageStatus.MISSING: 0`, `CoverageStatus.WEAK: 1`, `CoverageStatus.CONFLICT: 2`를 가집니다. downstream sort, gate, candidate tuple shape, emission pipeline은 그대로 유지했습니다.
- `core/agent_loop.py::_build_entity_second_pass_queries`의 `max_queries_for_slot`은 이제 `slot_coverage.status in {CoverageStatus.WEAK, CoverageStatus.CONFLICT}`일 때 `prior_probe_count >= 1 or source_role != SourceRole.OFFICIAL` boost 조건을 동일하게 씁니다. `prefer_probe_first`, `seen_queries`, `ordered_variants`, overall `len(second_pass_queries) >= 4` cap은 그대로 두었습니다.
- `tests/test_smoke.py`에 `test_coverage_reinvestigation_suggestions_include_conflict_slot_when_only_conflict_is_pending`와 `test_coverage_reinvestigation_second_pass_conflict_slot_uses_weak_like_probe_boost_rules`를 추가했습니다. 둘 다 `coverage` 필터에 걸리도록 reinvestigation cluster 바로 뒤에 넣었고, 첫 테스트는 CONFLICT-only fixture에서 `붉은사막 출시 상태 검색해봐`가 suggestion으로 나오는지, 두 번째는 CONFLICT slot이 non-OFFICIAL이면 2개 query를 받고 OFFICIAL + `prior_probe_count == 0`이면 1개로 남는지 고정합니다.
- `_build_entity_slot_probe_queries` guard(seq 369), focus-slot CONFLICT wording(seq 385), `_claim_coverage_status_rank` / `_claim_coverage_status_label`, 그리고 seq 388/391/394/397 source-role priority entries는 의도적으로 수정하지 않았습니다.
- `rg -n -C 4 "_build_entity_reinvestigation_suggestions|max_queries_for_slot|출시 상태 검색해봐|CONFLICT" tests/test_smoke.py`와 `rg -n -C 4 "_build_entity_reinvestigation_suggestions|max_queries_for_slot|CoverageStatus\\.CONFLICT|test_coverage_reinvestigation_" tests/test_smoke.py`로 기존 smoke assertion을 다시 확인했고, old CONFLICT-drop / 1-query-cap에 직접 기대는 기존 테스트는 보이지 않았습니다. 따라서 이번 라운드에서 뒤집은 기존 assertion은 없습니다.
- 이번 라운드에서는 browser code, docs, 다른 test file, 다른 source file은 수정하지 않았습니다. `core/agent_loop.py`와 `tests/test_smoke.py`의 기존 dirty hunk는 유지했고, handoff가 지정한 두 분기와 smoke 회귀 구간만 추가로 수정했습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 16 tests in 0.079s`, `OK`
  - 기존 14건에 이번 CONFLICT-inclusive reinvestigation 회귀 2건이 추가돼 16건이 됐습니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 5 tests in 0.001s`, `OK`
  - seq 388/391/394/397 source-role weighting + conflict-separation 5건 수는 변하지 않았습니다.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `rg -n -C 4 "_build_entity_reinvestigation_suggestions|max_queries_for_slot|출시 상태 검색해봐|CONFLICT" tests/test_smoke.py`
  - 결과: 이번 새 reinvestigation coverage 회귀 2건 외에, old CONFLICT-drop / 1-query-cap에 직접 기대는 기존 assertion은 보이지 않았습니다.
- `rg -n "weak/missing slots targeted first|재조사|follow_up_suggestions|출시 상태 검색해봐|공식 플랫폼 검색해봐|개발사 검색해봐|서비스 공식 검색해봐|장르 검색해봐" docs README.md`
  - 결과: `docs/PRODUCT_SPEC.md:369`에 `weak/missing slots targeted first in reinvestigation suggestions` 문장이 남아 있습니다. 이번 라운드에서는 docs를 수정하지 않았고, 이 문장은 CONFLICT suggestion 포함 이후 narrow docs-sync 후보로 남깁니다.
- Playwright는 실행하지 않았습니다. 이번 슬라이스는 browser-visible copy, shared browser helper, docs contract를 바꾸지 않고 Python reinvestigation logic과 focused smoke regression만 만졌기 때문에 범위를 벗어납니다.
- `python3 -m unittest tests.test_web_app`와 `make e2e-test`도 실행하지 않았습니다. 둘 다 이번 slice 밖이며, 기존 unrelated failure family와 broad browser suite는 이번 라운드 목표와 직접 연결되지 않습니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md:369`의 `weak/missing slots targeted first in reinvestigation suggestions` 문장은 이번 CONFLICT suggestion 포함 이후 현재 구현과 완전히 맞지 않습니다. 별도 narrow docs-sync 후보로 남깁니다.
- Milestone 4의 remaining COMMUNITY/PORTAL/BLOG weighting, strong-vs-weak-vs-unresolved separation beyond CONFLICT, response-body `[정보 상충]` tag emission, reinvestigation threshold/probe retry tuning은 여전히 separate future slice 후보입니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family는 이번 handoff 범위 밖으로 남아 있습니다.
