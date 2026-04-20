# 2026-04-19 source-role descriptive priority

## 변경 파일
- core/web_claims.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 `tests.test_smoke` 중심 검증과 docs-order grep만 다시 실행하고, Playwright/`tests.test_web_app`를 왜 생략했는지 범위 기준으로 정리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 라운드의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 391 이후 `_ROLE_PRIORITY`는 `OFFICIAL: 5 > WIKI: 4 = DATABASE: 4 > DESCRIPTIVE: 2 > NEWS/AUXILIARY: 1` 상태라, structured editorial/descriptive source가 raw news/auxiliary보다 겨우 한 단계만 앞서 있었습니다.
- 이번 슬라이스 목표는 handoff 그대로 `SourceRole.DESCRIPTIVE`만 `3`으로 올려 NEWS/AUXILIARY보다 더 분명히 앞세우고, tied `support_count`에서 DESCRIPTIVE가 NEWS보다 우선한다는 계약을 `tests/test_smoke.py`의 focused regression으로 고정하는 것이었습니다.
- `_claim_sort_key`, `merge_claim_records`, CONFLICT family surface, browser/docs 코드는 이번 라운드 범위에서 제외했습니다.

## 핵심 변경
- `core/web_claims.py::_ROLE_PRIORITY`에서 `SourceRole.DESCRIPTIVE`만 `2 -> 3`으로 올렸습니다. 현재 ladder는 `OFFICIAL(5) > WIKI(4) = DATABASE(4) > DESCRIPTIVE(3) > NEWS/AUXILIARY(1) > COMMUNITY/PORTAL/BLOG(0)`이며, seq 391 이후 다른 entry 값은 그대로 유지했습니다.
- `tests/test_smoke.py`에 `test_claims_source_role_priority_places_descriptive_above_news_below_database`를 추가했습니다. 이 테스트는 `_ROLE_PRIORITY[DESCRIPTIVE] > _ROLE_PRIORITY[NEWS]`, `_ROLE_PRIORITY[DESCRIPTIVE] > _ROLE_PRIORITY[AUXILIARY]`, `_ROLE_PRIORITY[DESCRIPTIVE] < _ROLE_PRIORITY[DATABASE]`, `_ROLE_PRIORITY[DESCRIPTIVE] < _ROLE_PRIORITY[WIKI]`를 직접 잠그고, tied `support_count=1` pair에서 primary claim이 DESCRIPTIVE-backed value를 고르는지 확인합니다. 위치는 seq 391의 `test_claims_source_role_priority_ties_database_with_wiki_above_descriptive` 바로 아래입니다.
- `rg -n -C 4 "source_role=SourceRole\\.DESCRIPTIVE|source_role = SourceRole\\.DESCRIPTIVE|SourceRole\\.DESCRIPTIVE" tests/test_smoke.py`로 old `DESCRIPTIVE: 2` 위치에 기대는 다른 smoke test를 다시 확인했고, seq 391 DATABASE regression과 이번 새 regression 외에 추가 ClaimRecord-level test는 보이지 않았습니다. 따라서 이번 라운드에서 primary-value/role assertion을 뒤집은 기존 테스트는 없었습니다.
- seq 391의 `test_claims_source_role_priority_ties_database_with_wiki_above_descriptive`는 assertion 변경 없이 그대로 통과합니다. DATABASE(4) > DESCRIPTIVE(3)가 여전히 유지되기 때문입니다.
- 기존 conflict-separation 테스트(`test_claims_summarize_slot_coverage_conflicting_trusted_alternative_returns_conflict`)도 assertion 변경 없이 그대로 통과합니다. 이 테스트는 DESCRIPTIVE를 ClaimRecord `source_role` 수준에서 쓰지 않기 때문입니다.
- 이번 라운드에서는 browser code, docs, 다른 test file, 다른 source file은 수정하지 않았습니다. `core/web_claims.py`와 `tests/test_smoke.py`의 기존 dirty hunk는 유지했고, handoff가 지정한 DESCRIPTIVE priority와 smoke regression 구간만 추가로 수정했습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 4 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 14 tests in 0.076s`, `OK`
  - 새 회귀 테스트 이름에 `coverage`가 없어서 seq 391 verify와 같은 14건이 유지됐습니다.
- `python3 -m py_compile core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `rg -n -C 4 "source_role=SourceRole\\.DESCRIPTIVE|source_role = SourceRole\\.DESCRIPTIVE|SourceRole\\.DESCRIPTIVE" tests/test_smoke.py`
  - 결과: seq 391 DATABASE regression과 이번 새 regression 외에, old `DESCRIPTIVE: 2` priority에 기대는 다른 ClaimRecord-level smoke test는 보이지 않았습니다.
- `rg -n "설명형.{0,20}기사|DESCRIPTIVE.{0,20}NEWS" docs README.md`
  - 결과: 매치 없음. 이번 라운드 기준으로 shipped docs/README에서 DESCRIPTIVE를 NEWS 아래나 DATABASE/WIKI 위로 명시적으로 열거한 짧은 trust/priority 문장은 찾지 못했습니다.
- Playwright는 실행하지 않았습니다. 이번 슬라이스는 browser-visible copy, shared browser helper, docs contract를 바꾸지 않고 Python source-role weighting과 focused smoke regression만 만졌기 때문에 범위를 벗어납니다.
- `python3 -m unittest tests.test_web_app`와 `make e2e-test`도 실행하지 않았습니다. 둘 다 이번 slice 밖이며, 기존 unrelated failure family와 broad browser suite는 이번 라운드 목표와 직접 연결되지 않습니다.

## 남은 리스크
- Milestone 4의 reinvestigation trigger threshold, strong-vs-weak-vs-unresolved separation beyond CONFLICT, response-body `[정보 상충]` tag emission은 여전히 별도 future slice 후보입니다.
- 이번 라운드는 source-role weighting 중 `DESCRIPTIVE: 3` 승격만 다뤘습니다. NEWS vs AUXILIARY, COMMUNITY/PORTAL/BLOG tiering, 그 밖의 추가 source-role weighting은 아직 범위 밖입니다.
- 이번 라운드에서 rerun한 docs-order grep 기준으로 shipped docs/README에 DESCRIPTIVE priority ordering을 직접 적은 문장은 보이지 않았습니다. 이후 문서가 source-role ladder를 직접 서술하기 시작하면 별도 narrow docs-sync가 필요할 수 있습니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family는 이번 handoff 범위 밖으로 남아 있습니다.
