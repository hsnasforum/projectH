# 2026-04-20 conflict chain end-to-end playwright

## 변경 파일
- e2e/tests/web-smoke.spec.mjs

## 사용 skill
- e2e-smoke-triage: CONFLICT browser surface 1건만 추가하는 handoff 범위를 유지하고 `-g` isolated Playwright rerun을 우선 적용했습니다.
- release-check: 실제 변경 파일, 실제 실행 명령, broad browser suite 미실행 사유를 handoff 범위에 맞춰 정직하게 정리했습니다.
- work-log-closeout: `work/4/20/` 아래에 표준 섹션 순서로 이번 구현 closeout을 남겼습니다.

## 변경 이유
- seq 408 응답 본문 헤더, seq 411 conflict source URL, seq 414 panel `rendered_as = "conflict"` surface는 각각 이미 shipped 되었지만, 한 browser render 안에서 세 표면이 함께 유지되는지는 Playwright가 아직 고정하지 못하고 있었습니다.
- 이 상태에서는 formatter branch, transcript body, panel text 중 하나가 조용히 깨져도 기존 unit/path coverage만으로는 브라우저 회귀를 바로 잡아내지 못할 수 있어, handoff가 지정한 current-risk reduction으로 단일 seeded transcript 시나리오를 추가했습니다.

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs:1855-1907`에 `test("CONFLICT chain end-to-end는 응답 본문 헤더 · 근거 출처 URL · panel rendered_as를 함께 표면화합니다", ...)`를 새로 추가하고, 기존 `live-session answer meta...` 뒤 / `web-search history card header badges...` 앞에 정확히 삽입했습니다.
- 새 fixture는 `prepareSession(page, "conflict-chain-end-to-end")` 다음 `renderSession(..., { force: true })`로 session 하나를 seed하며, assistant message 1개만 넣었습니다. 이 message는 seq 408 `상충하는 정보 [정보 상충]:` 헤더와 `장르/성격` bullet, seq 411 `근거 출처:` + `https://conflict.example.com/genre-official`, 그리고 4-slot `claim_coverage`(`fact_card` / `conflict` / `uncertain` / `not_rendered`)를 함께 가집니다.
- assertion은 다섯 묶음만 추가했습니다: transcript `<pre>`의 seq 408 헤더, 같은 `<pre>`의 conflict URL, URL이 헤더 뒤에 오는 순서, `#claim-coverage-text`의 `[정보 상충] 장르/성격` + `표시: 상충 정보 반영`, 그리고 panel 안에서 `표시:` 줄이 CONFLICT slot header 뒤에 오는 순서입니다.
- 기존 CONFLICT 시나리오 3개는 수정하지 않았고, shared helper(`prepareSession`, `ensureLongFixture` 등)는 바꾸지 않았으며, 새 `data-testid` selector도 추가하지 않았습니다.
- 이번 라운드에서 실제로 수정한 파일은 `e2e/tests/web-smoke.spec.mjs` 하나뿐입니다. `app/static/app.js`, `app/static/contracts.js`, `core/`, `storage/`, `tests/`, docs, `.pipeline/` rolling slot은 건드리지 않았습니다.

## 검증
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "CONFLICT chain end-to-end" --reporter=line`
  - 결과: `1 passed (7.0s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, 통과
- `make e2e-test`는 실행하지 않았습니다. 이번 slice는 이미 shipped 된 browser-visible contract 위에 isolated regression 1건만 추가했고 shared browser helper나 selector family를 바꾸지 않아, `.claude/rules/browser-e2e.md` 기준 broad suite가 과했습니다.

## 남은 리스크
- Milestone 4의 남은 후보인 C COMMUNITY/PORTAL/BLOG weighting, D reinvestigation threshold, E strong-vs-weak-vs-unresolved further polish는 이번 라운드 밖에 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0이고, 이번 slice는 e2e-only라서 count도 그대로 0입니다.
- unrelated `python3 -m unittest tests.test_web_app` failure family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state failures는 이번 slice 범위 밖이라 그대로 남아 있습니다.
- broad `make e2e-test`는 의도적으로 돌리지 않았습니다. 이후 라운드에서 shared browser helper를 바꾸거나 browser-visible contract를 넓히면 그때 broad suite를 다시 돌려야 합니다.
