# 2026-04-19 CONFLICT docs truth-sync bundle verification

## 변경 파일
- `verify/4/19/2026-04-19-conflict-docs-truth-sync-bundle-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-conflict-docs-truth-sync-bundle.md`)의 3개 markdown 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`client-coverage-status-conflict-exposure-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 381 (`CONFLICT Family Docs Truth-Sync Bounded Bundle`)은 Gemini advice 380이 고른 Option B였고, `docs/ACCEPTANCE_CRITERIA.md`, `docs/TASK_BACKLOG.md`, `docs/MILESTONES.md`의 CONFLICT 관련 문장만 최소 수정하도록 경계를 두었습니다.
- 이번 `/work`가 ACCEPTANCE_CRITERIA 3문장(line 35/48/49), TASK_BACKLOG 1문장(line 25), MILESTONES 3 bullets(line 51/52/151) 변경과 `[정보 상충]` response-body header tag 의도적 생략(line 49)을 주장했으므로, 각 변경이 현재 tree에 truthful하게 반영됐고 code/test/other docs가 untouched로 남았는지 고정해야 합니다.
- 선행 verify(`client-coverage-status-conflict-exposure-verification`)는 seq 378 contract exposure round 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:35`가 이제 `status tag (\`[교차 확인]\`, \`[정보 상충]\`, \`[단일 출처]\`, \`[미확인]\`) leading each slot line, ..., with explicit \`정보 상충\` wording when sources remain contradictory`로 4-tag + explicit conflict wording을 포함합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:48`이 `reinforced / regressed / still single-source / still unresolved` 4-way naming을 유지하면서 "or remains in an explicit `정보 상충` state" 구절을 덧붙여 CONFLICT가 암묵적으로 접히지 않도록 했습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:49`가 response-body 헤더 3개(`[교차 확인]`, `[단일 출처]`, `[미확인]`)만 emit됨을 유지하고, "Current implementation does not emit a dedicated `[정보 상충]` response-body header tag; `정보 상충` is currently surfaced through claim-coverage count summaries, history-card/live-session `.meta`, the fact-strength summary bar, and focus-slot explanation text instead."로 실제 구현과 정직하게 맞췄습니다.
  - `docs/TASK_BACKLOG.md:25`가 "a 4-segment color-coded fact-strength summary bar (`교차 확인 / 정보 상충 / 단일 출처 / 미확인`)"로 4-segment bar를 명시합니다.
  - `docs/MILESTONES.md:51-52`에 `fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다`와 `live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다` 두 bullet이 추가됐습니다.
  - `docs/MILESTONES.md:151`에 `history-card summary가 non-zero conflict count를 정보 상충 segment로 렌더링합니다` bullet이 추가됐습니다.
  - 기존 3-state MILESTONES bullet들(예: `사실 검증 교차 확인 3 · 미확인 2` 등)은 renumber되거나 rewrite되지 않았습니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`는 이번 라운드에서 수정되지 않았습니다.
  - 이번 라운드에서 source code, test 파일, 그리고 위 3개 외 markdown(`README.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `docs/projectH_pipeline_runtime_docs/**`)은 수정되지 않았습니다.
- 한 가지 잔여 drift 후보가 확인됐으나 이번 handoff scope 밖이었습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:1375`은 regression-gates 섹션에서 claim-coverage panel rendering contract를 "with `[교차 확인]`, `[단일 출처]`, `[미확인]` leading status tags"로 기술합니다. 이 문장의 bracket 표기는 `app/static/app.js:2511-2512` `renderPanelHint(..., "[교차 확인] 여러 출처가 합의한 사실, [단일 출처] 1개 출처에서만 확인된 정보, [미확인] 추가 조사가 필요한 항목입니다.")`에서 실제로 panel 하단 hint로 렌더링되는 3-tag 설명을 가리킵니다.
  - 현재 shipped panel hint가 여전히 3-tag 문장만 가지고 있으므로 line 1375 자체는 아직 틀린 문장은 아닙니다. 하지만 seq 369부터 CONFLICT 슬롯 라벨이 `"정보 상충"`으로 분리됐고, seq 377의 4-badge bar, seq 376의 4-key 요약, seq 378의 contracts.js CONFLICT 노출 등 주변 표면은 전부 CONFLICT를 노출하는데, panel hint만 CONFLICT 설명이 빠진 채로 남아 user-visible explanation gap을 만듭니다. 이것이 same-family user-visible current-risk의 다음 후보입니다(panel hint 자체는 code+doc mixed slice).
- 같은 날 same-family docs-only 라운드 수는 이번 `/work`를 합쳐 1회입니다. seq 366/369/373(blocked)/376/377/378은 implementation rounds이었고 이번만 docs-only입니다. `3+ docs-only same-family` guard는 아직 트리거되지 않았습니다. 다만 다음 라운드도 docs-only로 가면 guard 경로에 가까워지므로, panel hint code change + 해당 line 1375 문장 sync를 code+docs mixed 라운드로 묶는 편이 guard 리스크를 줄입니다.
- focused 검증이 모두 통과했습니다.
  - `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md` → 출력 없음, exit `0`.
  - 독립적으로 같은 grep을 돌리지 않고 `/work`가 기록한 grep 결과(line 번호와 lead-in text)와 직접 읽은 라인 내용이 일치함을 확인했습니다(`ACCEPTANCE_CRITERIA:35/48/49`, `TASK_BACKLOG:25`, `MILESTONES:51/52/151`).
- 이번 verify에서 추가로 확인한 cross-check
  - `app/static/app.js:2511-2512` panel hint → 여전히 3-tag 설명(`[교차 확인] / [단일 출처] / [미확인]`)만 가지고 있습니다. `[정보 상충]` 설명 엔트리는 없음.
  - `core/agent_loop.py:4700-4725` response-body section headers → 여전히 3-tag(`[교차 확인] / [단일 출처] / [미확인]`)만 emit. line 49의 "does not emit a dedicated `[정보 상충]` response-body header tag" 주장과 정합.
  - `core/agent_loop.py:4327-4335` `_claim_coverage_status_label` → `STRONG → "교차 확인"`, `CONFLICT → "정보 상충"`, `WEAK → "단일 출처"`, fallback → `"미확인"`으로 4-way label 그대로.

## 검증
- 직접 문서/코드 대조
  - 대상: `docs/ACCEPTANCE_CRITERIA.md:35/48/49/1375`, `docs/TASK_BACKLOG.md:25`, `docs/MILESTONES.md:51/52/151`, 그리고 cross-check용 `app/static/app.js:2511-2512`, `core/agent_loop.py:4327-4335/4700-4725`.
  - 결과: `/work`가 설명한 문서 변경이 현재 tree와 일치하고, code/test/other docs는 이번 라운드에서 건드리지 않았으며, line 1375 + panel hint code는 여전히 3-tag 상태로 내부적으로 정합입니다.
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - `python3 -m unittest tests.test_web_app`, `tests.test_smoke`, Playwright, `make e2e-test`: 이번 라운드는 docs-only truth-sync bundle이고 source code/test file을 전혀 건드리지 않았기 때문에, 이 명령들은 요구되지 않았고 실행하지 않았습니다. verify/README.md와 `.claude/rules/browser-e2e.md`의 "narrowest relevant" 기준에 맞습니다.
  - `grep` 재실행: `/work`가 이미 scoped grep을 실행해 결과를 closeout에 기록했고 line 내용이 현재 tree와 일치함을 직접 확인했으므로 동일 명령을 반복하지 않았습니다.

## 남은 리스크
- `app/static/app.js:2511-2512` claim-coverage panel hint는 여전히 3-tag 설명만 가지고 있습니다. CONFLICT 슬롯 라벨(`정보 상충`)은 panel에서 볼 수 있지만 panel 하단 hint에는 해석 엔트리가 없어, user가 `[정보 상충]`/`정보 상충`의 의미를 panel hint 한 줄로 확인할 수 없습니다. 같은 family에서 남은 가장 높은 우선순위 user-visible current-risk입니다. 이 hint를 4-tag로 넓히면 `docs/ACCEPTANCE_CRITERIA.md:1375` panel-rendering contract 문장도 같은 라운드에서 4-tag로 sync해야 하므로 code+docs mixed slice로 묶는 편이 coherent합니다.
- `core/agent_loop.py` focus_slot CONFLICT wording은 여전히 label lookup에 의존한 generic wording이고, CONFLICT-specific stronger explanation은 이번 라운드에서도 추가되지 않았습니다. Gemini 380 판단대로 wording design-ambiguous 상태로 남아 있어, 다음 순번 후보이긴 하지만 slice로 확정하려면 구체 문장 템플릿을 먼저 고정해야 합니다.
- Milestone 4의 새 sub-axis(`source role labeling/weighting`, `strong vs weak vs unresolved separation beyond CONFLICT`)는 이번 라운드 범위 밖이며 여전히 separate candidate입니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family(`LocalOnlyHTTPServer PermissionError`, `SQLiteSessionStore._compact_summary_hint_for_persist`)와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 docs-only 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
- 같은 날 same-family docs-only 라운드 수는 이번 /work를 합쳐 1회입니다. 다음 라운드를 순수 docs-only로 또 잡으면 2회가 되고, 더 쌓이면 3+ guard에 근접합니다. panel hint + line 1375 sync는 code+docs mixed라 docs-only count에 들어가지 않으며 guard 압박을 늘리지 않습니다.
