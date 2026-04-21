# 2026-04-20 trust_tier UI consumption verification

## 변경 파일
- `verify/4/20/2026-04-20-trust-tier-ui-consumption-verification.md`

## 사용 skill
- `round-handoff`: seq 444 `.pipeline/claude_handoff.md`(G-axis G1) 구현 주장을 `app/serializers.py`, `app/static/app.js`, `tests/test_smoke.py`, `e2e/tests/web-smoke.spec.mjs` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(`tests.test_smoke -k coverage/progress_summary/claims/reinvestigation`, sanity `tests.test_web_app` 단일 메서드, isolated Playwright rerun, `py_compile`, `node --check`, `git diff --check`)을 직접 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 444 `.pipeline/claude_handoff.md`(Gemini 443 advice 기반 G1 narrowed)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-trust-tier-ui-consumption.md`가 제출되었습니다.
- 목표는 seq 438이 server-internal로 추가한 `trust_tier`를 serializer로 pass-through하고 `item.trust_tier === "mixed"`일 때만 focus/비포커스 두 분기에서 text-only hint를 노출하는 것이었습니다. `status_label` 4-literal set, legend(`app/static/app.js:2518-2519`), summary-bar chip/label, CSS, 그리고 `_build_claim_coverage_progress_summary` server summary copy는 전부 제외 범위였습니다.
- Gemini advice 443의 `"Trusted/Standard/Low"` 표현은 shipped derivation(`{"trusted", "mixed", ""}`)과 불일치해 verify/handoff owner가 slice를 `"mixed"` 1-case로 좁혔고, 이번 라운드는 그 좁힌 범위대로 진행됐습니다.

## 핵심 변경
- `app/serializers.py:946-974` `_serialize_claim_coverage` 실제 상태
  - `:946-969` 기존 13개 키(`slot`, `status`, `status_label`, `previous_status`, `previous_status_label`, `progress_state`, `progress_label`, `is_focus_slot`, `support_count`, `candidate_count`, `value`, `source_role`, `rendered_as`) 이름·순서·표현식 전부 그대로 유지.
  - `:970` seq 441 추가분 `"support_plurality": str(item.get("support_plurality") or "").strip(),` 유지.
  - `:971` 새 키 `"trust_tier": str(item.get("trust_tier") or "").strip(),`가 마지막에 추가됨. `None`/`"unknown"` 등 대체 정규화 없이 빈 문자열 기본값 그대로 통과시킴. handoff 조건과 정합.
- `app/static/app.js:2450-2456` `buildFocusSlotExplanation`의 focus `"교차 확인"` 분기
  - `const trust = String(item.trust_tier || "").trim();` 가드 추가 후 `trust === "mixed"`일 때만 `"→ 재조사 대상이며 현재 교차 확인 상태이지만, 공식/위키/데이터 소스가 약합니다."` 반환. 그 외에는 기존 문구 `"→ 재조사 대상이며, 현재 교차 확인 상태입니다."` 유지.
  - improved/regressed/`"단일 출처"`/`"미확인"`/fallback 분기는 그대로. 단일-출처 `"multiple"` 분기(seq 441)는 미변경 확인.
- `app/static/app.js:2514-2518` `renderClaimCoverage`의 비포커스 새 `"교차 확인"` 분기
  - 기존 seq 441 `"단일 출처"` 비포커스 분기(`:2507-2513`) 바로 다음에 `else if (statusLabel === "교차 확인") { ... }` 블록이 삽입돼 있고, `item.trust_tier === "mixed"`일 때만 `"   → 교차 확인 기준은 충족하지만 공식/위키/데이터 소스가 약합니다."` 라인을 push. `"trusted"`/`""`는 아무 라인도 push하지 않음. handoff의 "no-hint for trusted/empty" 규칙과 일치.
  - 이후 source_role 라인과 metaParts 처리(`:2520-2527+`)는 그대로 유지.
- 색상/chip/badge/CSS/legend 미편집
  - 레전드 텍스트(`:2518-2519 -> 실제 현재 :2522-2523` 부근)는 수정되지 않음.
  - `formatSourceRoleWithTrust`, `formatClaimCoverageSummary`, `formatClaimRenderedAs`, `formatClaimProgress` 전부 미편집 확인.
  - `app/static/style.css`는 편집 대상에서 제외됐고 `git status`에서도 이번 라운드 hunk 없음.
- `tests/test_smoke.py:1390` 신규 회귀 `test_serialize_claim_coverage_passes_through_trust_tier_for_strong_items` 존재 확인. 이름에 `claim_coverage`가 들어가 `-k coverage` subset에 매칭돼 count가 23 → 24로 증가. seq 438 `test_build_entity_claim_coverage_items_emits_trust_tier_and_support_plurality_internal_fields` 직후에 배치됐다는 `/work` 문구와 정합.
- `e2e/tests/web-smoke.spec.mjs:1812` 신규 Playwright 시나리오 `claim_coverage_strong_mixed_trust_tier_non_focus_slot_emits_mixed_trust_hint` 존재 확인. seq 441 `claim_coverage_multi_source_weak_focus_slot_emits_multi_source_hint`(`:1785-1810`) 바로 다음 cluster 위치로, CONFLICT 클러스터(`:1855+`) 또는 fact-strength-bar 클러스터(`:1812+`)로 넘어가지 않음. 어서션은 STRONG + `trust_tier: "mixed"` 비포커스 fixture에 대해 `"[교차 확인] 개발"` + mixed-trust hint toContainText + `"1개 출처만 확인됨. 교차 검증이 권장됩니다."` not.toContainText 세 건.
- seq 408/411/414/417/420/423/427/430/438/441 shipped 표면은 전부 그대로. `core/agent_loop.py`는 이번 라운드에서 편집되지 않았고, `_build_claim_coverage_progress_summary` server summary copy/legend text/summary-bar chips/CSS/`"trusted"` client branch는 의도적으로 미편집. β/γ coordination 재오픈 없음.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `444` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 445.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `442` — seq 443 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `443` — seq 444 handoff로 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — seq 423/427/430/438/441/444 shipping으로 자연 해제 유지. real operator-only blocker 없음.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 24 tests in 0.041s`, `OK`. handoff 기대치(23 → 24) 정합. 기존 coverage 회귀 전부 green 유지.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 8 tests in 0.012s`, `OK`. seq 441 baseline 유지.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`. seq 427 baseline 유지.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.047s`, `OK`. seq 423 baseline 유지.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.056s`, `OK`. seq 441 partial-match 어서션이 serializer 키 추가에도 영향 없음을 확인.
- `python3 -m py_compile app/serializers.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `node --check app/static/app.js`
  - 결과: 출력 없음, 통과.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim_coverage_strong_mixed_trust_tier_non_focus_slot_emits_mixed_trust_hint" --reporter=line`
  - 결과: `1 passed (4.1s)`. isolated rerun green.
- `git diff --check -- app/serializers.py app/static/app.js tests/test_smoke.py e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, 통과.
- `make e2e-test` 및 full `tests.test_web_app`는 shared browser helper를 건드리지 않았고 ready/release 판정 라운드가 아니라 의도적으로 생략했습니다.

## 남은 리스크
- **server summary trust-tier drift 미표현**: `_build_claim_coverage_progress_summary`는 여전히 `trust_tier`를 읽지 않습니다. 요약 문장에 mixed-trust 신호를 싣는 것은 legend symmetry 재협상이 걸려 별도 arbitration이 맞다는 판단을 이번 라운드에도 유지했습니다.
- **seq 438 opt-in 필드 2종이 모두 consumer를 얻었음**: seq 441이 `support_plurality`, seq 444가 `trust_tier`를 client로 흘렸습니다. seq 438 premise가 닫혔고, 추가 current-risk reduction은 새 축(G2-followup / G3..G8)로만 나옵니다.
- **다음 슬라이스 ambiguity**: 남은 G-axis 후보(G2-followup non-focus summary symmetry, G3 `prefer_probe_first` threshold, G4 `_role_confidence_score`, G5 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state, G6 broader `tests.test_web_app` failure family, G7 canonical `REASON_CODE`/`OPERATOR_POLICY` vocabulary, G8 memory-foundation)는 축이 서로 다르고 single obvious dominant current-risk reduction이 없습니다. 따라서 next control은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 445)로 G-axis third slice arbitration을 여는 편이 `/verify` README 규칙과 맞습니다. 오늘(2026-04-20) same-family docs-only truth-sync 3회 이상 반복 조건은 해당 없음(docs-only round count 0 유지).
- **unrelated red tests 잔존**: 전체 `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 여전히 G5/G6 후보로 남아 있고 이번 라운드에서는 재판정하지 않았습니다.
- **docs round count**: 오늘(2026-04-20) docs-only round count는 0 그대로. 이번 UI hint 변경은 browser-visible copy truth-sync이지만 docs drift를 새로 만들지 않았습니다.
- **dirty worktree**: broad unrelated dirty files(`controller/`, `pipeline_runtime/`, `pipeline_gui/`, `storage/`, `docs/`, 과거 `/work`/`/verify` 노트)는 그대로 남아 있습니다. 이번 라운드는 해당 파일들을 건드리지 않았습니다.
