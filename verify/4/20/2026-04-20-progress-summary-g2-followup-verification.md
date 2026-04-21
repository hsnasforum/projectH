# 2026-04-20 progress summary G2 followup verification

## 변경 파일
- `verify/4/20/2026-04-20-progress-summary-g2-followup-verification.md`

## 사용 skill
- `round-handoff`: seq 447 `.pipeline/claude_handoff.md`(G2-followup narrowed) 구현 주장을 `core/agent_loop.py`, `tests/test_smoke.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(`tests.test_smoke -k progress_summary/coverage/claims/reinvestigation`, sanity `tests.test_web_app` 단일 메서드, `py_compile`, `git diff --check`)을 직접 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 447 `.pipeline/claude_handoff.md`(Gemini 446 advice 기반 G2-followup narrowed)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-progress-summary-g2-followup.md`가 제출되었습니다.
- 목표는 `_build_claim_coverage_progress_summary`에 `trust_tier`/`support_plurality` 신호를 좁게 반영하되 (a) focus-slot improved→STRONG + mixed-trust 변주 문구와 (b) 비포커스 WEAK + multi-source label-token 교체만 진행하고, STRONG 비포커스 mixed-trust + focus-slot steady STRONG 두 축은 의도적으로 유예하는 것이었습니다. Server-only change. 클라이언트/serializer/Playwright/legend는 제외.

## 핵심 변경
- `core/agent_loop.py:4408-4416` 신규 helper `_claim_coverage_non_focus_summary_label(default_label, status, support_plurality)`
  - `status == CoverageStatus.WEAK and support_plurality == "multiple"` 일 때만 `"여러 출처 확인"` 반환, 그 외 `default_label` 그대로. trust-tier-aware 변주는 포함되지 않음을 확인(STRONG 비포커스 mixed-trust 유예 원칙 준수).
- `core/agent_loop.py:4446-4450` `current_trust_tier_map` 신규 comprehension
  - seq 441 `current_support_plurality_map`(`:4441-4445`) 바로 다음에 삽입됨. 같은 pattern(`canonical_current` 기반, slot 빈 문자열 guard)으로 정렬 유지. early-return guard(`:4451-4452`)는 `current_map`/`previous_map`만 확인하므로 trust map은 guard에 영향 없음.
- `core/agent_loop.py:4455-4457` 튜플 annotation
  - `improved_slots`/`regressed_slots`는 기존 5-tuple 유지(`(slot, prev_label, curr_label, prev_status, curr_status)`), `unresolved_slots`만 `list[tuple[str, str, str, str, str]]`로 4-tuple→5-tuple 확장됨.
- `core/agent_loop.py:4485-4498` `unresolved_slots` append
  - guard `{CONFLICT, WEAK, MISSING}` 그대로. STRONG 제외 원칙 고수. append에 `current_trust_tier_map.get(slot, "")`가 5번째 원소로 추가됨.
- `core/agent_loop.py:4502-4524` focus-slot improved loop, STRONG 분기
  - `:4509-4520` `cur_status == CoverageStatus.STRONG` arm이 이제 `focus_trust_tier = current_trust_tier_map.get(focus_slot, "")`를 먼저 읽고, `"mixed"`일 때 `"재조사 결과 {slot}은/는 {prev}에서 {curr}(으)로 보강되었으나 공식/위키/데이터 소스가 약합니다."` 문장을 반환. 그 외에는 기존 `"... 보강되어 신뢰할 만한 출처들의 교차 확인 기준을 충족했습니다."` 유지. 생성 regression과 일치.
  - 비STRONG improved arm(`:4521-4524`)는 변경 없음.
- `core/agent_loop.py:4525-4546` focus-slot regressed loop
  - 미변경 확인. seq 430 regressed wording 그대로.
- `core/agent_loop.py:4547-4567` focus-slot unresolved loop
  - `:4547` unpack이 `for slot, current_label, cur_status, cur_support_plurality, _cur_trust_tier in unresolved_slots:` 로 확장. CONFLICT(`:4549-4553`), WEAK(`:4554-4563`), MISSING(`:4564-4567`) 분기 내용은 seq 441과 동일. trust tier는 focus unresolved path에서 사용되지 않음(narrowing 결정).
- `core/agent_loop.py:4569-4580` 비포커스 combined `improved + unresolved` fallback
  - `:4576-4577` comprehension이 `for slot, label, status, plurality, _trust_tier in unresolved_slots[:2]` 로 확장됐고, 각 항목의 label token을 `self._claim_coverage_non_focus_summary_label(label, status, plurality)`로 교체. 전체 문장 템플릿 `"재조사 결과 {improved_summary}로 보강되었습니다. 아직 {unresolved_summary} 상태의 슬롯이 남아 있습니다."` 그대로.
  - `improved_summary` comprehension(`:4570-4573`)은 3-tuple로 잘라낸 기존 5-tuple unpack 유지, label token 미변경.
- `core/agent_loop.py:4582-4587` 비포커스 bare-unresolved fallback
  - 동일한 helper call로 label token 교체. 전체 문장 템플릿 `"재조사했지만 아직 {unresolved_summary} 상태입니다."` 그대로.
- `tests/test_smoke.py` 신규 회귀 `test_build_claim_coverage_progress_summary_surfaces_mixed_trust_focus_strong_and_non_focus_weak_multi_source`
  - seq 441 `test_build_claim_coverage_progress_summary_focus_slot_weak_multi_source_emits_multi_source_wording` 바로 다음에 배치. 3 fixture(focus STRONG mixed-trust improvement / focus STRONG trusted improvement / non-focus WEAK multi-source token swap) 한 메서드에 고정.
- 서버/클라 외곽 shipped 표면 보존
  - `_build_entity_claim_coverage_items`(seq 438), `_claim_coverage_status_label`, seq 441/444 serializer keys(`app/serializers.py:970-971`), seq 441 `"단일 출처"` 클라이언트 분기, seq 444 `"교차 확인"` 클라이언트 분기, seq 441/444 Playwright scenarios, legend(`app/static/app.js:2518-2519`) 전부 미편집. grep 결과와 `git diff --check` 출력 0건으로 확인.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `447` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 448.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `445` — seq 446 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `446` — seq 447 handoff로 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — shipping으로 자연 해제 유지. real operator-only blocker 없음.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 9 tests in 0.014s`, `OK`. handoff 기대치(8 → 9) 정합. 새 focus STRONG mixed + non-focus WEAK multi 회귀 green.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 25 tests in 0.044s`, `OK`. handoff baseline 24에서 25로 증가. 새 test name에 `claim_coverage`가 포함되어 `-k coverage` subset에도 매칭됨. `/work`가 이 점을 이미 명시.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`. seq 427 baseline 유지.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.087s`, `OK`. seq 423 baseline 유지.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.051s`, `OK`. seq 441 single-source fixture가 `_claim_coverage_non_focus_summary_label`에서 default_label을 받아 기존 문구 유지. 부분 문자열 assertion 녹색 유지 확인.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `node --check app/static/app.js`, Playwright, `make e2e-test`, full `tests.test_web_app`는 이번 라운드가 server-only이고 browser helper/contract를 넓히지 않아 의도적으로 생략.

## 남은 리스크
- **STRONG 비포커스 mixed-trust 비노출 유지**: non-focus summary는 여전히 STRONG mixed-trust slot을 침묵합니다. 이번 라운드에서 `mixed_trust_slots` 신규 collection/`unresolved_slots` 확장 둘 다 결정 유예. 후속 arbitration에서 어느 shape가 안전한지 다시 평가해야 합니다.
- **focus-slot steady STRONG mixed-trust 비노출 유지**: rank-change 없는 focus STRONG에도 mixed-trust 변주가 없습니다. advice 446이 명시적으로 요구하지 않아 이번 라운드에 포함하지 않았고, 후속 판단으로 남습니다.
- **다음 슬라이스 ambiguity**: 위 두 유예 조각 외에 G3(reinvestigation threshold) / G4(`_role_confidence_score`) / G5(`tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state) / G6(broader `tests.test_web_app` family) / G7(`REASON_CODE` / `OPERATOR_POLICY` vocabulary) / G8(memory-foundation) 후보는 축이 서로 다르고 dominant current-risk reduction이 없습니다. 따라서 next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 448)로 G2-followup 잔여 조각 vs G3..G8 사이 중재를 여는 편이 `/verify` README 규칙과 맞습니다.
- **unrelated red tests 잔존**: 전체 `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 G5/G6 후보로 그대로 남아 있고 이번 라운드에서 재판정하지 않았습니다.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 그대로. server-only change라 docs drift 유발 없음. 같은 family docs-only 반복 3회 이상 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files(`controller/`, `pipeline_runtime/`, `pipeline_gui/`, `storage/`, `docs/`, 과거 `/work`/`/verify` 노트)는 그대로. 이번 라운드는 해당 파일들을 건드리지 않았습니다.
