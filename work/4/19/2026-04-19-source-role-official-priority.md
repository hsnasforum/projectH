# 2026-04-19 source-role official priority

## 변경 파일
- core/web_claims.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 `tests.test_smoke` 중심 검증만 다시 돌리고, Playwright/`tests.test_web_app`를 왜 생략했는지 범위 기준으로 정리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서에 맞춰 이번 라운드의 실제 코드 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- `core/web_claims.py::_ROLE_PRIORITY`는 tie된 `support_count`에서 `SourceRole.WIKI: 4`가 `SourceRole.OFFICIAL: 3`보다 앞서도록 되어 있어, 공식 출처와 위키 요약이 같은 지지 수를 가질 때도 primary claim이 WIKI 쪽으로 기울고 있었습니다.
- 이번 슬라이스 목표는 handoff 그대로 OFFICIAL만 `5`로 올려 WIKI보다 우선시키고, 그에 따라 `tests/test_smoke.py`의 기존 primary-value assertion과 새 focused regression을 맞추는 것이었습니다.
- `_claim_sort_key` tuple shape, `merge_claim_records`, 다른 `SourceRole` entry, CONFLICT family surface, browser/docs 코드는 이번 라운드 범위에서 제외했습니다.

## 핵심 변경
- `core/web_claims.py`에서 `_ROLE_PRIORITY`의 `SourceRole.OFFICIAL`만 `3 -> 5`로 올렸습니다. `WIKI: 4`, `DATABASE: 3`, `DESCRIPTIVE: 2`, `NEWS: 1`, `AUXILIARY: 1`, `COMMUNITY: 0`, `PORTAL: 0`, `BLOG: 0`는 그대로 유지했습니다.
- `tests/test_smoke.py`의 기존 conflict-separation 테스트는 `coverage["장르/성격"].status == CoverageStatus.CONFLICT` assertion을 그대로 유지하면서, primary value 기대값만 `"오픈월드 액션 어드벤처 게임"`에서 `"생존 제작 RPG"`로 뒤집었습니다. inline comment도 OFFICIAL > WIKI tie-break를 반영하도록 짧게 고쳤습니다.
- `tests/test_smoke.py`에 `test_claims_summarize_slot_coverage_prefers_official_over_wiki_when_support_ties`를 추가해 `_ROLE_PRIORITY[SourceRole.OFFICIAL] > _ROLE_PRIORITY[SourceRole.WIKI]`를 직접 고정하고, tied `support_count=1` pair에서도 primary claim이 OFFICIAL-backed value를 고르는지 잠갔습니다. 이 새 회귀는 file의 기존 claim/coverage 테스트 블록 바로 아래에 놓였습니다.
- handoff의 required verification인 `python3 -m unittest tests.test_smoke -k claims`가 처음에는 `Ran 0 tests`로 끝나서, 관련 두 테스트 이름을 `test_claims_...` prefix로만 좁게 조정했습니다. 코드 의미나 assertion 범위는 바꾸지 않았고, 최종 rerun에서는 해당 필터가 conflict test와 새 regression 두 개만 정확히 잡습니다.
- `rg -n -C 4 "SourceRole\\.(OFFICIAL|WIKI)" tests/test_smoke.py`로 tied-support WIKI/OFFICIAL pairing 의존성을 다시 확인했고, 기존 old order에 맞춰 추가 assertion flip이 필요한 다른 테스트는 찾지 못했습니다.
- 이번 라운드에서는 browser code, docs, 다른 test file, 다른 source file은 수정하지 않았습니다. `core/web_claims.py`, `tests/test_smoke.py`에는 이번 라운드 이전 dirty hunk가 이미 있었고, 이번 작업은 handoff가 지정한 OFFICIAL priority + smoke assertion 범위만 추가로 수정했습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k claims`
  - 1차 결과: `Ran 0 tests in 0.000s`, `NO TESTS RAN`
  - 두 관련 테스트명을 `test_claims_...`로 맞춘 뒤 2차 결과: `Ran 2 tests in 0.000s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 14 tests in 0.055s`, `OK`
- `python3 -m py_compile core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/web_claims.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `rg -n -C 4 "SourceRole\\.(OFFICIAL|WIKI)" tests/test_smoke.py`
  - 결과: 기존 conflict-separation test와 새 OFFICIAL > WIKI regression 외에 tie-break를 직접 잠그는 추가 테스트는 보이지 않았습니다.
- `rg -n "백과 기반.{0,20}공식 기반|WIKI.{0,20}OFFICIAL" docs README.md`
  - 결과: 매치 없음. 이번 라운드 기준으로 shipped docs/README에서 OFFICIAL를 WIKI 아래로 명시적으로 열거한 짧은 trust/priority 문장은 찾지 못했습니다.
- Playwright는 실행하지 않았습니다. 이번 슬라이스는 browser-visible copy, shared browser helper, docs contract를 바꾸지 않고 Python source-role tie-break와 smoke regression만 만졌기 때문에 범위를 벗어납니다.
- `python3 -m unittest tests.test_web_app`와 `make e2e-test`도 실행하지 않았습니다. 둘 다 이번 slice 밖이며, 기존 unrelated failure family와 broad browser suite는 이번 라운드 목표와 직접 연결되지 않습니다.

## 남은 리스크
- Milestone 4의 reinvestigation trigger threshold, strong-vs-weak-vs-unresolved separation beyond CONFLICT, response-body `[정보 상충]` tag emission은 여전히 별도 future slice 후보입니다.
- 이번 라운드는 source-role weighting 중 OFFICIAL > WIKI tie-break만 만졌습니다. `DATABASE`와 다른 role 간 추가 weighting 조정은 아직 범위 밖입니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family는 이번 handoff 범위 밖으로 남아 있습니다.
