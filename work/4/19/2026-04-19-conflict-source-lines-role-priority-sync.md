# 2026-04-19 conflict source lines role priority sync

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 `tests.test_smoke` 중심 검증, `py_compile`, `git diff --check`, role-priority/source-line candidate grep를 실제 실행 기준으로 정리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서로 이번 bounded slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 408에서 response body의 `상충하는 정보 [정보 상충]:` 헤더는 이미 추가됐지만, `근거 출처:` source-line helper는 여전히 `primary_claims`, `weak_claims`, `supplemental_claims`만 수집하고 있어서 conflict slot source가 source-line block에서 빠질 수 있었습니다.
- 같은 helper와 `_entity_claim_sort_key` 안의 hardcoded `role_priority` map 2개도 seq 388/391/394/397 이후 shipped `core/web_claims.py::_ROLE_PRIORITY`와 어긋나 있었습니다. `OFFICIAL`, `DESCRIPTIVE`, `NEWS` 값이 낡았고 `DATABASE`, `COMMUNITY` key가 빠져 있었습니다.

## 핵심 변경
- `core/agent_loop.py:4515-4552`의 `_build_entity_claim_source_lines` signature는 이제 keyword-only `conflict_claims` 인자를 포함하며, 인자 순서는 `primary_claims`, `conflict_claims`, `weak_claims`, `supplemental_claims`입니다. 본문 flatten iteration도 `[*primary_claims, *conflict_claims, *weak_claims, *supplemental_claims]`로 바꿨습니다.
- `core/agent_loop.py:4131-4140`의 `_entity_claim_sort_key` hardcoded `role_priority`와 `core/agent_loop.py:4541-4550`의 `_build_entity_claim_source_lines` hardcoded `role_priority`는 이제 둘 다 `core/web_claims.py::_ROLE_PRIORITY`와 같은 값으로 맞췄습니다. 즉 `OFFICIAL=5`, `WIKI=4`, `DATABASE=4`, `DESCRIPTIVE=3`, `NEWS=2`, `AUXILIARY=1`, `COMMUNITY=0`, `PORTAL=0`, `BLOG=0`이며, 기존에 없던 `DATABASE`, `COMMUNITY` key를 추가했습니다.
- `core/agent_loop.py:4781-4787`의 `_build_entity_web_summary` 단일 callsite는 이제 `conflict_claims=conflict_claims`를 같이 넘깁니다.
- `tests/test_smoke.py:1133-1204`에 `test_coverage_entity_card_source_line_includes_conflict_slot_source`를 추가했습니다. seq 408 header regression 바로 아래에 두었고, conflict slot source URL이 `근거 출처:` block에 실제로 나타나는지, 그리고 그 URL이 conflict section 이전 텍스트에는 없어서 새 flattening을 실제로 타는지 확인합니다.
- step 4 grep(`rg -n "SourceRole\\.(OFFICIAL|WIKI|DATABASE|DESCRIPTIVE|NEWS)|근거 출처:|링크:" tests/test_smoke.py`)과 `python3 -m unittest tests.test_smoke -k coverage` 기준으로 기존 `tests/test_smoke.py` assertion을 뒤집어야 하는 곳은 없었습니다. grep hit 중 role-priority 회귀는 모두 `core/web_claims.py::_ROLE_PRIORITY`를 잠그는 테스트였고, entity-card primary/source-line ordering을 old `_entity_claim_sort_key` 값으로 직접 고정한 기존 assertion은 보이지 않았습니다.
- handoff 금지 범위는 그대로 유지했습니다. seq 408 response-body header 자체, seq 385/400/405 CONFLICT chain surface, `core/agent_loop.py:5763-5776` regex canonicalization, `core/agent_loop.py:5924-5939` alternate builder, `core/web_claims.py::_ROLE_PRIORITY`, browser files, `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, docs, 다른 source file은 수정하지 않았습니다.

## 검증
- `rg -n "SourceRole\\.(OFFICIAL|WIKI|DATABASE|DESCRIPTIVE|NEWS)|근거 출처:|링크:" tests/test_smoke.py`
  - 결과: 기존 hit는 seq 388/391/394/397 `_ROLE_PRIORITY` 회귀들과 seq 408 conflict header regression, 이번 새 source-line regression뿐이었고, old `_entity_claim_sort_key` ordering을 직접 잠그는 기존 entity-card assertion은 보이지 않았습니다.
- `rg -n "근거 출처|primary_claims|weak_claims|supplemental_claims" docs`
  - 결과: source-of-truth root `docs/*.md`에는 `근거 출처` helper가 primary/weak/supplemental only라고 명시한 문장은 보이지 않았고, `docs/recycle/drafts/*`의 일반 구조 언급만 hit했습니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 18 tests in 0.103s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 5 tests in 0.001s`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- Playwright, `python3 -m unittest tests.test_web_app`, `make e2e-test`는 실행하지 않았습니다. 이번 slice는 Python helper/source-line ordering과 smoke regression만 바꾸며 browser-visible shared helper나 browser contract를 넓히지 않았습니다.

## 남은 리스크
- source-of-truth root `docs/*.md`에는 이번 helper scope drift를 직접 설명한 문장을 찾지 못했습니다. 다만 `docs/recycle/drafts/*`에는 `근거 출처` 구조를 설명하는 일반 문장이 남아 있으므로, 내일 narrow docs-sync가 필요해진다면 root docs가 아니라 draft/historical note 정리인지부터 먼저 판별해야 합니다.
- Milestone 4의 남은 code sub-axis는 여전히 separate future round 후보입니다. 예를 들면 COMMUNITY/PORTAL/BLOG tiering 세분화, reinvestigation threshold/probe cap tuning, strong-vs-weak-vs-unresolved 추가 polish, seq 408 response-body header용 optional Playwright scenario, claim-coverage panel conflict surface extension이 남아 있습니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family는 이번 slice와 무관한 dirty-state 영역으로 그대로 남아 있습니다.
