# 2026-04-20 support_plurality UI consumption verification

## 변경 파일
- `verify/4/20/2026-04-20-support-plurality-ui-consumption-verification.md`

## 사용 skill
- `round-handoff`: seq 441 `.pipeline/claude_handoff.md`(G-axis G2) 구현 주장을 `core/agent_loop.py`, `app/serializers.py`, `app/static/app.js`, `tests/test_smoke.py`, `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(`tests.test_smoke -k progress_summary/coverage`, `tests.test_web_app` 대상 단일 메서드, isolated Playwright rerun, `py_compile`, `node --check`, `git diff --check`)을 직접 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 441 `.pipeline/claude_handoff.md`(Gemini 440 advice 기반 G2)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-support-plurality-ui-consumption.md`가 제출되었습니다.
- 목표는 seq 438이 추가한 `support_plurality` 내부 필드를 서버 focus-slot WEAK 요약 + 클라이언트 focus/비포커스 "단일 출처" 힌트 두 지점에서 opt-in 소비하되, `trust_tier`, `status_label` 4-literal set, 레전드(`app/static/app.js:2518-2519`), summary-bar chip/label은 손대지 않는 것이었습니다. multi-source WEAK copy lie 한 건만 좁게 닫는 current-risk reduction 슬라이스입니다.

## 핵심 변경
- `core/agent_loop.py:4408-4549` `_build_claim_coverage_progress_summary` 실제 상태 확인
  - `:4431-4435` 새 `current_support_plurality_map` 컴프리헨션이 `canonical_current`에서 slot → `support_plurality`만 뽑아 별도 맵으로 유지. 기존 `current_map`(status 맵)과 공존하며 return-early guard(`:4436`)는 변경 없음.
  - `:4442` `unresolved_slots: list[tuple[str, str, str, str]]`로 튜플 폭이 3 → 4로 확장. append site `:4475-4482`가 네 번째 원소로 `current_support_plurality_map.get(slot, "")`를 싣습니다. improved/regressed 튜플(`:4440-4441`)은 기존 5-tuple 그대로 유지(변경 없음).
  - `:4525` focus-slot 루프 unpack가 `for slot, current_label, cur_status, cur_support_plurality in unresolved_slots`로 확장됨.
  - `:4532-4541` focus-slot WEAK 분기가 `cur_support_plurality == "multiple"`일 때 `"아직 여러 출처가 확인되었으나 교차 확인 기준에는 미달합니다."`, 아니면 기존 `"아직 한 가지 출처의 정보로만 확인됩니다."`를 반환. CONFLICT 분기(`:4527-4531`)와 MISSING fallback(`:4542-4545`)은 그대로 유지.
  - 비포커스 summary fallback(`:4547-4562+`)은 4-tuple unpack 시 support_plurality 원소를 `_support_plurality`로 버려 wording을 바꾸지 않았습니다. handoff가 요구한 대로 non-focus multi-source WEAK는 계속 기존 `"재조사했지만 아직 {slot} {label} 상태입니다."` 문구로 나와 legend 4-literal set과 symmetry 유지.
- `app/serializers.py:946-972` `_serialize_claim_coverage` 확인
  - 기존 13개 키 이름·순서·표현식 전부 그대로, 끝(`:970`)에 `"support_plurality": str(item.get("support_plurality") or "").strip(),`만 추가. `trust_tier`는 serializer에서 내보내지 않음(G1 out-of-scope 원칙 유지).
- `app/static/app.js:2433-2464` `buildFocusSlotExplanation`
  - `:2453-2459` `curr === "단일 출처"` 분기가 `item.support_plurality === "multiple"`일 때 `"→ 재조사 대상이며 여러 출처가 확인되었으나, 아직 교차 확인 기준에는 미달합니다."`, 아니면 기존 `"→ 재조사 대상이지만, 아직 단일 출처 상태입니다. 추가 교차 검증이 권장됩니다."`를 반환. improved/regressed/미확인/교차 확인 분기는 그대로.
- `app/static/app.js:2466-2523+` `renderClaimCoverage`
  - `:2503-2510` 비포커스 `statusLabel === "단일 출처"` 분기가 `item.support_plurality === "multiple"`일 때 `"→ 여러 출처가 확인되었으나 교차 확인 기준에는 미달합니다."`, 아니면 기존 `"→ 1개 출처만 확인됨. 교차 검증이 권장됩니다."` 라인을 push. focus 분기와 `statusLabel === "미확인"` 분기는 그대로.
  - 레전드(`:2518-2519`)는 손대지 않음. 확인함.
- `tests/test_smoke.py:3194` 신규 회귀 `test_build_claim_coverage_progress_summary_focus_slot_weak_multi_source_emits_multi_source_wording` 존재 확인. 이름에 `claim_coverage`와 `progress_summary`가 모두 포함돼 `-k progress_summary`와 `-k coverage` subset 양쪽에 매칭됩니다.
- `tests/test_web_app.py:8594-8597` 어서션이 `"한 가지 출처의 정보로만 확인됩니다"` 부분 문자열을 검사하도록 truth-sync됨. 이 테스트는 현재 checkout에서 `WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`(`:8513`)에 속하며, handoff가 참조한 옛 메서드 이름 `test_handle_chat_entity_web_search_emits_claim_coverage_progress_summary_for_focused_reinvestigation`은 현재 없는 이름입니다. `/work`가 이 차이를 명시적으로 기록했습니다. fixture는 single-source이므로 서버가 기존 single-source fallback `"아직 한 가지 출처의 정보로만 확인됩니다."`를 그대로 반환하고, truth-synced assertion이 해당 문자열을 부분 일치로 매칭합니다. multi-source wording(`"여러 출처가 확인되었으나 교차 확인 기준에는 미달합니다"`)으로 flip되지 않았음을 확인했습니다.
- `e2e/tests/web-smoke.spec.mjs:1785-1810` 신규 Playwright 시나리오 `claim_coverage_multi_source_weak_focus_slot_emits_multi_source_hint` 존재 확인. 바로 직전(`:1770-1783`) 기존 regressed-transition 시나리오 다음에 배치돼 있고, CONFLICT 클러스터(`:1855+`)로 넘어가지 않음. 어서션은 focus slot(`is_focus_slot: true`, `support_plurality: "multiple"`)에 대해 `"재조사 대상이며 여러 출처가 확인되었으나, 아직 교차 확인 기준에는 미달합니다."` toContainText + `"1개 출처만 확인됨. 교차 검증이 권장됩니다."` not.toContainText + `"[단일 출처] 이용 형태"` toContainText 세 건으로, `status_label` 4-literal set 보존까지 함께 pinning.
- seq 408/411/414/417/420/423/427/430/438 shipped 표면은 전부 그대로입니다. 레전드 텍스트, `_claim_coverage_status_label`, `_build_entity_claim_coverage_items`, seq 430 regressed-transition wording(`core/agent_loop.py:4486-4524`, `app/static/app.js:2441-2448`, `e2e/tests/web-smoke.spec.mjs:1770-1783`, `tests/test_smoke.py:2976-2994`) 미수정 확인.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `441` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 442.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `439` — seq 440 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `440` — seq 441 handoff로 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — seq 423/427/430/438/441 shipping으로 자연 해제 유지. real operator-only blocker 없음.

## 검증
- 직접 코드/테스트 대조 (파일 경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 8 tests in 0.013s`, `OK`. handoff 기대치(7 → 8) 정합. 새 focus-slot multi-source WEAK 회귀 green.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 23 tests in 0.043s`, `OK`. handoff의 `22` 기대치와 달리 `23`이 된 이유는 새 회귀 이름에 `claim_coverage`가 들어가 `-k coverage` subset에도 매칭되기 때문임. `/work`가 이 점을 이미 명시했고, 기존 22개 회귀가 전부 green 유지.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - 결과: `Ran 1 test in 0.051s`, `OK`. `:8594-8597` 부분 문자열 어서션이 single-source fallback wording과 정합.
- `python3 -m py_compile core/agent_loop.py app/serializers.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `node --check app/static/app.js`
  - 결과: 출력 없음, 통과.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim_coverage_multi_source_weak_focus_slot_emits_multi_source_hint" --reporter=line`
  - 결과: `1 passed (5.4s)`. isolated rerun green.
- `git diff --check -- core/agent_loop.py app/serializers.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `python3 -m unittest tests.test_smoke -k claims`, `-k reinvestigation`, 전체 `tests.test_web_app`, `make e2e-test`는 이번 slice가 `_build_entity_claim_coverage_items` 내부나 shared browser helper를 건드리지 않았고 브라우저 릴리스 판정도 아니어서 의도적으로 재실행하지 않았습니다. `/work`가 `claims/reinvestigation`은 실행 결과(각 `7`, `6`)를 보고했고, 해당 suite는 이번 변경의 write path와 격리되어 있습니다.

## 남은 리스크
- **`trust_tier` 미소비**: 서버 append에는 남아 있으나 serializer가 내보내지 않고 클라이언트도 읽지 않습니다. α + G2 이후 G1(Opt-in UI consumption of trust_tier)은 여전히 열려 있는 자연스러운 후속 후보이며, 이번 verify에서도 downstream-consumer-없는 내부 필드가 남습니다.
- **non-focus multi-source WEAK summary fallback**: `_build_claim_coverage_progress_summary` 비포커스 요약은 여전히 `"재조사했지만 아직 {slot} 단일 출처 상태입니다."`를 내놓습니다. legend 4-literal set과 symmetry 유지를 위해 의도적으로 유지한 결정이고, 필요하면 G 계열에서 별도 slice로 재검토해야 합니다.
- **`tests/test_web_app.py`의 메서드 이름 drift**: handoff는 구형 메서드 이름을 인용했지만 현재 checkout에서는 `WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`가 actual 대응 메서드입니다. 이번 라운드는 부분 문자열 어서션 한 줄만 바꿔 truth-sync했으나, 전체 `tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 여전히 별도 라운드 몫입니다.
- **다음 슬라이스 ambiguity**: G 축 first slice(G2)가 닫혔고, 남은 G1/G3/G4/G5/G6/G7/G8 후보는 축이 서로 다르며 single obvious current-risk reduction이 없습니다. 따라서 next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 442)로 G-axis second slice arbitration을 여는 편이 `/verify` README 규칙과 맞습니다. 오늘(2026-04-20) same-family docs-only truth-sync 반복은 없으므로 docs bundle escalation 조건은 해당 없음.
- **docs round count**: 오늘(2026-04-20) docs-only round count는 여전히 0입니다. 이번 server + client copy 변경은 사용자에게 보이는 텍스트 튜닝이지만 product-framing docs drift를 유발하지 않았고, `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`/`PROJECT_CUSTOM_INSTRUCTIONS.md`/로드맵 문서는 이 축과 무관합니다.
- **dirty worktree**: `controller/`, `pipeline_runtime/`, `pipeline_gui/`, `storage/`, `docs/`, 과거 `/work`·`/verify` 노트에 broad unrelated dirty files 잔존. 이번 슬라이스는 그 파일들을 건드리지 않았습니다.
