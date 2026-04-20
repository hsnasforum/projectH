# 2026-04-20 shorter value sort key

## 변경 파일
- core/web_claims.py
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 grep, `tests.test_smoke` family rerun, `py_compile`, `git diff --check`만 실제 실행 기준으로 정리했습니다.
- work-log-closeout: `work/4/20/` 아래에 표준 섹션 순서로 이번 bounded slice의 변경/검증/남은 리스크만 기록했습니다.

## 변경 이유
- 기존 canonical sort key는 `(support_count, role_priority, confidence, len(value), value)`라서 support/role/confidence가 모두 같을 때 LONGER `value`가 primary claim으로 선택됐습니다. entity-card slot 값으로는 긴 설명문보다 짧고 식별적인 값이 더 적합한데, 현재 tie-break는 그 반대로 기울어 있었습니다.
- 이번 라운드는 Milestone 4 strong-tied-with-strong tie-break를 정확한 tuple 수준에서 조정해, 같은 조건이면 SHORTER `value`가 이기도록 바꾸고, 길이와 문자열까지 같을 때는 `source_url`로 결정론적 마지막 tie-break를 주는 것이 목적이었습니다.

## 핵심 변경
- `core/web_claims.py::_claim_sort_key`는 이제 `[core/web_claims.py](/home/xpdlqj/code/projectH/core/web_claims.py#L61)`에서 `tuple[int, int, int, int, str, str]`를 반환하고, shape는 `(support_count, role_priority, int(confidence*1000), -len(value), value, source_url)`입니다. `len` 차원을 음수로 뒤집어 shorter value가 이기게 했고, `source_url`을 최종 lexicographic tie-break로 추가했습니다.
- `core/agent_loop.py::_entity_claim_sort_key`도 `[core/agent_loop.py](/home/xpdlqj/code/projectH/core/agent_loop.py#L4130)`에서 동일한 6-tuple shape로 바꿨습니다. role-priority dict는 그대로 두고 tuple만 같은 구조로 맞춰, seq 411 이후 유지해 온 두 sort key의 parity를 보존했습니다.
- `[core/agent_loop.py](/home/xpdlqj/code/projectH/core/agent_loop.py#L4556)`의 `_build_entity_claim_source_lines::support_refs.sort`는 의도적으로 수정하지 않았습니다. 그 정렬은 claim value 길이가 아니라 support reference title 길이를 다루는 별도 surface라 이번 범위 밖입니다.
- `[tests/test_smoke.py](/home/xpdlqj/code/projectH/tests/test_smoke.py#L2708)`에 `test_claims_sort_key_prefers_shorter_value_when_other_keys_tie`를 추가했습니다. 위치는 `test_claims_source_role_priority_splits_portal_community_above_blog` 바로 뒤, `test_claim_coverage_conflict_status_label_rank_and_probe_queries` 바로 앞입니다.
- 새 회귀는 두 축만 고정합니다. 첫째, 같은 slot/support/role/confidence에서 긴 값과 짧은 값이 경쟁하면 `summarize_slot_coverage([long_claim, short_claim], ...)`와 reversed order 둘 다 짧은 `"펄어비스"`를 primary로 고릅니다. 둘째, slot/support/role/confidence/value가 모두 같고 `source_url`만 다른 두 claim을 양방향 order로 넣어도 `primary_claim.source_url`이 같은 값으로 유지되는지 확인해 결정론을 고정합니다.
- step 7 grep 결과:
  - `rg -n 'len\\(.*\\.value\\)|len\\(record\\.value\\)|len\\(claim\\.value\\)' core/ tests/`는 `core/web_claims.py::_claim_sort_key`, `core/agent_loop.py::_entity_claim_sort_key`, 그리고 unrelated guard인 `core/agent_loop.py:4201 if len(best.value) > 120`만 찾았습니다. positive-sense `len(value)`를 우선순위로 쓰는 다른 code path는 없었습니다.
  - `rg -n '_claim_sort_key|_entity_claim_sort_key' .` 기준 executable consumer는 `core/web_claims.py:111`, `core/web_claims.py:185`, `core/agent_loop.py:4172`, `core/agent_loop.py:4191`뿐이었습니다. 나머지 hit는 과거 `/work`/`/verify`/`report` 기록으로, 실행 경로는 아닙니다.
  - `rg -n 'primary_claim.*value|primary_claim.value ==|primary_claim.value\\b' tests/test_smoke.py tests/test_web_app.py`는 `tests/test_smoke.py`의 기존 assertion 몇 건과 이번 새 회귀만 찾았고 `tests/test_web_app.py` hit는 없었습니다. 기존 assertion들은 support_count 또는 role tier 차이로 primary가 갈리는 케이스라 shorter-wins로 뒤집히지 않았고, 실제 `-k claims`/`-k coverage` rerun도 그대로 통과했습니다.
  - `rg -n 'source_url|len\\(value\\)|len\\(record\\.value\\)' docs/`는 `docs/recycle/drafts/projecth-investigation-pipeline-draft.md:129`의 `source_url: str` 필드 선언만 찾았습니다. old sort tuple이나 longer-wins behavior를 직접 적은 문장은 찾지 못했습니다.
- seq 408/411/414/417/420/423 shipped surface는 의도적으로 손대지 않았습니다.

## 검증
- `rg -n 'len\\(.*\\.value\\)|len\\(record\\.value\\)|len\\(claim\\.value\\)' core/ tests/`
  - 결과: sort key 2곳과 unrelated `len(best.value) > 120` guard 1곳만 hit.
- `rg -n '_claim_sort_key|_entity_claim_sort_key' .`
  - 결과: executable consumer는 `core/web_claims.py:111`, `core/web_claims.py:185`, `core/agent_loop.py:4172`, `core/agent_loop.py:4191`만 확인. 나머지는 historical note/report hit.
- `rg -n 'primary_claim.*value|primary_claim.value ==|primary_claim.value\\b' tests/test_smoke.py tests/test_web_app.py`
  - 결과: `tests/test_smoke.py`의 기존 assertion과 이번 새 회귀만 hit, `tests/test_web_app.py` hit 없음. 기존 assertion flip 없음.
- `rg -n 'source_url|len\\(value\\)|len\\(record\\.value\\)' docs/`
  - 결과: `docs/recycle/drafts/projecth-investigation-pipeline-draft.md:129`의 `source_url: str` 1건만 hit. old sort tuple / longer-wins 문장 없음.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.000s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 20 tests in 0.105s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.101s`, `OK`
- `python3 -m py_compile core/web_claims.py core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/web_claims.py core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- Playwright, `python3 -m unittest tests.test_web_app`, `make e2e-test`는 실행하지 않았습니다. 이번 slice는 browser-visible copy가 아니라 sort-key tuple 2곳과 smoke regression 1건만 바꿨습니다.

## 남은 리스크
- Milestone 4 남은 sub-candidate E2(entity-card strong-badge downgrade edge)와 E3(non-CONFLICT transition wording polish)는 이후 라운드 후보로 남아 있습니다.
- step 7 docs grep에서는 old sort tuple이나 longer-wins behavior를 직접 적은 문장을 찾지 못했습니다. `docs/recycle/drafts/projecth-investigation-pipeline-draft.md:129`의 `source_url: str`는 현재 변경과 충돌하지 않아 그대로 두었고, 오늘(2026-04-20) docs-only round count도 계속 0입니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 밖에 그대로 남아 있습니다.
