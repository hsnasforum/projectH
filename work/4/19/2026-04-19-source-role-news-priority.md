# 2026-04-19 source-role news priority

## 변경 파일
- core/web_claims.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 `tests.test_smoke` 중심 검증과 docs-order grep만 다시 실행하고, Playwright/`tests.test_web_app`를 왜 생략했는지 범위 기준으로 정리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 라운드의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 394 이후 `_ROLE_PRIORITY`는 `OFFICIAL: 5 > WIKI: 4 = DATABASE: 4 > DESCRIPTIVE: 3 > NEWS: 1 = AUXILIARY: 1` 상태라, verified news publisher와 generic auxiliary source가 tied `support_count`에서 같은 priority에 머물렀습니다.
- 이번 슬라이스 목표는 handoff 그대로 `SourceRole.NEWS`만 `2`로 올려 AUXILIARY보다 앞세우고, tied `support_count`에서 NEWS가 AUXILIARY보다 우선한다는 계약을 `tests/test_smoke.py`의 focused regression으로 고정하는 것이었습니다.
- `_claim_sort_key`, `merge_claim_records`, CONFLICT family surface, browser/docs 코드는 이번 라운드 범위에서 제외했습니다.

## 핵심 변경
- `core/web_claims.py::_ROLE_PRIORITY`에서 `SourceRole.NEWS`만 `1 -> 2`로 올렸습니다. 현재 ladder는 `OFFICIAL(5) > WIKI(4) = DATABASE(4) > DESCRIPTIVE(3) > NEWS(2) > AUXILIARY(1) > COMMUNITY/PORTAL/BLOG(0)`이며, seq 394 이후 다른 entry 값은 그대로 유지했습니다.
- `tests/test_smoke.py`에 `test_claims_source_role_priority_places_news_above_auxiliary_below_descriptive`를 추가했습니다. 이 테스트는 `_ROLE_PRIORITY[NEWS] > _ROLE_PRIORITY[AUXILIARY]`, `_ROLE_PRIORITY[NEWS] < _ROLE_PRIORITY[DESCRIPTIVE]`, `_ROLE_PRIORITY[NEWS] > _ROLE_PRIORITY[COMMUNITY]`를 직접 잠그고, tied `support_count=1` pair에서 primary claim이 NEWS-backed value를 고르는지 확인합니다. 위치는 seq 394의 `test_claims_source_role_priority_places_descriptive_above_news_below_database` 바로 아래입니다.
- `rg -n -C 4 "source_role=SourceRole\\.NEWS|source_role = SourceRole\\.NEWS|SourceRole\\.NEWS" tests/test_smoke.py`로 old `NEWS: 1` 위치에 기대는 다른 smoke test를 다시 확인했고, seq 394 DESCRIPTIVE regression과 이번 새 regression 외에 추가 ClaimRecord-level test는 보이지 않았습니다. 따라서 이번 라운드에서 primary-value/role assertion을 뒤집은 기존 테스트는 없었습니다.
- seq 394의 `test_claims_source_role_priority_places_descriptive_above_news_below_database`는 assertion 변경 없이 그대로 통과합니다. `DESCRIPTIVE(3) > NEWS(2)`가 여전히 유지되기 때문입니다.
- 기존 conflict-separation 테스트(`test_claims_summarize_slot_coverage_conflicting_trusted_alternative_returns_conflict`)도 assertion 변경 없이 그대로 통과합니다. 이 테스트는 NEWS를 ClaimRecord `source_role` 수준에서 쓰지 않기 때문입니다.
- 이번 라운드에서는 browser code, docs, 다른 test file, 다른 source file은 수정하지 않았습니다. `core/web_claims.py`와 `tests/test_smoke.py`의 기존 dirty hunk는 유지했고, handoff가 지정한 NEWS priority와 smoke regression 구간만 추가로 수정했습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 5 tests in 0.000s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 14 tests in 0.057s`, `OK`
  - 새 회귀 테스트 이름에 `coverage`가 없어서 seq 394 verify와 같은 14건이 유지됐습니다.
- `python3 -m py_compile core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `rg -n -C 4 "source_role=SourceRole\\.NEWS|source_role = SourceRole\\.NEWS|SourceRole\\.NEWS" tests/test_smoke.py`
  - 결과: seq 394 DESCRIPTIVE regression과 이번 새 regression 외에, old `NEWS: 1` priority에 기대는 다른 ClaimRecord-level smoke test는 보이지 않았습니다.
- `rg -n "보조 기사.{0,20}보조 출처|NEWS.{0,20}AUXILIARY" docs README.md`
  - 결과: 매치 없음. 이번 라운드 기준으로 shipped docs/README에서 NEWS를 AUXILIARY 아래나 DESCRIPTIVE 위로 명시적으로 열거한 짧은 trust/priority 문장은 찾지 못했습니다.
- Playwright는 실행하지 않았습니다. 이번 슬라이스는 browser-visible copy, shared browser helper, docs contract를 바꾸지 않고 Python source-role weighting과 focused smoke regression만 만졌기 때문에 범위를 벗어납니다.
- `python3 -m unittest tests.test_web_app`와 `make e2e-test`도 실행하지 않았습니다. 둘 다 이번 slice 밖이며, 기존 unrelated failure family와 broad browser suite는 이번 라운드 목표와 직접 연결되지 않습니다.

## 남은 리스크
- Milestone 4의 COMMUNITY/PORTAL/BLOG ladder, reinvestigation trigger threshold, strong-vs-weak-vs-unresolved separation beyond CONFLICT, response-body `[정보 상충]` tag emission은 여전히 별도 future slice 후보입니다.
- 이번 라운드는 source-role weighting 중 `NEWS: 2` 승격만 다뤘습니다. AUXILIARY 이하 tiering과 그 밖의 추가 source-role weighting은 아직 범위 밖입니다.
- 이번 라운드에서 rerun한 docs-order grep 기준으로 shipped docs/README에 NEWS priority ordering을 직접 적은 문장은 보이지 않았습니다. 이후 문서가 source-role ladder를 직접 서술하기 시작하면 별도 narrow docs-sync가 필요할 수 있습니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family는 이번 handoff 범위 밖으로 남아 있습니다.
