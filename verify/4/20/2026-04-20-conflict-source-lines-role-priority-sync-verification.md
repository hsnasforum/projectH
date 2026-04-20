# 2026-04-20 conflict source lines role priority sync verification

## 변경 파일
- `verify/4/20/2026-04-20-conflict-source-lines-role-priority-sync-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-conflict-source-lines-role-priority-sync.md`)의 code 주장을 현재 tree와 대조하고, 날이 바뀌어 새 `verify/4/20/` 폴더에 오늘(2026-04-20) 전용 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 411 (`Conflict-aware 근거 출처 source-line helper + Agent-Loop role_priority sync`)는 Gemini advice 410이 지정한 두 가지 변경을 같은 라운드에 묶은 code-only 슬라이스였습니다: (1) `_build_entity_claim_source_lines` signature 확장과 iteration flattening에 `conflict_claims` bucket 포함, (2) `_entity_claim_sort_key`/`_build_entity_claim_source_lines` 두 hardcoded `role_priority` 맵을 `core/web_claims.py::_ROLE_PRIORITY` 쉬핑값으로 sync(DATABASE, COMMUNITY 추가 및 OFFICIAL/DESCRIPTIVE/NEWS 갱신).
- 이번 `/work`가 `core/agent_loop.py`와 `tests/test_smoke.py`의 정확한 범위 변경, step 4 grep으로 기존 assertion flip 필요 없음 확인, 새 focused regression(`-k coverage` 17 → 18 tests)을 주장했으므로, 각 변경이 현재 tree와 일치하고 scope_limit을 넘지 않았는지 이번 verify에서 고정해야 다음 control 선택이 안전합니다.
- 이 verify는 어제(2026-04-19) work에 대한 검증이지만 생성 시점은 오늘(2026-04-20)이므로 `verify/4/20/` 폴더에 저장했습니다. 어제의 `verify/4/19/` 선행 노트(`response-body-conflict-header-verification`)를 덮지 않고 날짜별 폴더 규약을 따릅니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `core/agent_loop.py:4130-4141` `_entity_claim_sort_key` hardcoded `role_priority` 맵이 이제 9-key로 완전 sync됐습니다: `{OFFICIAL: 5, WIKI: 4, DATABASE: 4, DESCRIPTIVE: 3, NEWS: 2, AUXILIARY: 1, COMMUNITY: 0, PORTAL: 0, BLOG: 0}`. 이전에 없던 `DATABASE`와 `COMMUNITY` key가 추가됐고 pre-elevation 값들이 업데이트됐습니다. 반환 tuple shape `(support_count, role_priority.get(...), confidence, len(value), value)`는 그대로입니다.
  - `core/agent_loop.py:4515-4524` `_build_entity_claim_source_lines` signature는 이제 `primary_claims, conflict_claims, weak_claims, supplemental_claims` 순서로 keyword-only 파라미터를 받습니다. `:4527` iteration은 `[*primary_claims, *conflict_claims, *weak_claims, *supplemental_claims]`로 네 bucket을 flatten합니다.
  - `core/agent_loop.py:4541-4551` hardcoded `role_priority` 맵도 같은 9-key 완전 sync로 바뀌었습니다. `support_refs.sort(key=lambda item: (role_priority.get(item[2], 0), len(item[1])), reverse=True)` sort 호출은 수정되지 않았습니다.
  - `core/agent_loop.py`의 `_build_entity_web_summary` 안 `_build_entity_claim_source_lines` 단일 callsite(`:4781+`)가 `conflict_claims=conflict_claims` 인자를 전달합니다.
  - `tests/test_smoke.py:1133-1204` `test_coverage_entity_card_source_line_includes_conflict_slot_source` regression이 추가됐습니다. seq 408 `test_coverage_entity_card_response_emits_conflict_section_header_when_conflict_slot_present` 바로 아래에 배치돼 coverage filter에 걸리며, conflict-slot source URL이 `근거 출처:` block에 실제로 나타나는지 + 그 URL이 primary/weak/supplemental 경로로는 이미 존재하지 않아 새 flattening을 실제로 exercise하는지 함께 고정합니다.
- `/work`가 기록한 step 4 grep(`rg -n "SourceRole\\.(OFFICIAL|WIKI|DATABASE|DESCRIPTIVE|NEWS)|근거 출처:|링크:" tests/test_smoke.py`)과 coverage/claims rerun 결과는 기존 assertion flip이 필요하지 않음을 정당하게 확인합니다. `_claim_sort_key`(core/web_claims.py)를 잠그는 seq 388/391/394/397 회귀들은 `_entity_claim_sort_key` 내부 sync와 독립이라 영향받지 않고, entity-card primary/source-line ordering을 old `_entity_claim_sort_key` 값으로 직접 고정한 기존 smoke assertion은 없었습니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - seq 408 `_build_entity_web_summary`의 `상충하는 정보 [정보 상충]:` 헤더 emit 블록과 seq 385/400/405 CONFLICT chain surface는 수정되지 않았습니다.
  - `core/agent_loop.py:5763-5776` regex canonicalization, `:5924-5939` alternate response builder, `core/web_claims.py::_ROLE_PRIORITY` 자체, `storage/web_search_store.py`, `app/serializers.py`, `app/static/contracts.js`, `app/static/app.js`, `app/static/style.css`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, 모든 `docs/*.md`는 이번 라운드에서 수정되지 않았습니다.
  - hardcoded map refactor into shared import of `_ROLE_PRIORITY`는 scope 확장 + 순환 import 위험 때문에 handoff에서 명시적으로 금지됐고, 이번 /work도 그 지시를 지켜 duplicate values를 유지했습니다.
- 오늘(2026-04-20) 기준 same-day same-family docs-only round count는 0입니다. 어제의 3회(seq 381 + seq 401 + seq 402)는 같은 날 기준 guard였고, 날이 바뀐 오늘은 fresh 상태로 재시작됩니다. 따라서 오늘 docs-only round 선택지도 다시 열려 있지만, 이번 seq 411은 code-only이므로 어느 방향이든 guard 압박이 없습니다.

## 검증
- 직접 코드 대조
  - 대상: `core/agent_loop.py:4130-4141`, `:4515-4557`, `:4781+`(_build_entity_web_summary callsite), `tests/test_smoke.py:1133-1204`, 참고용으로 `core/web_claims.py:32-42`(`_ROLE_PRIORITY`), seq 408이 emit한 `:4736-4762` 블록.
  - 결과: `/work`가 설명한 signature/flattening/role_priority/callsite 변경이 현재 tree와 일치하고, seq 408 CONFLICT 헤더 emit / 모든 다른 CONFLICT chain 관련 surface / `_ROLE_PRIORITY` 자체 / browser / docs는 실제로 untouched입니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: 이번 verify 독립 실행, `Ran 18 tests in 0.077s`, `OK`. seq 408 verify의 17건에서 이번 새 source-line 회귀 1건이 추가돼 18건이 됐습니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: 이번 verify 독립 실행, `Ran 5 tests in 0.001s`, `OK`. seq 397 이후 5건 변화 없음 — `_entity_claim_sort_key` sync가 `_claim_sort_key` 회귀들을 건드리지 않음을 재확인.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright 스위트: 이번 라운드는 Python helper signature 확장 + hardcoded map sync + focused smoke regression만 바꿨고 browser-visible shared helper/fixture/contract shape는 변경되지 않았습니다. `.claude/rules/browser-e2e.md`의 "isolated Playwright rerun 우선" 기준에서 생략이 truthful합니다.
  - 전체 `python3 -m unittest tests.test_web_app`: 이번 라운드는 `tests.test_web_app` 경로를 전혀 건드리지 않았고, 기존 실패 family(37 errors)는 어제 verify들에서 별도 dirty-state truth-sync 라운드 몫으로 분리돼 있습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared helper 변경도 없으므로 생략합니다.

## 남은 리스크
- Milestone 4 남은 sub-axis 후보는 여전히 pre-pinning이 필요합니다.
  - claim-coverage panel conflict surface extension (panel/status summary 경로는 seq 411에서도 여전히 conflict_claims를 discard하므로 panel-side CONFLICT 표현은 아직 추가되지 않음)
  - seq 408 response-body 헤더와 seq 411 source-line CONFLICT 확장용 optional Playwright scenario (new browser-emitted text가 transcript/history-card UX에서 드리프트 없이 렌더링되는지 end-to-end 확인)
  - source-role weighting 남은 tier tie: COMMUNITY(0) = PORTAL(0) = BLOG(0) 세분화 또는 weighting axis 완전 종료
  - reinvestigation trigger threshold / probe retry count 추가 tuning
  - strong-vs-weak-vs-unresolved separation beyond CONFLICT 추가 polish
- `/work`가 `rg -n "근거 출처|primary_claims|weak_claims|supplemental_claims" docs`로 확인한 바 root `docs/*.md`에는 helper scope를 3-bucket으로 직접 명시한 문장이 없었고, `docs/recycle/drafts/*`에만 일반 구조 언급이 있습니다. 이는 current-contract docs drift가 아니므로 docs-sync 후속 대상 아닙니다.
- 오늘 fresh 상태이므로 code-only, code+docs mixed, pure docs-only 중 어느 방향이든 열려 있습니다. 다만 선택할 때 어제 reset된 3회 guard가 오늘 다시 경고 임계에 접근하지 않도록, 만약 docs-only로 간다면 이번 하나만 하고 다음은 code로 돌리는 편이 안전합니다.
- 다음 슬라이스는 여러 후보 중 low-confidence prioritization이 있으므로, rule상 operator 전에 Gemini arbitration을 먼저 여는 편이 맞습니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
