# 2026-04-20 claim coverage internal trust support fields verification

## 변경 파일
- `verify/4/20/2026-04-20-claim-coverage-internal-trust-support-fields-verification.md`

## 사용 skill
- `round-handoff`: seq 438 `.pipeline/claude_handoff.md`(Gemini 437 advice 기반 E2b-α)의 구현 주장을 `core/agent_loop.py`, `tests/test_smoke.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(`-k coverage` primary + progress_summary/claims/reinvestigation sanity + `py_compile` + `git diff --check`)을 직접 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 438 `.pipeline/claude_handoff.md`(Gemini 437 advice E2b-α 기반)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-claim-coverage-internal-trust-support-fields.md`가 제출되었습니다.
- 이 라운드의 목표는 `_build_entity_claim_coverage_items`에 내부 필드 `trust_tier`와 `support_plurality`를 additive하게 추가하되, `status_label` 4-literal set, 기존 key 이름/순서, `rendered_as` literal, `CoverageStatus`/`SourceRole`/`_ROLE_PRIORITY` 어떤 것도 바꾸지 않는 것이었습니다.
- trusted-role set은 `{OFFICIAL, DATABASE, WIKI}`로 seq 420 tier-4 parity 유지, multi-source metric은 `primary_claim.support_count >= 2` (candidate_count 사용 금지).

## 핵심 변경
- `core/agent_loop.py:4223-4303` `_build_entity_claim_coverage_items` 실제 상태
  - MISSING branch `:4239-4253`: `"slot"`, `"status"`, `"status_label"`, `"support_count"`, `"candidate_count"`, `"value"`, `"source_role"`, `"rendered_as"` 기존 키 순서 유지. 끝에 `"trust_tier": ""`, `"support_plurality": ""` 두 필드 추가 확인. 기존 default 값은 변경 없음.
  - 메인 append `:4265-4301`: `:4265` `status` 계산은 기존대로 `str(getattr(slot_coverage, "status", CoverageStatus.WEAK) or CoverageStatus.WEAK)` 유지.
  - `:4266-4270` 새 `_trusted_roles_for_trust_tier = {SourceRole.OFFICIAL, SourceRole.DATABASE, SourceRole.WIKI}` literal 확인. handoff가 고정한 exact trio 그대로이며 seq 420 tier-4 parity와 정합.
  - `:4271-4274` `_supporting_source_roles` tuple comprehension이 `primary_claim.supporting_sources` 3-tuple의 세 번째 요소(role)를 `str(role or "")`로 정리. `ClaimRecord.supporting_sources: tuple[tuple[str, str, str], ...]` 계약과 일치.
  - `:4275-4282` STRONG 분기에서 trusted-role 교집합 비어 있지 않으면 `"trusted"`, 아니면 `"mixed"`, STRONG 아니면 `""` 로 trust_tier 계산.
  - `:4283-4287` WEAK 분기에서 `_primary_support_count >= 2` 면 `"multiple"`, 아니면 `"single"`, WEAK 아니면 `""` 로 support_plurality 계산. `candidate_count` 아닌 `primary_claim.support_count` 사용 확인.
  - `:4288-4301` append dict 끝에 `"trust_tier": trust_tier`, `"support_plurality": support_plurality` 두 키 추가, 기존 `"slot"`/`"status"`/`"status_label"`/`"support_count"`/`"candidate_count"`/`"value"`/`"source_role"`/`"rendered_as"` 키 이름·순서·값 식 모두 미변경 확인.
- `tests/test_smoke.py:1283-1388` 신규 regression `test_build_entity_claim_coverage_items_emits_trust_tier_and_support_plurality_internal_fields` 확인
  - 배치는 기존 `test_coverage_entity_card_claim_coverage_payload_marks_conflict_slot_with_conflict_rendered_as`(`:1206`) 직후 첫 번째 테스트로 들어가 있어 coverage cluster 인접성 유지. `/work` 문장과 일치.
  - 네 가지 분기 fixture를 한 호출에서 모두 실행: `개발`(STRONG + OFFICIAL+DATABASE 지원) / `서비스/배급`(STRONG + NEWS only) / `장르/성격`(WEAK + support_count=2 + WIKI 2건) / `이용 형태`(WEAK + support_count=1 + BLOG).
  - `assertEqual(coverage_by_slot["개발"]["trust_tier"], "trusted")`, `서비스/배급` → `"mixed"`, `장르/성격` → `support_plurality == "multiple"`, `이용 형태` → `support_plurality == "single"` 어서션 확인.
  - MISSING 분기는 `CORE_ENTITY_SLOTS` 중 `"상태"` 슬롯에 대해 `core_coverage`가 값을 주지 않아 primary_claim이 None → `coverage_by_slot["상태"]["trust_tier"] == ""`, `"support_plurality"] == ""` 로 검증되어 uniform shape 확인.
  - 모든 item에 대해 `assertIn("trust_tier", item)`, `assertIn("support_plurality", item)` presence guard 존재.
  - 기존 `status_label` 어서션은 추가되지 않았습니다. 라벨셋 미변경 제약 준수.
- seq 408/411/414/417/420/423/427/430 shipped surface 미수정 확인
  - `_annotate_claim_coverage_progress`(`:4305+`), `_claim_coverage_status_label`, `_build_entity_claim_source_lines::support_refs.sort`, seq 420 `_ROLE_PRIORITY`, seq 423 overall cap, seq 427 sort-key 6-tuple, seq 430 regressed-transition wording(`:4475-4488`) 모두 그대로.
  - `app/static/app.js` legend(`:2518`), `buildFocusSlotExplanation`(`:2441-2448`), Playwright scenarios(`e2e/tests/web-smoke.spec.mjs`) 미수정.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `438` — 이미 shipped 됐고 새로운 `/work`로 consumed.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `436` — seq 437 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `437` — seq 438 handoff로 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — seq 423/427/430/438 shipping으로 자연 해제 유지. real operator-only blocker 없음.

## 검증
- 직접 코드/테스트 대조
  - `core/agent_loop.py:4239-4253` MISSING branch 새 필드 2건 확인.
  - `core/agent_loop.py:4265-4301` 메인 append trusted-role set + 파생 computation + 새 필드 2건 확인.
  - `tests/test_smoke.py:1283-1388` 네 분기 + MISSING + presence guard 확인.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 22 tests in 0.049s`, `OK`. handoff 기대치(21 → 22) 그대로. 기존 coverage 회귀 전부 green 유지, 신규 회귀 추가만으로 +1.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 7 tests in 0.022s`, `OK`. seq 430 baseline 유지.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`. seq 427 baseline 유지.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.054s`, `OK`. seq 423 baseline 유지.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `node --check app/static/app.js`, `npx playwright test`, `make e2e-test`, `python3 -m unittest tests.test_web_app`는 이번 α slice가 브라우저 visible contract를 바꾸지 않아 의도적으로 생략했습니다. 클라이언트/Playwright 파일 변경 없음을 `git status --short app/static app/serializers.py e2e/tests` 대신 위 grep hit 없음으로 확인했습니다.

## 남은 리스크
- **downstream UI consumer 미소비**: 현재 `trust_tier`/`support_plurality`는 어떤 browser/Playwright/docs surface에서도 읽히지 않습니다. α는 opt-in 기반만 만든 슬라이스라 설계상 정상이지만, 이후 UI consumer 없이 방치되면 "사용처 없는 내부 필드"로 남습니다. Milestone 4 refinement는 advice 437 기준 closing이라 당장의 follow-up slice는 없지만, 새 축(G)에서 UI가 옵트인해 쓰거나 제거 판단이 뒤따라야 coherent 상태가 됩니다.
- **다음 슬라이스 ambiguity**: advice 437은 "next suggested axis is G (axis rotation)"라고만 적었고 G에 들어갈 슬라이스를 pin하지 않았습니다. gemini_request seq 436에 나열된 G-후보(reinvestigation `prefer_probe_first` threshold 튜닝, `_role_confidence_score` float-axis 튜닝, fact-strength bar UI polish, memory-foundation 다음 슬라이스, session-store parity hardening, storage-layer reuse, unrelated `tests.test_web_app` failure family truth-sync, `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state cleanup, canonical `REASON_CODE`/`OPERATOR_POLICY` vocabulary enforcement)는 모두 축이 다르고 single obvious current-risk reduction가 없습니다. 다음 control slot은 `.pipeline/operator_request.md`가 아니라 `.pipeline/gemini_request.md`(CONTROL_SEQ 439)로 G-axis first slice arbitration을 여는 편이 /verify README 규칙에 맞습니다.
- **unrelated red tests 잔존**: 전체 `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 여전히 별도 truth-sync 라운드 몫입니다. G 선택지에 포함되지만 이번 라운드에서는 재판정하지 않았습니다.
- **docs round count**: 오늘(2026-04-20) docs-only round count는 여전히 0입니다. server-only additive 변경이라 docs drift를 유발하지 않았습니다.
- **dirty worktree**: broad unrelated dirty files(`controller/`, `pipeline_runtime/`, `pipeline_gui/`, `storage/`, docs, older `/work` `/verify` 노트)는 그대로 남아 있습니다. 이번 라운드에서 의도적으로 건드리지 않았고 α 구현은 해당 파일을 수정하지 않습니다.
