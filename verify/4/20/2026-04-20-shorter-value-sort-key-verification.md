# 2026-04-20 shorter value sort key verification

## 변경 파일
- `verify/4/20/2026-04-20-shorter-value-sort-key-verification.md`

## 사용 skill
- `round-handoff`: seq 427 `/work`(`work/4/20/2026-04-20-shorter-value-sort-key.md`)의 Milestone 4 Option E1 tie-break 수정 주장을 `core/web_claims.py`, `core/agent_loop.py`, `tests/test_smoke.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증만 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 427 `.pipeline/claude_handoff.md`(Gemini 426 Option E1 arbitration 기반)가 구현되어 새 `/work` 노트가 제출되었습니다. 이 라운드의 목표는 두 canonical claim sort key(`core/web_claims.py::_claim_sort_key`, `core/agent_loop.py::_entity_claim_sort_key`)의 value-length 축을 `len(value)` → `-len(value)`로 뒤집어 SHORTER value가 이기도록 바꾸고, `source_url`을 최종 lexicographic tie-breaker로 추가해 동일 length·동일 문자열일 때도 결정론적 primary claim 선택을 고정하는 것이었습니다.

## 핵심 변경
- `core/web_claims.py:61-69` 의 `_claim_sort_key`가 현재 `tuple[int, int, int, int, str, str]`을 반환하고 shape는 `(record.support_count, _ROLE_PRIORITY.get(record.source_role, 0), int(record.confidence * 1000), -len(record.value), record.value, record.source_url)` 입니다. handoff 지시와 문자 수준으로 일치합니다.
- `core/agent_loop.py:4130-4149` 의 `_entity_claim_sort_key`가 동일한 6-tuple shape로 바뀌었고, `role_priority` dict(OFFICIAL:5 / WIKI:4 / DATABASE:4 / DESCRIPTIVE:3 / NEWS:2 / AUXILIARY:1 / COMMUNITY:1 / PORTAL:1 / BLOG:0, seq 420 positions)는 그대로 유지됩니다. 두 sort key의 seq 411-era structural parity가 보존됐습니다.
- `core/agent_loop.py:4556` 의 `_build_entity_claim_source_lines::support_refs.sort`는 수정되지 않았습니다. title 길이 기반 정렬이라 value-length tie-break 축과 별개 도메인임을 `/work`도 명시했습니다.
- `tests/test_smoke.py:2708-2776` 에 `test_claims_sort_key_prefers_shorter_value_when_other_keys_tie`가 정확히 삽입됐습니다. 위치는 `test_claims_source_role_priority_splits_portal_community_above_blog`(`:2670-2706`) 직후, `test_claim_coverage_conflict_status_label_rank_and_probe_queries`(`:2778-`) 직전으로 handoff의 pin 경로와 동일합니다.
- 새 회귀는 두 축을 고정합니다: (1) 같은 slot/support/role/confidence에서 긴 value와 짧은 value를 양방향 순서로 `summarize_slot_coverage`에 넣어도 primary는 짧은 `"펄어비스"`로 수렴하고, (2) slot/support/role/confidence/value가 모두 같고 `source_url`만 다른 두 claim을 양방향 order로 넣어도 primary의 `source_url`이 같은 값으로 유지됩니다. supporting_sources 길이 assert도 merge 경로 회귀 가드로 추가됐습니다.
- sort key consumer는 `core/web_claims.py:111` (`merge_claim_records` winner 선택), `:185` (`summarize_slot_coverage` primary 선택), `core/agent_loop.py:4172`·`:4191` (`_select_entity_fact_card_claims` best selection) 네 곳뿐입니다. `rg -n '_claim_sort_key|_entity_claim_sort_key' --type py`로 재확인했습니다.
- handoff가 금지한 shipped surface는 보존됐습니다: seq 385/400/405 focus-slot 템플릿, seq 408 5-tuple + response-body header, seq 411 source-line + role_priority sync, seq 414 `_build_entity_claim_coverage_items` + `rendered_as=conflict`, seq 417 Playwright CONFLICT 시나리오, seq 420 `_ROLE_PRIORITY` positions, seq 423 reinvestigation overall cap. `app/`, `storage/`, `e2e/`, docs, agent-config 파일은 이번 라운드에서 수정되지 않았습니다.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `427` — 이미 shipped 됐고 새로운 `/work`로 consumed.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `425` — seq 426 advice로 이미 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `426` — seq 427 handoff로 이미 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — dispatcher-state 질문이 seq 423/427 shipping으로 이벤트 자연 해제된 상태 유지. 남은 blocker 없음.

## 검증
- 직접 코드/테스트 대조
  - `core/web_claims.py:61-69` 6-tuple + `-len(record.value)` + `record.source_url` 확인.
  - `core/agent_loop.py:4130-4149` 6-tuple + `-len(claim.value)` + `claim.source_url` + role_priority dict 보존 확인.
  - `core/agent_loop.py:4556` `support_refs.sort` 미수정 확인.
  - `tests/test_smoke.py:2708-2776` 새 회귀 위치 및 assert 3종(shorter-wins 양방향 2건 + source_url 양방향 1건 + supporting_sources 길이 가드) 확인.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`. 기존 6 + 신규 1. `test_claims_source_role_priority_splits_portal_community_above_blog`(seq 420) 포함 기존 assertion flip 없음.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 20 tests in 0.066s`, `OK`. seq 423 baseline 유지. `_claim_sort_key`를 간접 소비하는 coverage 테스트에서 shorter-wins로 primary가 뒤집힌 케이스 없음.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.076s`, `OK`. seq 423 baseline 유지.
- `python3 -m py_compile core/web_claims.py core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- core/web_claims.py core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `rg -n '_claim_sort_key|_entity_claim_sort_key' --type py`
  - 결과: 정의 2곳 + 소비자 4곳(web_claims.py:111/185, agent_loop.py:4172/4191)만 hit. 다른 실행 경로 없음을 재확인.
- Playwright, `tests.test_web_app`, `make e2e-test`는 이번 verify에서 돌리지 않았습니다. 이번 slice는 sort-key tuple 2곳과 smoke regression 1건만 바꿔 browser-visible contract / shared helper / selector를 건드리지 않았습니다.

## 남은 리스크
- Milestone 4 남은 후보 E2(entity-card strong-badge downgrade edge)와 E3(non-CONFLICT 전이 wording polish)는 여전히 별도 라운드 몫입니다. E1이 소비된 지금, 두 후보 중 어느 쪽이 더 정확히 pinned되는지는 여전히 slice_ambiguity 성격이라 다음 control은 `.pipeline/gemini_request.md`(seq 428)로 arbitration을 먼저 여는 편이 rule에 맞습니다.
- `/work` step 7 docs grep에서는 old sort tuple(`len(value)`) 또는 longer-wins behavior를 literal로 언급한 docs 문장을 찾지 못했습니다(hit는 `docs/recycle/drafts/projecth-investigation-pipeline-draft.md:129`의 `source_url: str` 한 건뿐, 현재 동작과 충돌하지 않음). 오늘(2026-04-20) docs-only round count는 계속 0.
- `prefer_probe_first` threshold(`core/agent_loop.py:3836-3840`), `_build_entity_slot_probe_queries` output shape, `_role_confidence_score` float axis는 overall cap과 별개로 남아 있으며 별도 tuning round 후보입니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` 실패는 이번 slice 밖이며 별도 truth-sync 라운드 몫입니다.
- seq 424 `.pipeline/operator_request.md`(dispatcher_state_truth_sync)는 seq 423/427 shipping으로 자연 해제 상태를 유지합니다. real operator-only decision / approval blocker / 안전 정지 / Gemini 부재 어느 조건에도 해당하지 않습니다.
