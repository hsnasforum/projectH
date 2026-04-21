# 2026-04-20 progress summary G2-deferred-B verification

## 변경 파일
- `verify/4/20/2026-04-20-progress-summary-g2-deferred-b-verification.md`

## 사용 skill
- `round-handoff`: seq 453 `.pipeline/claude_handoff.md`(G2-deferred-B, Gemini 452 advice) 구현 주장을 `core/agent_loop.py`, `tests/test_smoke.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(`tests.test_smoke -k progress_summary/coverage/claims/reinvestigation`, sanity `tests.test_web_app` 단일 메서드, `py_compile`, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 453 `.pipeline/claude_handoff.md`(Gemini 452 advice 기반 G2-deferred-B)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-progress-summary-g2-deferred-b.md`가 제출되었습니다.
- 목표는 focus slot이 steady STRONG(rank-change 없음)이면서 `trust_tier == "mixed"`인 경우를 새 focus-slot 분기 하나로 server summary에 surfacing하고, 다른 focus/non-focus 경로는 건드리지 않는 것이었습니다. Server-only slice.

## 핵심 변경
- `core/agent_loop.py:4585-4592` 신규 focus-slot steady STRONG mixed-trust 분기
  - `:4585-4588` guard `if current_map.get(focus_slot, "") == CoverageStatus.STRONG and current_trust_tier_map.get(focus_slot, "") == "mixed":` — handoff가 지시한 narrowed form 그대로(중복 `if focus_slot:` 제거, `.get(..., "")` 안전 default 유지).
  - `:4589-4592` return `"재조사했지만 {focus_slot}{focus_particle} 교차 확인 기준은 충족하지만 공식/위키/데이터 소스가 약합니다."` — advice 452 literal 정확히 일치.
  - 들여쓰기는 `if focus_slot:`(`:4517`) 블록 내부의 세 focus 루프(`:4519`, `:4542`, `:4564`)와 같은 한 단계. 즉 for 루프 본문보다 한 단계 얕음. `focus_particle`(`:4518`)은 이 블록에서 이미 바인딩되어 있어 재사용됐고 추가 유도는 없음.
  - 삽입 위치는 unresolved focus loop final MISSING return(`:4581-4584`) 직후, `if improved_slots:`(`:4594`) 직전. handoff가 명시한 exact 위치와 일치.
- `core/agent_loop.py:4594-4609` 비포커스 fallbacks 미변경 확인
  - seq 450 combined-list 소비(`combined_unresolved_slots = unresolved_slots + mixed_trust_slots`, helper call with `trust_tier`)와 문장 템플릿 두 건 그대로. 이번 슬라이스가 fall-through 경로를 건드리지 않았음.
- seq 441/447/450 shipped 표면 보존
  - focus WEAK `"multiple"` 분기(`:4571-4579`), focus improved→STRONG mixed-trust variant(`:4526-4541`), helper `_claim_coverage_non_focus_summary_label`(`:4408-4419`), `mixed_trust_slots` 선언/append(`:4461`, `:4503-4515`) 등 전부 미편집. grep + `git diff --check` 0건 출력.
- `tests/test_smoke.py:3355-3384` 신규 regression `test_build_claim_coverage_progress_summary_focus_slot_steady_strong_mixed_trust_emits_mixed_trust_wording`
  - `query = "붉은사막 개발 상황 알려줘"`, `loop._entity_slot_from_probe_text(query) == "개발"` assertEqual로 매핑을 직접 고정. fixture는 previous/current 모두 `개발 STRONG`, current에는 `trust_tier="mixed"`, `support_plurality="multiple"`.
  - `assertEqual`로 exact sentence 문자열을 `focus_slot`/`focus_particle`과 결합해 비교, `assertNotIn("아직", result)`로 pre-slice non-focus fallback이 아니라 새 focus branch가 반환됐음을 검증. `/work`가 적은 구조와 일치.
  - 배치는 seq 450 regression(`:3322-3353`) 바로 다음(`:3355+`). `/work`의 인접 배치 주장과 정합.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `453` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 454.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `451` — seq 452 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `452` — seq 453 handoff로 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — shipping으로 자연 해제 유지. real operator-only blocker 없음.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.014s`, `OK`. handoff 기대치(10 → 11) 정합.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.056s`, `OK`. 새 test name에 `claim_coverage_progress_summary` 포함 → `-k coverage`에도 매칭돼 26 → 27. `/work` 기록과 일치.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`. seq 427 baseline 유지.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.051s`, `OK`. seq 423 baseline 유지.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.060s`, `OK`. 해당 fixture의 focused slot은 steady STRONG + mixed 조합이 아니라서 새 분기가 fire되지 않고 기존 `"한 가지 출처의 정보로만 확인됩니다"` partial-match가 그대로 통과했음을 확인.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `node --check app/static/app.js`, Playwright, `make e2e-test`, full `tests.test_web_app`는 이번 라운드가 server-only이고 shared browser helper/contract를 넓히지 않아 의도적으로 생략.

## 남은 리스크
- **progress_summary mixed-trust matrix complete**: G2-deferred-B 닫힘으로 focus improved→STRONG / focus steady STRONG / non-focus STRONG 세 mixed-trust 표면이 모두 커버됨. 현재 indicator set 기준 server summary 측 mixed-trust 매트릭스는 complete.
- **다음 슬라이스 ambiguity 잔존**: 남은 후보 G3(reinvestigation `prefer_probe_first` threshold), G4(`_role_confidence_score` 가중치), G5(`tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state), G6(broader `tests.test_web_app` first red-cell), G7(canonical `REASON_CODE`/`OPERATOR_POLICY` vocabulary), G8(memory-foundation), G9(`if unresolved_slots:` 이름 충돌 정리)는 축이 서로 다르고 dominant current-risk reduction 부재. 따라서 next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 454)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests 잔존**: 전체 `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 G5/G6 후보로 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 그대로. server-only change라 docs drift 유발 없음. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 해당 파일들을 건드리지 않았습니다.
