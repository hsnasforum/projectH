# 2026-04-20 source role weighting portal community

## 변경 파일
- core/web_claims.py
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 grep, `tests.test_smoke -k claims`, `-k coverage`, `py_compile`, `git diff --check`만 실제 실행 기준으로 정리했습니다.
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경/검증/리스크만 기록했습니다.

## 변경 이유
- Milestone 4 source role weighting에서 기존 `COMMUNITY == PORTAL == BLOG == 0` 묶음은 블로그를 strict bottom tier로 분리하지 못해, support tie에서 포털/커뮤니티와 개인 블로그를 같은 축으로 취급하고 있었습니다.
- seq 411 이후 `_ROLE_PRIORITY`는 `core/web_claims.py` master와 `core/agent_loop.py` 내부 hardcoded mirror 2곳이 항상 같아야 하므로, 이번 라운드는 `COMMUNITY`/`PORTAL`만 1로 올리고 `BLOG`를 0에 남기는 작은 숫자 permutation을 세 맵에 함께 반영하는 것이 목적이었습니다.

## 핵심 변경
- `core/web_claims.py:32-42`의 `_ROLE_PRIORITY`는 이제 `COMMUNITY: 1`, `PORTAL: 1`, `BLOG: 0`입니다. `AUXILIARY: 1`은 그대로 유지되어 `COMMUNITY`/`PORTAL`과 같은 tier를 공유하고, `OFFICIAL: 5`, `WIKI: 4`, `DATABASE: 4`, `DESCRIPTIVE: 3`, `NEWS: 2` 위치도 그대로 유지했습니다.
- `core/agent_loop.py:4133-4141`의 `_entity_claim_sort_key` mirror와 `core/agent_loop.py:4547-4555`의 `_build_entity_claim_source_lines` mirror에도 같은 두 숫자 변경만 적용해, 세 `_ROLE_PRIORITY` 맵이 다시 동일하게 유지되도록 맞췄습니다.
- `tests/test_smoke.py:2647-2683`에 `test_claims_source_role_priority_splits_portal_community_above_blog`를 추가했습니다. 위치는 기존 `test_claims_source_role_priority_places_news_above_auxiliary_below_descriptive` 직후, `test_claim_coverage_conflict_status_label_rank_and_probe_queries` 직전입니다.
- 새 회귀는 `_ROLE_PRIORITY[SourceRole.COMMUNITY] == 1`, `_ROLE_PRIORITY[SourceRole.PORTAL] == 1`, `_ROLE_PRIORITY[SourceRole.BLOG] == 0`, `_ROLE_PRIORITY[SourceRole.AUXILIARY] == 1`, `COMMUNITY > BLOG`, `PORTAL > BLOG`, `NEWS > COMMUNITY`를 직접 고정합니다. 이어서 `summarize_slot_coverage([blog_claim, portal_claim], slots=("이용 형태",))`에서 tie support(`1` vs `1`)일 때 primary claim이 `PORTAL` 쪽으로 선택되는지 확인합니다.
- step 5 grep 결과, 기존 `tests/test_smoke.py`에는 `COMMUNITY == 0`, `PORTAL == 0`, `COMMUNITY == PORTAL == BLOG`, `COMMUNITY/PORTAL == BLOG`를 고정하는 assertion이 없었습니다. `core/` 쪽에서도 하드coded role-priority map은 `core/web_claims.py` 1곳과 `core/agent_loop.py` mirror 2곳뿐이었고, 나머지는 `core/agent_loop.py:4108-4109`의 `_role_confidence_score` float 축과 `core/source_policy.py`의 role label reference뿐이었습니다. `docs/`에서는 `COMMUNITY`/`PORTAL`/`BLOG` numeric position을 직접 적은 문장을 찾지 못해 이번 라운드에서 docs는 수정하지 않았습니다.
- `_role_confidence_score` float scores(`PORTAL: 0.45`, `BLOG: 0.35`, `AUXILIARY: 0.4`)는 별도 축이라 의도적으로 수정하지 않았고, seq 408/411/414/417 CONFLICT chain surface와 Playwright scenario, docs도 손대지 않았습니다.

## 검증
- `rg -n 'COMMUNITY|PORTAL|BLOG' tests/test_smoke.py`
  - 결과: 기존 pinned equality/zero assertion은 없고, 기존 `NEWS > COMMUNITY` 1건과 이번 새 회귀 block만 확인됐습니다.
- `rg -n '_ROLE_PRIORITY' tests`
  - 결과: `_ROLE_PRIORITY`를 직접 참조하는 회귀는 기존 priority tests와 이번 새 회귀뿐이었고, `COMMUNITY == 0` 또는 `COMMUNITY == PORTAL == BLOG`를 고정한 테스트는 없었습니다.
- `rg -n 'SourceRole.COMMUNITY|SourceRole.PORTAL|SourceRole.BLOG' core/`
  - 결과: 하드coded role-priority map은 `core/web_claims.py` 1곳과 `core/agent_loop.py` 2곳만 확인됐습니다. 별도 numeric priority map은 없고, `_role_confidence_score` float axis와 role label reference만 남아 있습니다.
- `rg -n 'PORTAL.*0|COMMUNITY.*0|BLOG' docs/`
  - 결과: hit 없음. numeric priority를 직접 열거한 docs 문장은 찾지 못했습니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 6 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 19 tests in 0.071s`, `OK`
- `python3 -m py_compile core/web_claims.py core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/web_claims.py core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- Playwright, `python3 -m unittest tests.test_web_app`, `make e2e-test`는 실행하지 않았습니다. 이번 slice는 integer role-priority와 smoke regression 1건만 바꾸며 browser copy/selector/shared browser helper를 바꾸지 않았습니다.

## 남은 리스크
- Milestone 4 남은 후보 D(reinvestigation threshold)와 E(strong-vs-weak-vs-unresolved further polish)는 다음 라운드 후보로 남아 있습니다.
- 이번 step 5 grep에서는 `COMMUNITY`/`PORTAL`/`BLOG` numeric role-priority를 직접 열거한 docs 문장을 찾지 못했습니다. 따라서 narrow docs-sync follow-up은 열지 않았고, 오늘(2026-04-20) docs-only round count도 계속 0입니다.
- `_role_confidence_score` float axis는 `_ROLE_PRIORITY` integer axis와 별개로 남아 있으며, 향후 tuning round에서 따로 다뤄야 합니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 밖에 그대로 남아 있습니다.
