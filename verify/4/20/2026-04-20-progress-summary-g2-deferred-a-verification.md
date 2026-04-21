# 2026-04-20 progress summary G2-deferred-A verification

## 변경 파일
- `verify/4/20/2026-04-20-progress-summary-g2-deferred-a-verification.md`

## 사용 skill
- `round-handoff`: seq 450 `.pipeline/claude_handoff.md`(G2-deferred-A, Gemini 449 advice Option (i)) 구현 주장을 `core/agent_loop.py`, `tests/test_smoke.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(`tests.test_smoke -k progress_summary/coverage/claims/reinvestigation`, sanity `tests.test_web_app` 단일 메서드, `py_compile`, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 450 `.pipeline/claude_handoff.md`(Gemini 449 advice 기반 G2-deferred-A Option (i))가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-progress-summary-g2-deferred-a.md`가 제출되었습니다.
- 목표는 `_build_claim_coverage_progress_summary`의 두 비포커스 fallback이 STRONG + `trust_tier == "mixed"` 슬롯을 새 `mixed_trust_slots` collection을 통해 surfacing하되, `unresolved_slots` guard/semantic은 그대로 두고 문장 템플릿도 verbatim으로 유지하는 것이었습니다. G2-deferred-B(focus-slot steady STRONG)는 defer 상태 유지.

## 핵심 변경
- `core/agent_loop.py:4408-4419` helper `_claim_coverage_non_focus_summary_label` 확장
  - 시그니처가 `(self, default_label, status, support_plurality, trust_tier)`로 4-인자 확장됨.
  - `:4415-4416` 기존 WEAK + multiple 분기 그대로.
  - `:4417-4418` 신규 `status == CoverageStatus.STRONG and trust_tier == "mixed"` 분기가 `"교차 확인(출처 약함)"`을 반환함. handoff 지시의 exact literal과 일치.
  - `:4419` default `return default_label`. trusted STRONG은 여전히 `default_label`(= `"교차 확인"`)로 통과해 기존 summary와 동일하게 보임.
- `core/agent_loop.py:4449-4453` `current_trust_tier_map` (seq 447 추가분) 그대로 유지.
- `core/agent_loop.py:4458-4461` collection annotations
  - `improved_slots`/`regressed_slots`/`unresolved_slots`는 seq 447의 5-tuple annotation 유지.
  - `:4461` 신규 `mixed_trust_slots: list[tuple[str, str, str, str, str]] = []`가 `unresolved_slots` 바로 다음 위치에 삽입됨.
- `core/agent_loop.py:4462-4515` `CORE_ENTITY_SLOTS` 루프
  - `:4489-4502` unresolved guard `{CONFLICT, WEAK, MISSING}` 그대로. STRONG 미포함. seq 447 원칙 준수.
  - `:4503-4515` 신규 `if current_status == CoverageStatus.STRONG and current_trust_tier_map.get(slot, "") == "mixed":` 가드가 unresolved append 이후에 삽입돼 `mixed_trust_slots`에 동일 5-tuple shape(`slot`, `status_label`, `status`, `support_plurality`, `trust_tier`)로 append. 이중 append가 발생하지 않음을 루프 구조(두 guard가 서로 배타적 상태)로 확인.
- `core/agent_loop.py:4517-4584` focus-slot 루프 3종
  - seq 441+447 shipped 분기 그대로. focus-slot은 `mixed_trust_slots`를 소비하지 않아, focus match가 있는 경로에서는 이번 변경의 effect가 없음을 확인.
- `core/agent_loop.py:4586-4598` 비포커스 improved + unresolved fallback (site D)
  - `:4591` `combined_unresolved_slots = unresolved_slots + mixed_trust_slots` 순서 고정 (unresolved 먼저).
  - `:4592-4595` 이전 `if unresolved_slots:` 대신 `if combined_unresolved_slots:` 사용. comprehension이 5-tuple unpack (`slot, label, status, plurality, trust_tier`)으로 확장됐고 helper 호출에 `trust_tier` 인자 추가됨.
  - `:4597` 문장 템플릿 `"재조사 결과 {improved_summary}로 보강되었습니다. 아직 {unresolved_summary} 상태의 슬롯이 남아 있습니다."` verbatim 유지.
- `core/agent_loop.py:4600-4607` 비포커스 bare-unresolved fallback (site E)
  - `:4600` 동일한 결합 순서.
  - `:4601-4604` 동일한 helper 호출 확장.
  - `:4606` 문장 템플릿 `"재조사했지만 아직 {unresolved_summary} 상태입니다."` verbatim 유지.
  - `:4607` `return None` tail 유지.
- `tests/test_smoke.py` 신규 회귀 `test_build_claim_coverage_progress_summary_surfaces_non_focus_strong_mixed_trust_via_combined_summary`
  - seq 447 regression 바로 다음 위치. bare-unresolved path에서 genuine unresolved slot이 mixed-trust slot보다 먼저 오고 mixed-trust slot이 `"개발 교차 확인(출처 약함)"`으로 surfacing되는지 고정. `rg` hit(helper return 1 + regression assertion 2)로 `/work` 문구와 일치 확인.
- 외곽 shipped 표면 보존
  - seq 441/444 serializer keys, seq 441 `"단일 출처"` 클라 분기, seq 444 `"교차 확인"` 클라 분기, seq 441/444 Playwright scenarios, legend(`app/static/app.js:2518-2519`), `status_label` 4-literal set 모두 미편집. `git diff --check` 0건 출력.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `450` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 451.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `448` — seq 449 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `449` — seq 450 handoff로 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — shipping으로 자연 해제 유지. real operator-only blocker 없음.
- `/work` 노트의 step 7 grep drift 처리
  - `rg -n "if unresolved_slots:" core/agent_loop.py`가 site D/E에서는 0건이지만 파일 다른 위치에서 1건 hit(`:4867` 부근, `_select_entity_fact_card_claims` 또는 인접 helper). `/work`가 솔직하게 "target 범위 밖 기존 코드라 건드리지 않았다"고 기록해 handoff 기대치(ZERO post-edit)와의 차이가 투명하게 남아 있습니다. 이번 slice 범위에서는 문제 없음 — 해당 hit은 다른 helper 내부의 별개 `unresolved_slots`로, 이름만 같고 semantically 분리되어 있습니다.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 10 tests in 0.013s`, `OK`. handoff 기대치(9 → 10) 정합.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 26 tests in 0.045s`, `OK`. 새 test name에 `claim_coverage_progress_summary`가 포함돼 `-k coverage` subset에도 매칭됨. handoff/working 조건부 허용 조건과 일치.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.000s`, `OK`. seq 427 baseline 유지.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.048s`, `OK`. seq 423 baseline 유지.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.058s`, `OK`. step 6 critical sanity green. seq 441 partial-match 어서션이 helper 확장 후에도 유지됨을 확인 — 해당 fixture의 비포커스 STRONG 슬롯에 `trust_tier == "mixed"`가 없거나, `[:3]` slice 내에서 genuine unresolved 엔트리가 mixed-trust 보다 앞서서 기존 assertion target 문자열이 살아남았음을 의미.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `node --check app/static/app.js`, Playwright, `make e2e-test`, full `tests.test_web_app`는 이번 라운드가 server-only이고 shared browser helper/contract를 넓히지 않아 의도적으로 생략.

## 남은 리스크
- **G2-deferred-B 잔존**: focus-slot steady STRONG mixed-trust(no rank change)는 summary에서 여전히 silent. 새 focus-slot 분기가 필요하며 다음 arbitration 후보.
- **Sentence template 어색함**: mixed-only 요약에서 `"재조사했지만 아직 개발 교차 확인(출처 약함) 상태입니다"`처럼 "교차 확인"이 "상태"로 수식되는 구조가 의미적으로 어색. 이번 라운드는 advice 449의 combined-list 접근을 수용해 trade-off 받아들였음. 사용자 피드백이 강하면 후속 β arbitration에서 template 재설계 필요.
- **기타 `if unresolved_slots:` hit 잔존**: `core/agent_loop.py:4867` 부근의 별개 `unresolved_slots` 이름 사용은 이번 slice와 무관한 기존 코드. `/work`가 투명하게 기록했고 slice 범위 밖 처리 맞음. 이름 collision을 줄이고 싶으면 별도 리팩터링 arbitration 필요.
- **다음 슬라이스 ambiguity**: 남은 G 후보(G2-deferred-B, G3 reinvestigation threshold, G4 `_role_confidence_score`, G5 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state, G6 broader `tests.test_web_app` family first red-cell, G7 canonical `REASON_CODE`/`OPERATOR_POLICY` vocabulary, G8 memory-foundation)는 축이 서로 다르고 dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 451)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests 잔존**: 전체 `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 G5/G6 후보로 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 그대로. server-only change라 docs drift 유발 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드에서 건드리지 않음.
