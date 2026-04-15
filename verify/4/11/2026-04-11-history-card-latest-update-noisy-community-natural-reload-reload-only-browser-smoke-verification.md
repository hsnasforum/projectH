## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-bundle.md`가 직전 verify에서 지적된 raw count mismatch와 count wording ambiguity까지 반영해 이제 truthful한지 다시 확인해야 했습니다.
- 확인이 끝난 뒤에는 이미 닫힌 count-truth-sync slice를 가리키는 stale handoff를 정리하고, 같은 browser docs family에서 남은 더 큰 bounded docs bundle 한 건만 다음 구현으로 넘겨야 했습니다.

## 핵심 변경
- 새 Playwright 시나리오 `history-card latest-update 자연어 reload noisy community 보조 커뮤니티 brunch 미노출 기사 교차 확인 보조 기사 hankyung mk 유지됩니다` 가 실제로 추가되어 있었고, noisy latest-update natural-reload reload-only branch만 좁게 잠그고 있음을 확인했습니다 (`e2e/tests/web-smoke.spec.mjs:2507`).
- 같은 시나리오는 프리시드 `response_origin` 을 `label: "외부 웹 최신 확인"`, `kind: "assistant"`, `model: null`, `verification_label: "기사 교차 확인"`, `source_roles: ["보조 기사"]` 로 고정하고, 자연어 reload 뒤 `WEB` / `최신 확인` / `기사 교차 확인` / `보조 기사` 유지와 `보조 커뮤니티` / `brunch` / `공식 기반` / `공식+기사 교차 확인` 미노출, `hankyung.com` / `mk.co.kr` 유지, zero-count `.meta` no-leak까지 직접 검증합니다 (`e2e/tests/web-smoke.spec.mjs:2559`, `e2e/tests/web-smoke.spec.mjs:2615`, `e2e/tests/web-smoke.spec.mjs:2645`).
- docs sync도 실제로 들어가 있었습니다. `README.md`는 82번 뒤 83번 항목을 추가했고 (`README.md:207`), `docs/ACCEPTANCE_CRITERIA.md`는 reload-only 항목과 함께 count line을 `document-level browser coverage inventory count` 라고 명시해 raw file-level `test(...)` count와의 혼동을 막았습니다 (`docs/ACCEPTANCE_CRITERIA.md:1351`, `docs/ACCEPTANCE_CRITERIA.md:1421`). `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`도 같은 reload-only coverage를 반영하고 있습니다 (`docs/MILESTONES.md:101`, `docs/TASK_BACKLOG.md:100`).
- 최신 `/work`의 `## 남은 리스크`도 이제 raw `test(...)` count를 `104`로 truthfully 적고, `83` count가 document-level inventory count라는 점을 명확히 설명합니다 (`work/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-bundle.md:62`).
- 따라서 latest `/work`는 현재 기준 truthful합니다. 반면 현재 `.pipeline/claude_handoff.md` 는 이미 닫힌 `browser smoke count truth-sync docs bundle` 을 계속 가리키고 있어 stale 상태였고, 이번 verify 라운드에서 다음 slice를 새로 좁혔습니다.
- 다음 단일 슬라이스는 `history-card entity-card initial-render meta-contract browser docs bundle` 로 정했습니다. 이미 존재하는 Playwright 시나리오 세 건 (`e2e/tests/web-smoke.spec.mjs:2661`, `e2e/tests/web-smoke.spec.mjs:2933`, `e2e/tests/web-smoke.spec.mjs:3036`) 이 README / ACCEPTANCE / MILESTONES / TASK_BACKLOG 어디에도 아직 적혀 있지 않아, 같은 browser docs family 안의 남은 bounded drift를 한 번에 닫는 편이 맞습니다.

## 검증
- 코드/문서 대조:
  - `rg -n "history-card latest-update 자연어 reload noisy community|history-card latest-update 다시 불러오기 후 noisy community source가 본문" e2e/tests/web-smoke.spec.mjs`
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2361,2695p'`
  - `rg -n "Playwright smoke covers 83 core browser scenarios|104|document-level browser coverage inventory count|105" docs/ACCEPTANCE_CRITERIA.md work/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-bundle.md`
  - `rg -n "history-card entity-card noisy single-source initial-render|history-card entity-card actual-search initial-render|history-card entity-card dual-probe initial-render|strong-plus-missing count-summary meta contract|mixed count-summary meta contract" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - `nl -ba README.md | sed -n '194,208p'`
  - `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1421,1432p'`
  - `nl -ba docs/MILESTONES.md | sed -n '92,104p'`
  - `nl -ba docs/TASK_BACKLOG.md | sed -n '98,104p'`
  - `rg -c '^\\s*test\\(' e2e/tests/web-smoke.spec.mjs` → `104`
- isolated browser rerun:
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 자연어 reload noisy community" --reporter=line`
  - 결과: `Running 1 test using 1 worker` 후 `1 passed (6.2s)`
- 포맷 확인:
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11`
  - 결과: 출력 없음
- 이번 변경은 Playwright single-scenario + docs sync 범위이므로 `tests/test_web_app.py`, `make e2e-test`, 전체 Playwright suite는 재실행하지 않았습니다.

## 남은 리스크
- same-family noisy latest-update reload-only browser slice와 count semantics drift는 현재 기준 닫혔습니다. 대신 history-card entity-card initial-render meta-contract browser 시나리오 세 건이 test 파일에는 존재하지만 docs inventory에서는 아직 빠져 있습니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/...`, 기존 `verify/4/11/...`, 기존 `work/4/11/...`, untracked `docs/projectH_pipeline_runtime_docs/`). 다음 구현 라운드는 기존 pending 파일을 되돌리지 않고 지정된 docs 범위만 좁게 수정해야 합니다.
