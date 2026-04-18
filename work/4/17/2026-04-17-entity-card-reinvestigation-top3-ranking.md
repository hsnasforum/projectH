# entity-card reinvestigation top-3 ranking

HANDOFF_SHA: 870bdd77c1e5f819a51ca67396a753e6c0c0e2b01d943ad4c385245538933c33

## 변경 파일

- `core/agent_loop.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`

## 사용 skill

- 없음

## 변경 이유

- `docs/TASK_BACKLOG.md:146-149`에서 현재 단계의 최상단 항목인 "Improve entity-card web investigation quality" / "Reinvestigate weak or unresolved slots more effectively"를 닫기 시작하는 가장 작은 슬라이스입니다. 닫힌 runtime-docs cleanup family를 다시 열지 않고, 대신 승인 제어된 외부 웹 조사 경로 안에서 user-visible 개선을 한 단계 넣는 방향입니다.
- 기존 `_build_entity_reinvestigation_suggestions()`는 status 우선순위(MISSING → WEAK) 뒤에 raw stored index로만 정렬했기 때문에, 같은 status 버킷 안에서는 저장된 `claim_coverage` 순서가 top-3 targeted prompt를 그대로 결정했습니다. 그래서 user 입장에서 가장 쉽게 closable한 gap (빈 MISSING 슬롯, 신뢰도 낮은 단일 출처 WEAK 슬롯)이 stored order 뒤로 밀리면 최대 3개 targeted prompt 자리가 낭비되는 구조였습니다.
- 이번 슬라이스는 `_build_entity_reinvestigation_suggestions()` 한 곳 안에서 `candidate_count` / `source_role` / 작은 slot-priority map만으로 top-3을 다시 고르게 해서 user-visible gap을 더 잘 닫도록 바꿉니다. 새 storage 필드, 새 UI, 새 answer mode, 새 권한 흐름을 요구하지 않는 bounded 변경입니다.

## 핵심 변경

- `core/agent_loop.py`의 `_build_entity_reinvestigation_suggestions()`에서 기존 `(status_priority, stored_index)` 2단 정렬을 `(status_rank, sub_rank, slot_rank, stored_index)` 4단 정렬로 확장했습니다.
  - `status_rank`: 기존과 동일하게 MISSING(0) → WEAK(1). STRONG / 기타 status는 이전과 동일하게 targeted prompt 후보에서 제외됩니다.
  - `sub_rank` (MISSING): `candidate_count == 0`인 완전 공백 슬롯이 0, 그 외 noisy MISSING 슬롯이 1. 공백 슬롯은 user-visible gap을 "덧쓰기" 없이 직접 닫을 수 있어 targeted prompt 투자 대비 기대 이득이 큽니다.
  - `sub_rank` (WEAK): `source_role`이 `TRUSTED_CLAIM_SOURCE_ROLES` 밖(빈 문자열 포함)인 경우 0, trusted role일 때 1. 신뢰도 낮은 단일 출처가 가장 취약하고 targeted recheck 효과가 큽니다.
  - `slot_rank`: 새 클래스 상수 `_REINVESTIGATION_SLOT_USER_PRIORITY = {"개발": 0, "이용 형태": 1, "상태": 2, "서비스/배급": 3, "장르/성격": 4}`를 사용합니다. 같은 status/sub_rank 안에서 user-visible disambiguation 비중이 큰 슬롯을 먼저 선택합니다.
  - `stored_index`는 이제 맨 마지막 tie-break으로만 쓰입니다. 더는 top-3 선택을 혼자 결정하지 못합니다.
- 레거시 슬롯 canonicalization (`_canonical_legacy_entity_slot`), prompt 문자열, STRONG 제외, generic fallback prompt 세 개 및 dedupe, answer-mode 라우팅, focus-slot progress 의미론은 건드리지 않았습니다.
- `_follow_up_suggestions_for_web_search()`는 그대로 이 helper를 호출하므로 entity-card 경로에서는 자동으로 새 ranking을 얻고, 비-entity-card 경로는 이전과 동일합니다.

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` → 통과.
- `python3 -m unittest tests.test_smoke -k reinvestigation` → 3/3 통과 (새 regression `test_entity_reinvestigation_top3_ranks_by_slot_value_and_source_fragility_over_stored_order` 포함).
- `python3 -m unittest tests.test_web_app -k reinvestigation` → 3/3 통과 (새 API 경로 regression `test_handle_chat_load_web_search_record_id_entity_reinvestigation_top3_ranks_by_slot_value_and_source_fragility` 포함). 새 테스트는 raw stored order가 first-pick할 legacy 경로와 다른 top-3 (`서비스 공식`, `장르`, `개발사`)을 locking합니다.
- `python3 -m unittest tests.test_smoke -k claim_coverage` → 5/5 통과, `python3 -m unittest tests.test_web_app -k claim_coverage` → 21/21 통과.
- `python3 -m unittest tests.test_smoke -k entity` → 21/21 통과, `python3 -m unittest tests.test_web_app -k entity` → 55/55 통과. 기존 legacy-slot reload suggestion lock, focus-slot progress 직렬화, entity_card 요약 텍스트는 그대로 유지됩니다.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` → 이슈 없음.
- 브라우저 쪽은 suggestion ordering 외에 copy/selector/layout 변경이 없어 이번 라운드는 browser-visible contract를 넓히지 않았다고 판단해 full `make e2e-test` 및 isolated Playwright rerun을 실행하지 않았습니다. 브라우저 문자열과 layout은 기존 그대로입니다.

## 남은 리스크

- 새 `_REINVESTIGATION_SLOT_USER_PRIORITY`는 현재 Korean game/entity fixture 경험을 기반으로 한 고정 매핑입니다. 향후 다른 domain/entity family가 붙으면 이 map을 확장하거나 data-driven 구조로 바꿀 필요가 생길 수 있지만, 지금은 `CORE_ENTITY_SLOTS` 5개에 닫혀 있어 scope-out이 맞습니다.
- WEAK `sub_rank`는 `TRUSTED_CLAIM_SOURCE_ROLES` 바깥/빈 문자열을 동등하게 0으로 처리합니다. stored 엔트리에서 `source_role`이 legacy 미기록이면 untrusted로 취급되어 top-3에 더 잘 들어갑니다. 이는 legacy 미기록 = 신뢰도 증명 불가 로 안전측 해석이지만, 오래된 stored record 중 사실은 trusted source인 케이스가 있으면 순서가 달라집니다. 이번 라운드는 follow-up suggestion 순서에만 영향을 주고 카드 렌더링이나 progress summary에는 영향 없어 수용 가능 수준으로 판단했습니다.
- 이번 변경은 `core/agent_loop.py` 한 파일 안에서 닫았고 `core/web_claims.py`를 손대지 않았습니다. 다음에 같은 family의 다음 슬라이스 (예: `claim_coverage` 항목에 fragility signal을 명시 필드로 둔다) 가 필요해지면 그때 shared helper로 옮기는 것이 맞습니다.
- 더티 worktree(`docs/projectH_pipeline_runtime_docs/**`, `verify/4/9/**`, 그리고 untracked `report/gemini/2026-04-09-...`, `work/4/17/...default-cleanup.md`, `verify/4/17/...default-cleanup-verification.md`)는 이번 슬라이스와 무관해 그대로 두었습니다.
