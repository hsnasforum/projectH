# 2026-04-19 claim-coverage panel hint conflict explanation verification

## 변경 파일
- `verify/4/19/2026-04-19-claim-coverage-panel-hint-conflict-explanation-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-claim-coverage-panel-hint-conflict-explanation.md`)의 code+docs mixed 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`conflict-docs-truth-sync-bundle-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 382 (`Claim Coverage Panel Hint CONFLICT Explanation — code + ACCEPTANCE_CRITERIA:1375 sync`)는 panel 하단 hint에 `[정보 상충]` 설명 엔트리를 추가해 panel 안의 `정보 상충` 라벨을 같은 화면에서 해석 가능하게 만들고, 그와 정합을 이루도록 line 1375 panel-rendering-contract 문장을 같은 라운드에서 4-tag로 갱신하는 code+docs mixed 슬라이스였습니다.
- 이번 `/work`가 `app/static/app.js:2511-2512`, `docs/ACCEPTANCE_CRITERIA.md:1375`, `e2e/tests/web-smoke.spec.mjs`의 3개 파일 변경을 주장했으므로 각 변경이 현재 tree에 truthful하게 반영됐고 나머지 code/test/markdown 파일이 untouched로 남았는지 고정해야 다음 control 선택이 안전합니다.
- 선행 verify(`conflict-docs-truth-sync-bundle-verification`)는 seq 381 docs-only bundle 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `app/static/app.js:2511-2512`가 이제 `progressText` true/false 두 branch 모두 동일하게 `[교차 확인] 여러 출처가 합의한 사실, [정보 상충] 출처들이 서로 어긋나 추가 확인이 필요한 항목, [단일 출처] 1개 출처에서만 확인된 정보, [미확인] 추가 조사가 필요한 항목입니다.`로 4-tag 순서를 렌더링합니다. `${progressText} ` prefix는 기존 위치 그대로 유지됩니다.
  - `docs/ACCEPTANCE_CRITERIA.md:1375`가 `claim-coverage panel rendering contract with \`[교차 확인]\`, \`[정보 상충]\`, \`[단일 출처]\`, \`[미확인]\` leading status tags, actionable hints, source role with trust level labels, color-coded fact-strength summary bar, and dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved with natural Korean particle normalization)`로 4-tag 리스트만 바뀌었고, 뒷부분 `actionable hints` 이하 문장은 그대로 유지됩니다.
  - `e2e/tests/web-smoke.spec.mjs:1727` `claim-coverage panel hint는 conflict 상태 설명을 4-tag 순서로 렌더링합니다` 시나리오가 추가됐습니다. seq 377/378/381에서 추가된 기존 scenarios는 이전 위치에 그대로 남아 있습니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `docs/ACCEPTANCE_CRITERIA.md:35/48/49`를 포함한 다른 ACCEPTANCE_CRITERIA 문장은 이번 라운드에서 수정되지 않았습니다. line 49의 "does not emit a dedicated `[정보 상충]` response-body header tag" 주장은 그대로 truthful합니다.
  - `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/TASK_BACKLOG.md`, `docs/MILESTONES.md`는 이번 라운드에서 수정되지 않았습니다.
  - `core/agent_loop.py` response-body section headers(`확인된 사실 [교차 확인]:` / `단일 출처 정보 [단일 출처] (추가 확인 필요):` / `확인되지 않은 항목 [미확인]:`)는 그대로 유지됩니다.
  - `summarizeClaimCoverageCounts`, `formatClaimCoverageCountSummary`, `formatClaimCoverageSummary`, `renderFactStrengthBar`, `app/static/contracts.js`, `app/static/style.css`, `app/serializers.py`, `storage/web_search_store.py`, `core/contracts.py`, `core/web_claims.py`는 이번 라운드에서 수정되지 않았습니다.
- 이번 라운드로 CONFLICT same-family chain이 관찰 가능한 모든 surface에서 정합하게 맞춰진 상태입니다.
  - server: `core/contracts.py` CoverageStatus.CONFLICT, `core/web_claims.py` conflict emission, `core/agent_loop.py` label/rank/unresolved/probe 분기
  - storage: `storage/web_search_store.py::_summarize_claim_coverage` 4-key
  - serializer: `app/serializers.py:282-287` 4-key claim_coverage_summary
  - browser history-card summary: `formatClaimCoverageCountSummary` 4-segment join
  - browser in-answer bar: `renderFactStrengthBar` 4-badge + `.fact-count.conflict` CSS
  - browser live-session summary: `formatClaimCoverageSummary → summarizeClaimCoverageCounts` (dead branch resolved at seq 378)
  - browser client contract enum: `app/static/contracts.js::CoverageStatus.CONFLICT`
  - browser claim-coverage panel hint: `renderPanelHint(..., ... [정보 상충] ... )` 4-tag 설명
  - 문서: `docs/PRODUCT_SPEC.md:269`(seq 376), `docs/ARCHITECTURE.md:222`(seq 376), `docs/ACCEPTANCE_CRITERIA.md:35/48/49`(seq 381), `docs/ACCEPTANCE_CRITERIA.md:1375`(seq 382), `docs/TASK_BACKLOG.md:25`(seq 381), `docs/MILESTONES.md:51/52/151`(seq 381)
  - Playwright locks: history-card CONFLICT summary(seq 376), in-answer bar CONFLICT badge(seq 377), live-session answer meta CONFLICT summary(seq 378), panel hint 4-tag explanation(seq 382)
- focused 검증이 모두 통과했습니다.
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel hint는 conflict 상태 설명을 4-tag 순서로 렌더링합니다" --reporter=line` → `1 passed (5.4s)` (`/work` 결과)
  - `git diff --check -- app/static/app.js docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs` → 출력 없음, exit `0` (이번 verify에서 독립 재실행)
- 기존 panel-hint scenario widening이 필요 없었던 이유도 truthful합니다.
  - 기존 시나리오는 `#claim-coverage-hint`에 대해 3개 tag substring을 `.toContainText(...)`로 확인하므로, 4-tag 문구가 여전히 3개 기존 tag substring을 포함해 assertion이 깨지지 않습니다. `/work`의 설명과 현재 tree가 정합합니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `app/static/app.js:2508-2513`, `docs/ACCEPTANCE_CRITERIA.md:1375`, `e2e/tests/web-smoke.spec.mjs:1727`, 그리고 untouched 검증용으로 `docs/ACCEPTANCE_CRITERIA.md:35/48/49`, `core/agent_loop.py:4700-4725`, `app/static/contracts.js:26`, `app/static/app.js:2246-2319`.
  - 결과: `/work`가 설명한 3개 파일 변경이 현재 tree와 일치하고, 언급된 untouched 영역도 실제로 그대로 유지됩니다.
- `git diff --check -- app/static/app.js docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright full 스위트: 이번 라운드는 단일 panel-hint renderer 호출 문구 + 단일 docs bullet + 단일 신규 시나리오 변화이고, shared browser helper를 건드리지 않았으므로 `.claude/rules/browser-e2e.md`의 "isolated Playwright rerun 우선" 기준에 맞습니다. `/work`가 이미 isolated rerun 결과를 기록했습니다.
  - isolated Playwright rerun 자체 재실행: `/work`가 `1 passed (5.4s)`로 기록했고 git diff check가 깨끗해 이번 verify에서 같은 시나리오를 다시 돌릴 추가 근거가 없습니다.
  - 전체 `python3 -m unittest tests.test_web_app`, `tests.test_smoke`: 이번 라운드는 Python 경로를 전혀 건드리지 않았고, 기존 실패 family는 선행 verify들에서 별도 dirty-state truth-sync 라운드 몫으로 분리돼 있습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared helper 변경도 없으므로 생략합니다.

## 남은 리스크
- CONFLICT same-family current-risk는 이번 라운드까지로 관찰 가능한 모든 surface에서 truthfully 닫혔습니다. 다음 슬라이스 후보는 current-risk보다 polish / 새 axis 쪽에 가깝고, 둘 다 low-confidence prioritization이 있습니다.
  - (polish-a) `core/agent_loop.py`의 CONFLICT-specific focus_slot wording strengthening: 현재도 label lookup을 통해 `"아직 정보 상충 상태입니다."`처럼 CONFLICT-aware 문장이 나오지만, CONFLICT 전용 전용 explanation template을 고정하면 좀 더 명확한 사용자 메시지가 가능합니다. 다만 wording design이 여러 방향(중립 기술, 방향성 지시, 출처 충돌 구체 지시 등)으로 갈릴 수 있어 실제 slice로 내려면 Gemini가 문장 템플릿을 고정해 주는 편이 안전합니다.
  - (polish-b) response-body header에 `[정보 상충]` tag를 추가해 response-body 섹션에서도 CONFLICT 블록을 분리하는 방향. 이는 사용자 체감 변화가 크고 focused regression 범위도 넓어져 bounded mini-slice라기보다 별도 설계 논의가 필요합니다.
  - (axis-c) Milestone 4의 `source role labeling/weighting` 한 하위 계약(예: 신뢰도 레벨별 cut-off, role 별 badge detail)의 한 파일/한 surface 슬라이스.
  - (axis-d) Milestone 4의 `strong vs weak vs unresolved separation beyond CONFLICT`에서 지금까지 섞여 있는 경로(예: MISSING 슬롯 reinvestigation trigger threshold, strong-badge downgrade 조건) 중 하나의 한 파일 슬라이스.
- Milestone 4 새 sub-axis로 넘어가는 pivot과 CONFLICT family 내부 polish 사이에서, 어느 쪽이 현재 MVP 우선순위(current-risk reduction > user-visible improvement > new quality axis > internal cleanup)에 더 잘 맞는지는 이 verify 혼자 결정할 만큼 근거가 명확하지 않습니다. 따라서 다음 control slot은 Gemini arbitration으로 여는 편이 rule에 맞습니다.
- 같은 날 same-family docs-only round 수는 seq 381의 1회 그대로입니다. 이번 라운드는 code+docs mixed라 docs-only count가 증가하지 않았으며, 다음 라운드도 mixed 혹은 code-only로 잡히면 3+ guard에서 계속 멀어집니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
