# 2026-04-19 response body conflict header verification

## 변경 파일
- `verify/4/19/2026-04-19-response-body-conflict-header-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-response-body-conflict-header.md`)의 code+docs 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`focus-slot-weak-missing-wording-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 408 (`Response-body [정보 상충] tag emission — code + docs ripple slice`)은 Gemini advice 407을 따라 `_select_entity_fact_card_claims`에 `conflict_claims` bucket을 추가하고, 해당 bucket을 entity-card response builder에서 `상충하는 정보 [정보 상충]:` 헤더 section으로 emit하며, 같은 라운드에서 3개 문서 문장(ACCEPTANCE_CRITERIA:49, PRODUCT_SPEC:347/370)을 동기화하는 code+docs mixed 슬라이스였습니다.
- 이번 `/work`가 5-tuple 반환 전환, 3개 callsite 전부 새 shape로 unpack, response builder가 CONFLICT 슬롯 존재 시에만 헤더 emit, 3개 문서 문장 sync, 새 focused regression(`-k coverage` 17 tests로 +1) 추가를 주장했으므로, 각 변경이 현재 tree와 일치하고 scope_limit을 넘지 않았는지 이번 verify에서 고정해야 다음 control 선택이 안전합니다.
- 선행 verify(`focus-slot-weak-missing-wording-verification`)는 seq 405 WEAK/MISSING wording 라운드 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `core/agent_loop.py:4148-4218` `_select_entity_fact_card_claims`가 이제 `(primary_claims, conflict_claims, weak_claims, supplemental_claims, unresolved_slots)` 5-tuple을 반환합니다. 핸드오프가 지정한 `primary` 다음, `weak` 앞 순서로 `conflict_claims`가 들어갔습니다.
  - 세 callsite가 새 shape에 맞춰 unpack됐습니다:
    - `core/agent_loop.py:4696` response builder: `primary_claims, conflict_claims, weak_claims, supplemental_claims, unresolved_slots = self._select_entity_fact_card_claims(...)` (모든 5개 소비).
    - `core/agent_loop.py:6236` panel/status summary 경로: `primary_claims, _, weak_claims, _, _ = self._select_entity_fact_card_claims(...)`.
    - `core/agent_loop.py:6510` panel/status summary 경로: 같은 discard 패턴.
  - `core/agent_loop.py:4695-4762`의 실제 entity-card response 생성 함수(handoff에 적힌 이름은 `_build_entity_card_response`였지만 현재 코드상 owner는 `_build_entity_web_summary`)가 `conflict_claims`가 비어있지 않을 때 strong section 뒤, weak section 앞에 `"상충하는 정보 [정보 상충]:"` 헤더 + 본문 bullet(`정보 상충, {role_label}, 확정 금지` qualifier 포함)을 emit합니다. 비어있으면 헤더 section을 생략합니다. 핸드오프의 "STRONG과 WEAK 사이, 비어있을 때 미emit" 조건과 정합합니다.
  - `core/agent_loop.py:5763-5776` regex legacy canonicalization, `:5924-5939` alternate response builder, `core/web_claims.py` conflict emission, `storage/web_search_store.py`, `app/serializers.py`, `app/static/contracts.js`, `app/static/app.js`, `app/static/style.css`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, 그리고 `_ROLE_PRIORITY` 전체는 핸드오프 지시대로 수정되지 않았습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:49`가 새 4-tag enumerated list(`확인된 사실 [교차 확인]:`, `상충하는 정보 [정보 상충]:`, `단일 출처 정보 [단일 출처] (추가 확인 필요):`, `확인되지 않은 항목 [미확인]:`)로 확장됐고 기존 "does not emit a dedicated `[정보 상충]` response-body header tag; ..." trailing clause는 핸드오프 지시대로 삭제됐습니다. "emits" 표현은 자연스럽게 "The claim-coverage panel hint maps each emitted tag to its explanation..." 문장으로 커버됩니다.
  - `docs/PRODUCT_SPEC.md:347`이 `(확인된 사실 [교차 확인], 상충하는 정보 [정보 상충], 단일 출처 정보 [단일 출처], 확인되지 않은 항목 [미확인])` 4-tag enumeration으로 확장됐습니다.
  - `docs/PRODUCT_SPEC.md:370`이 `([교차 확인], [정보 상충], [단일 출처], [미확인])` 4-tag로 확장됐습니다.
  - `tests/test_smoke.py:1038-1131`에 `test_coverage_entity_card_response_emits_conflict_section_header_when_conflict_slot_present`가 추가됐습니다. CONFLICT fixture에서 `상충하는 정보 [정보 상충]:` 헤더 emit + identifiable conflict value 노출 + STRONG(있을 때) < CONFLICT < WEAK(있을 때) 순서 검증, 그리고 no-CONFLICT fixture에서 헤더 미emit를 모두 잠급니다.
- `/work`가 기록한 audit도 정합합니다.
  - `rg -n "_select_entity_fact_card_claims\\(" tests/test_smoke.py` 결과: smoke 안에 old 4-tuple unpack assertion이 없어 추가 test 조정이 필요하지 않았습니다. 기존 3-section response-body assertion도 no-conflict fixture 기준이라 새 conflict 헤더 추가로 깨지지 않았습니다.
  - `rg -n 'verified-vs-uncertain explanation|Response-body section headers|\\[교차 확인\\].*\\[단일 출처\\].*\\[미확인\\]|...' docs` 결과: 이번 라운드 target 3문장 외에 3-tag로 남은 response-body enumeration hit가 보이지 않았습니다. 다른 markdown 파일(`docs/ARCHITECTURE.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/project-brief.md`)은 response-body emitted header/tag enumeration을 직접 적지 않으므로 추가 drift가 생기지 않았고 이번 라운드 docs 수정 범위 외로 안전하게 유지됐습니다.
- 같은 날 same-family docs-only round count는 seq 381 + seq 401 + seq 402로 여전히 3입니다. 이번 seq 408은 code+docs mixed round라 docs-only count를 늘리지 않습니다. `3+ docs-only same-family` guard는 넘지 않았습니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `core/agent_loop.py:4148-4218`, `:4695-4762`, `:4696/6236/6510`, `:4736-4762`(새 emit 블록), `tests/test_smoke.py:1038-1131`, `docs/ACCEPTANCE_CRITERIA.md:49`, `docs/PRODUCT_SPEC.md:347/370`.
  - 결과: `/work`가 설명한 code+docs 변경이 현재 tree와 일치하고, 의도한 untouched 영역(regex canonicalization, alternate builder, CONFLICT chain 나머지 surface, `_ROLE_PRIORITY`, 다른 markdown 파일, `tests/test_web_app.py`, `e2e`)는 실제로 그대로입니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: 이번 verify 독립 실행, `Ran 17 tests in 0.063s`, `OK`. seq 405 verify의 16건에서 새 CONFLICT 헤더 회귀 1건이 추가돼 17건이 됐습니다.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: 이번 verify 독립 실행, `Ran 5 tests in 0.000s`, `OK`. seq 397 이후 5건 변화 없음.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright 스위트: 이번 라운드는 server-emitted response-body 텍스트에 새 섹션을 추가했고 browser-visible shared helper/fixture/contract shape 자체는 건드리지 않았습니다. `.claude/rules/browser-e2e.md`의 "isolated Playwright rerun 우선" 기준 아래에서 smoke regression이 이미 heading emission을 잠갔으므로 Playwright 생략이 truthful합니다. /work가 남긴 "optional Playwright scenario"는 future candidate로 유지.
  - 전체 `python3 -m unittest tests.test_web_app`: 이번 라운드는 `tests.test_web_app` 경로를 전혀 건드리지 않았고, 기존 실패 family(37 errors)는 선행 verify들에서 별도 dirty-state truth-sync 라운드 몫으로 분리돼 있습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared browser helper 변경도 없으므로 생략합니다.

## 남은 리스크
- `/work`가 정확히 짚은 후속 후보들이 여전히 남아 있습니다.
  - `근거 출처:` source-line helper는 여전히 `primary_claims`, `weak_claims`, `supplemental_claims`만 직접 참조합니다. conflict bullet과 source-line의 1:1 대응을 더 분명히 하려면 별도 narrow slice가 필요합니다(response-body에는 상충 bullet이 나타나지만 해당 conflict source가 출처 라인에 빠질 가능성 차단용).
  - claim-coverage panel 계산 경로(line 6236/6510 callsite 쪽)는 conflict_claims를 discard하고 있어, panel의 `rendered_as` 또는 richer wording에서 conflict slot이 별도 표면 없이 unresolved bucket에만 묶여 있습니다. 추가 panel-surface 라운드 후보.
  - 새 response-body 헤더가 실제 transcript/history card UX에서 별도 copy/layout drift 없이 읽히는지는 별도 browser rerun(Playwright scenario)에서 추가 확인하는 편이 안전합니다. 이는 새 user-visible browser-emitted text이기 때문에 future bounded Playwright 라운드로 남기기 적합합니다.
- Milestone 4 남은 sub-axis(COMMUNITY/PORTAL/BLOG weighting, 추가 reinvestigation threshold/probe cap tuning, strong-vs-weak-vs-unresolved further polish beyond CONFLICT)는 여전히 separate future code round 후보이며 각각 file+surface+boundary pre-pinning이 필요합니다.
- 같은 날 same-family docs-only round count는 3 유지. 오늘 더 이상 pure docs-only round는 허용되지 않습니다. code-only 또는 code+docs mixed 라운드로만 진행 가능.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
- 다음 슬라이스는 위 여러 후보 중 어느 것을 고를지에 대한 low-confidence prioritization 상황이므로, rule상 operator 전에 Gemini arbitration을 먼저 여는 편이 맞습니다.
