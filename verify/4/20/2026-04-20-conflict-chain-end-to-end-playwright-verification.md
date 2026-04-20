# 2026-04-20 conflict chain end-to-end playwright verification

## 변경 파일
- `verify/4/20/2026-04-20-conflict-chain-end-to-end-playwright-verification.md`

## 사용 skill
- `round-handoff`: seq 417 `/work`(`work/4/20/2026-04-20-conflict-chain-end-to-end-playwright.md`)의 Playwright 시나리오 주장 내용을 실제 파일(`e2e/tests/web-smoke.spec.mjs`)과 직접 대조한 뒤, handoff가 요구한 narrowest `-g` isolated Playwright 재실행 + `git diff --check`만 돌려 truthful 여부를 확정했습니다.
- `e2e-smoke-triage`: CONFLICT surface가 이미 saturated 된 상태에서 broad `make e2e-test`는 과하다는 handoff 결정을 재확인하고, isolated rerun을 narrow 기준으로 유지했습니다.

## 변경 이유
- seq 417 `.pipeline/claude_handoff.md`(Gemini 416 Option B 기반)가 구현되어 새로운 `/work` 노트가 제출되었습니다. 이 라운드의 목표는 seq 408 응답 본문 헤더 + seq 411 conflict `근거 출처` URL + seq 414 panel `rendered_as = "conflict"` 세 surface가 한 browser render 안에서 함께 나오는지 Playwright 단일 시나리오로 고정하는 것이었고, 본 verify는 그 주장과 실제 테스트 파일·실행 결과가 일치하는지 검증합니다.

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs:1855-1907`에 새 테스트 `test("CONFLICT chain end-to-end는 응답 본문 헤더 · 근거 출처 URL · panel rendered_as를 함께 표면화합니다", ...)`가 정확히 삽입되어 있습니다. 바로 앞 테스트(`live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다`, `:1825-1853`)와 뒤 테스트(`web-search history card header badges...`, 현재 `:1909-`)는 수정되지 않았습니다.
- fixture 구성
  - `prepareSession(page, "conflict-chain-end-to-end")` (`:1856`)를 호출해 기존 helper를 그대로 사용했고, `renderSession({...}, { force: true })` (`:1860-1885`)로 session 하나를 주입했습니다.
  - assistant message는 1개이며, `text`는 seq 408 `상충하는 정보 [정보 상충]:` 헤더 + `장르/성격` bullet + seq 411 `근거 출처:` / `[정보 상충] 장르/성격:` sub-header + `링크: https://conflict.example.com/genre-official`를 한 줄씩 `join("\n")`로 연결합니다.
  - `claim_coverage`(`:1877-1882`)는 4-literal 전부 포함하는 4슬롯입니다: `개발`(STRONG, `rendered_as: "fact_card"`), `장르/성격`(CONFLICT, `status_label: "정보 상충"`, `rendered_as: "conflict"`), `이용 형태`(WEAK, `uncertain`), `상태`(MISSING, `not_rendered`).
- assertion(`:1888-1906`)은 5묶음으로 handoff가 지정한 것과 정확히 일치합니다:
  1) `#transcript pre`(마지막)에 `상충하는 정보 [정보 상충]:` 포함 (`:1889`).
  2) 같은 `<pre>`에 `https://conflict.example.com/genre-official` 포함 (`:1890`).
  3) 같은 `<pre>` 텍스트에서 conflict URL 위치가 헤더 위치보다 뒤 (`:1892-1896`).
  4) `#claim-coverage-text`에 `[정보 상충] 장르/성격`과 `표시: 상충 정보 반영` 모두 포함 (`:1898-1900`).
  5) `#claim-coverage-text` 텍스트에서 `표시: 상충 정보 반영` 위치가 `[정보 상충] 장르/성격` 뒤 (`:1902-1906`).
- handoff가 금지한 surface와 파일은 그대로 유지되었습니다: 기존 CONFLICT 시나리오 3개(`:1727`, `:1786`, `:1825`), shared helper(`prepareSession`, `ensureLongFixture`), `app/static/app.js`, `app/static/contracts.js`, `core/`, `storage/`, `tests/`, docs, `.pipeline/` rolling slot 중 어디에도 이번 라운드의 수정이 포함되지 않았습니다.
- 새 `data-testid` selector도 추가되지 않았고, `#transcript pre`와 `#claim-coverage-text`처럼 이미 배포된 selector만 사용합니다.

## 검증
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "CONFLICT chain end-to-end" --reporter=line`
  - 결과: `1 passed (4.9s)`. 정확히 1개 시나리오가 실행되어 통과했습니다(`/work` 기록의 `1 passed (7.0s)`와 동일 PASS, 실행 시간은 환경 차이).
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, 통과.
- broad `make e2e-test`, `python3 -m unittest tests.test_smoke`, `python3 -m unittest tests.test_web_app`, `python3 -m py_compile`은 이번 라운드에서 실행하지 않았습니다. 이번 slice는 browser-visible contract나 shared browser helper를 넓히지 않았고 Python surface를 전혀 바꾸지 않아, `.claude/rules/browser-e2e.md`와 `CLAUDE.md`의 narrowest-first 원칙에 맞춰 isolated `-g` 재실행 + `git diff --check`만 수행했습니다.

## 남은 리스크
- Milestone 4 남은 후보는 여전히 별도 라운드 몫입니다:
  - C) Source Role Weighting — COMMUNITY/PORTAL/BLOG tiering 한 번의 정확한 numeric permutation (`core/web_claims.py::_ROLE_PRIORITY` + `core/agent_loop.py` 두 mirror map 동시 갱신 필요).
  - D) Reinvestigation threshold / probe retry — `max_queries_for_slot` 상한, probe list 크기, `prefer_probe_first` 문턱 중 정확히 한 상수.
  - E) Strong vs Weak vs Unresolved Separation further polish — STRONG-tied-with-STRONG tie-break, entity-card strong-badge downgrade edge, 비-CONFLICT 전이 wording.
- 오늘(2026-04-20) docs-only round count는 여전히 0입니다. 이번 slice는 e2e-only라 count는 그대로이며, 다음 라운드가 code-only, code+docs mixed, pure docs-only 중 어느 shape을 택해도 docs-only guard(3-round)에 여유가 있습니다.
- unrelated `python3 -m unittest tests.test_web_app` 전체 실패 family 및 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` 쪽 dirty-state 실패는 이번 slice 밖이며 별도 truth-sync 라운드 몫입니다.
- broad `make e2e-test`는 의도적으로 실행하지 않았습니다. 이후 shared browser helper, `renderSession` 계약, 또는 `#transcript pre` / `#claim-coverage-text` selector 계약 자체가 바뀌면 그때 broad suite 재실행이 필요합니다.
- 다음 control 은 C/D/E 중 어느 후보도 file + surface + numeric/textual 경계가 단독으로 pinned 되어 있지 않아 slice_ambiguity 성격입니다. operator-only decision, approval blocker, 안전 정지, Gemini 부재 중 어느 조건에도 해당하지 않으므로 `.pipeline/gemini_request.md` (seq 418)으로 arbitration을 먼저 여는 편이 rule에 맞습니다.
