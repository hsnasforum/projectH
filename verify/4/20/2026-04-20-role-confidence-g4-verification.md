# 2026-04-20 role confidence G4 verification

## 변경 파일
- `verify/4/20/2026-04-20-role-confidence-g4-verification.md`

## 사용 skill
- `round-handoff`: seq 456 `.pipeline/claude_handoff.md`(G4 `role_confidence` 튜닝, Gemini 455 advice) 구현 주장을 `core/agent_loop.py`, `tests/test_smoke.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(`tests.test_smoke -k claims/coverage/progress_summary/reinvestigation`, 신규 회귀 단독 재실행, sanity `tests.test_web_app` 단일 메서드, `py_compile`, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 456 `.pipeline/claude_handoff.md`(Gemini 455 advice 기반 G4)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-role-confidence-g4.md`가 제출되었습니다.
- 목표는 `_build_entity_claim_records`의 inline `role_confidence` 맵을 `_ROLE_PRIORITY`(OFFICIAL:5, WIKI:4, DATABASE:4)와 정합하도록 OFFICIAL↔WIKI swap + DATABASE explicit key 추가만 수행하고, 나머지 키/fallback/모든 다른 helper는 비편집으로 유지하는 것이었습니다.

## 핵심 변경
- `core/agent_loop.py:4103-4112` `role_confidence` map
  - `:4104` `SourceRole.OFFICIAL: 0.95` (이전 `0.9`)
  - `:4105` `SourceRole.WIKI: 0.9` (이전 `0.95`)
  - `:4106` `SourceRole.DATABASE: 0.9` (신규; 이전엔 explicit key 없이 `.get(source_role, 0.4)` fallback으로 떨어짐)
  - `:4107-4112` `DESCRIPTIVE: 0.75`, `NEWS: 0.55`, `PORTAL: 0.45`, `BLOG: 0.35`, `AUXILIARY: 0.4`, fallback `.get(source_role, 0.4)` 모두 그대로 유지. key 순서는 OFFICIAL → WIKI → DATABASE → 기존 순서로 편집(handoff가 허용한 stylistic reorder 범위).
  - COMMUNITY는 여전히 map에 없고 fallback `0.4`로 유지. `_ROLE_PRIORITY`가 COMMUNITY를 AUXILIARY와 같은 tier-1에 두어 값은 우연히 맞지만 explicit key 추가는 scope 밖이라 제외.
- 맵 아래 `confidence=role_confidence` 할당(`:4126`)과 `ClaimRecord` 생성부 미변경 확인.
- `_entity_claim_sort_key`(`core/agent_loop.py:4130-4141`) / `_ROLE_PRIORITY`(`core/web_claims.py:32-42`) / `_claim_sort_key`(`core/web_claims.py:61-69`) 전부 미편집. seq 420 / seq 427 계약 유지.
- `trust_tier` derivation은 여전히 `{OFFICIAL, DATABASE, WIKI}` 집합 기반이고 `confidence`를 읽지 않음을 재확인. 이번 slice는 set-based trust_tier 추론과 무관.
- `tests/test_smoke.py:2600-2645` 신규 회귀 `test_build_entity_claim_records_role_confidence_aligns_with_role_priority_hierarchy`
  - `loop._entity_source_role_label`과 `_extract_entity_source_fact_bullets`를 lambda로 monkey-patch해서 OFFICIAL/WIKI/DATABASE 각각의 forced_role을 주입, `_build_entity_claim_records`가 반환한 `ClaimRecord.confidence`를 role 기준으로 dict로 모아 `0.95 / 0.9 / 0.9` equality를 고정하고 `OFFICIAL > WIKI` / `WIKI == DATABASE` 불변식까지 한 메서드에서 검증.
  - 배치는 `test_coverage_reinvestigation_overall_cap_is_now_5` 다음 위치이며 `_build_entity_claim_records`를 쓰는 cluster 인접성 유지. `/work` 문구와 일치.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453 shipped 표면 전부 미편집 확인. serializer, client branches, Playwright scenarios, legend, `status_label` 4-literal set, `_build_claim_coverage_progress_summary`의 focus/비포커스 분기와 helper `_claim_coverage_non_focus_summary_label` 모두 그대로.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `456` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 457.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `454` — seq 455 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `455` — seq 456 handoff로 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — shipping으로 자연 해제 유지. real operator-only blocker 없음.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.000s`, `OK`. 새 test name(`role_confidence_aligns_with_role_priority_hierarchy`)에는 `claims` substring이 없어 count baseline 7 유지. `/work` 관측과 일치.
- `python3 -m unittest tests.test_smoke.SmokeTest.test_build_entity_claim_records_role_confidence_aligns_with_role_priority_hierarchy`
  - 결과: `Ran 1 test in 0.000s`, `OK`. 신규 회귀 직접 타겟 재실행 green.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.057s`, `OK`. seq 453 baseline 유지.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.014s`, `OK`. seq 453 baseline 유지.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.055s`, `OK`. seq 423 baseline 유지.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.061s`, `OK`. confidence float 조정이 sort-key tier-3 tiebreak에만 영향 주고 이 테스트의 assertion에는 전파되지 않음을 확인.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- Playwright, `make e2e-test`, full `tests.test_web_app`는 이번 라운드가 server-only이고 shared browser helper/contract를 넓히지 않아 의도적으로 생략.

## 남은 리스크
- **COMMUNITY implicit parity**: COMMUNITY는 `role_confidence` explicit key 없이 `0.4` fallback으로 남습니다. `_ROLE_PRIORITY`의 tier-1(AUXILIARY와 parity)과 값은 일치하지만 implicit. 후속 슬라이스에서 가독성/lint 관점으로 explicit 추가 검토 가능.
- **property-style invariant 부재**: `role_confidence`가 `_ROLE_PRIORITY` ordering을 반드시 따라야 한다는 runtime/test enforcement는 없습니다. 이번 회귀는 OFFICIAL/WIKI/DATABASE 3건에 대한 point assertion. 일반화된 invariant test는 별도 후속 candidate.
- **다음 슬라이스 ambiguity**: G3(`prefer_probe_first` threshold), G5(`tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state), G6(broader `tests.test_web_app` first red-cell), G7(`REASON_CODE`/`OPERATOR_POLICY` vocabulary), G8(memory-foundation), G9(`if unresolved_slots:` naming-collision cleanup)는 축이 서로 다르고 dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 457)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests 잔존**: 전체 `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 G5/G6 후보로 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 그대로. server-only change라 docs drift 유발 없음. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 해당 파일들을 건드리지 않았습니다.
