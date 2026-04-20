# 2026-04-20 conflict source lines followup Gemini 413 verification

## 변경 파일
- `verify/4/20/2026-04-20-conflict-source-lines-followup-gemini-413-verification.md`

## 사용 skill
- `round-handoff`: 이전 라운드의 `/verify`(`verify/4/20/2026-04-20-conflict-source-lines-role-priority-sync-verification.md`)가 이미 seq 411 `/work`를 truthful하게 닫았음을 재확인하고, 같은 날 Gemini advice seq 413이 새로 도착한 상황에서 다음 control slot을 어떻게 이어 쓸지 기록했습니다.

## 변경 이유
- 이 verify 라운드는 seq 411 `/work`(`work/4/19/2026-04-19-conflict-source-lines-role-priority-sync.md`)에 대한 재-dispatch입니다. dispatcher가 참조한 anchor verify는 seq 408 `verify/4/19/2026-04-19-response-body-conflict-header-verification.md`였지만, 실제 최신 verify는 오늘 날짜 폴더에 저장된 `verify/4/20/2026-04-20-conflict-source-lines-role-priority-sync-verification.md`이고 /work를 이미 truthful 하게 검증했습니다.
- 그 사이 Gemini advice가 seq 413 (`STATUS: advice_ready`, Option A: Claim-coverage panel conflict surface — panel-side rendered_as / wording polish)으로 도착했으므로, 이번 verify는 별도 추가 검증 없이 prior verify를 가리키고 다음 control outcome이 `.pipeline/claude_handoff.md` seq 414로 seq 413 advice를 변환하는 것임을 truthful 하게 기록하는 bridge 성격의 노트입니다.

## 핵심 변경
- 선행 verify(`verify/4/20/2026-04-20-conflict-source-lines-role-priority-sync-verification.md`)가 여전히 유효합니다.
  - `core/agent_loop.py:4130-4141`, `:4515-4557`, `:4781+`의 seq 411 변경이 그대로이고, `tests/test_smoke.py:1133-1204` 새 회귀도 유지됩니다.
  - 마지막 verify 이후로 새 `/work` 노트는 도착하지 않았고, dirty tree의 다른 hunk도 이번 verify 목적과 무관합니다.
- `.pipeline` slot 상태 snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ 411 — seq 411 슬라이스가 이미 shipped.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ 412 — 어제 verify 라운드에서 next-axis 중재를 위해 열어 둔 요청.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ 413 — Gemini가 seq 412 요청을 받아 Option A(`Claim-coverage panel conflict surface — panel-side rendered_as / wording polish`)를 `core/agent_loop.py` + `app/static/app.js` + `tests/test_smoke.py` 3파일로 pinning.
  - `.pipeline/operator_request.md`: 이번 라운드 변경 없음.
- Gemini 413 advice는 truthful exact slice입니다. operator-only decision, approval blocker, 안전 정지, Gemini 부재 같은 상황이 아니므로 `.pipeline/operator_request.md`를 여는 편이 아닙니다. `.pipeline/claude_handoff.md`를 seq 414로 써서 advice를 implement로 변환하는 편이 rule에 맞습니다.
- 다음 슬라이스 target 확인 (code+docs mixed, today docs-only count 0에서 시작)
  - `core/agent_loop.py:4222-4272` `_build_entity_claim_coverage_items`: 현재 `rendered_as`를 `fact_card`/`uncertain`/`not_rendered` 3-literal로만 emit하고, `status_label`을 `"교차 확인" if status == CoverageStatus.STRONG else "단일 출처"`/`"미확인"` 하드코드로 결정합니다. CONFLICT 슬롯은 payload 단계에서 silently WEAK-like label로 떨어져, panel이 `정보 상충`을 표면화할 수 없습니다.
  - 두 callsite (`:6246`, `:6520`)는 여전히 seq 411 이후에도 `primary_claims, _, weak_claims, _, _`로 conflict_claims를 discard합니다.
  - `app/static/app.js:2406-2412` `formatClaimRenderedAs`는 `fact_card`/`uncertain`/`not_rendered` 3-literal만 처리합니다. `conflict` 분기를 추가하려면 `"상충 정보 반영"`을 반환하도록 한 줄만 확장하면 됩니다.
  - docs 쪽 natural ripple: `docs/ARCHITECTURE.md:220`과 `docs/PRODUCT_SPEC.md:267`의 `rendered_as (\`fact_card\` / \`uncertain\` / \`not_rendered\`)` 열거가 code 변경 직후 stale이 되므로, 같은 라운드에서 바로 4-literal로 확장하는 편이 truthful합니다. 오늘은 docs-only round count가 0이므로 mixed 라운드 포함이 guard에 걸리지 않습니다.
- 같은 날 same-family docs-only round count는 오늘 fresh 상태로 0입니다. 이번 seq 414 슬라이스가 code+docs mixed라도 docs-only count는 증가하지 않습니다.

## 검증
- 추가 코드 테스트/Playwright 재실행: 이번 verify는 dispatch loop bridge 성격이며 `/work`가 바뀌지 않았습니다. 선행 verify에서 이미 `-k coverage` 18 / `-k claims` 5 / `py_compile` / `git diff --check` 모두 통과한 상태를 재확인만 했고, 이번 라운드에서 동일 명령을 한 번 더 돌릴 추가 근거가 없었습니다.
- 직접 상태 대조: `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`의 CONTROL_SEQ/STATUS를 직접 읽었고, `core/agent_loop.py:4222-4272` / `:6246` / `:6520` / `app/static/app.js:2406-2412` / `docs/ARCHITECTURE.md:220` / `docs/PRODUCT_SPEC.md:267`의 현재 상태를 확인해 다음 슬라이스 target이 정확함을 고정했습니다.

## 남은 리스크
- 선행 verify(`verify/4/20/2026-04-20-conflict-source-lines-role-priority-sync-verification.md`)에 이미 기록된 Milestone 4 남은 sub-axis 후보(COMMUNITY/PORTAL/BLOG weighting, reinvestigation threshold 추가 tuning, strong-vs-weak-vs-unresolved further polish, seq 408/411용 optional Playwright scenario)는 여전히 미해결 상태입니다. 이번 seq 414 슬라이스는 그 중 Gemini가 고른 "claim-coverage panel conflict surface"만 다룹니다.
- 이번 슬라이스가 shipped되면 `app/static/app.js::formatClaimRenderedAs`가 새 `"상충 정보 반영"` 리터럴을 포함하게 됩니다. 다른 브라우저/renderer 경로가 `rendered_as === "conflict"`를 처리하지 못하고 silent skip되는지는 별도 audit 후보입니다. 현재 확인된 consumer는 `:2480` 한 곳이지만 optional Playwright scenario에서 end-to-end 확인하는 편이 안전합니다.
- 다른 docs 파일에 `rendered_as`를 3-literal로 직접 enumerate한 stale 문장이 남아 있는지는 이번 /work 단계에서 재grep하고, 추가 발견 시 별도 narrow docs-sync round 후보로 `남은 리스크`에 기록하도록 handoff에 명시했습니다. 오늘 docs-only round count 0이므로 follow-up docs 라운드가 필요하면 guard 여유 안에서 가능합니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
