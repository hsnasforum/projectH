# history-card click-reload plain-follow-up browser docs truth-sync bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/NEXT_STEPS.md`
- `docs/TASK_BACKLOG.md`
- `work/4/11/2026-04-11-history-card-click-reload-plain-follow-up-browser-docs-truth-sync-bundle.md`

## 사용 skill

- `superpowers:using-superpowers`
- `doc-sync`

## 변경 이유

직전 라운드에서 브라우저 composer 를 거치는 click-reload → plain follow-up 페어(`e2e/tests/web-smoke.spec.mjs` 의 신규 entity-card / latest-update 시나리오 2건)가 이미 구현·통과되어 browser smoke 가족의 proof gap 자체는 닫혔습니다. 그러나 현재 루트 docs 는 여전히 browser smoke inventory 를 `123` 개 시나리오라고만 서술하고 새 쌍을 어느 곳에서도 명시하지 않아 truth drift 가 남아 있었습니다. 이 슬라이스는 docs-only 로 그 drift 를 한 번에 닫습니다.

핸드오프가 명시한 대로 같은 날 같은 가족에서 작은 docs 마이크로 라운드를 또 찍지 않고, 필수 루트 docs 5개(`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md`)를 한 번에 bundle 로 truth-sync 했습니다. inventory count(`123 core browser scenarios`)는 `125` 로 정확히 올렸고, 새 페어(entity-card / latest-update)는 각 루트 doc 에 정확히 한 번씩만 추가했습니다. 기존 가족 표현은 바꾸지 않았습니다.

이번 슬라이스는 browser smoke 계약이 실제로 바뀐 것이 아니라, 이미 landed 된 2건의 신규 scenario 가 docs 에 반영되지 않아 있었던 문제를 닫는 것입니다. 구현·app·runtime 은 건드리지 않았습니다.

## 핵심 변경

### `README.md`

`Current smoke scenarios:` 번호 목록 124–125 번을 추가했습니다. 기존 123 항목(`web-search history card header badges` general label+progress-only) 바로 뒤에 2개 새 항목을 나란히 붙였습니다.

- `124. history-card entity-card 다시 불러오기 click reload 후 브라우저 composer … plain follow-up … /api/chat/stream POST payload 에 load_web_search_record_id 를 전혀 포함하지 않은 채 전송되고, follow-up 이후에도 #claim-coverage-box 가 visible 이며 #claim-coverage-text 에 저장된 entity-card 장르 / [단일 출처] 슬롯과 history-card .meta 가 정확히 사실 검증 단일 출처 1 · 단일 출처 상태 1건. 로 drift 없이 유지되는지 확인`
- `125. history-card latest-update 다시 불러오기 click reload 후 … follow-up 이후에도 #claim-coverage-box 가 hidden 이며 history-card .meta 카운트가 0 으로 유지되는지 확인`

각 항목은 browser-composer 경로(`#user-text` + `submit-request`)와 `/api/chat/stream` POST payload 에서 `load_web_search_record_id` 의 부재를 명시하고, entity-card 는 top-level claim-coverage 유지, latest-update 는 empty claim-coverage surface 유지를 구분해 적었습니다. 구체 문구는 기존 시나리오 스타일(예: `사실 검증 단일 출처 1 · 단일 출처 상태 1건.`)을 그대로 유지해 실제 assertion 과 매치되도록 했습니다.

### `docs/ACCEPTANCE_CRITERIA.md`

- 1352 라인의 `Playwright smoke covers 123 core browser scenarios (…)` 를 `Playwright smoke covers 125 core browser scenarios (…)` 로 업데이트했습니다. 괄호 문구와 `document-level browser coverage inventory count, not the raw test(...) count` 한정은 그대로 유지해 raw `test(...)` count 와의 차이 맥락을 보존했습니다.
- `### In Progress` 바로 앞 inventory 블록 끝(browser folder picker mixed scanned-PDF … 직후)에 2개 새 bullet 을 추가했습니다:
  - `history-card entity-card 다시 불러오기 click reload → 브라우저 composer … plain follow-up … /api/chat/stream POST payload 가 load_web_search_record_id 를 전혀 포함하지 않고, follow-up 이후에도 #claim-coverage-box visible, #claim-coverage-text 에 저장된 entity-card 장르 / [단일 출처] 슬롯, history-card .meta 정확히 사실 검증 단일 출처 1 · 단일 출처 상태 1건. 유지`
  - `history-card latest-update 다시 불러오기 click reload → … follow-up 이후에도 #claim-coverage-box hidden, history-card .meta count 0 유지`

두 bullet 은 README 의 124/125 와 실제 assertion 키(`#claim-coverage-box`, `#claim-coverage-text`, `.meta` 값)가 일치합니다.

### `docs/MILESTONES.md`

`Milestone 4` 윗쪽 현재 shipped browser smoke 가족 bullet 묶음(`web-search history card header badges` general label+progress-only composition 직후)에 2개 새 bullet 을 추가했습니다:

- `history-card entity-card click reload → browser composer (#user-text + submit-request) plain follow-up (이 결과 한 문장으로 요약해줘) browser smoke covering /api/chat/stream POST payload omitting load_web_search_record_id after the click-reload step, #claim-coverage-box visible with #claim-coverage-text containing the stored entity-card 장르 / [단일 출처] slot, and history-card .meta exactly 사실 검증 단일 출처 1 · 단일 출처 상태 1건. retained across the plain follow-up`
- `history-card latest-update click reload → browser composer (#user-text + submit-request) plain follow-up (이 결과 한 문장으로 요약해줘) browser smoke covering /api/chat/stream POST payload omitting load_web_search_record_id after the click-reload step, #claim-coverage-box hidden, and history-card .meta count 0 retained across the plain follow-up`

기존 `In Progress` 섹션이나 다른 가족 bullet 은 건드리지 않았습니다.

### `docs/NEXT_STEPS.md`

- 23 라인의 `Playwright smoke currently covers 123 core browser scenarios (…)` 를 `125 core browser scenarios` 로 업데이트했습니다. `aligned with docs/ACCEPTANCE_CRITERIA.md:1351` 참조 라인은 그대로 뒀습니다 — 해당 참조 라인 자체는 inventory 헤더의 이전 라인 번호를 가리키고, ACCEPTANCE_CRITERIA.md 의 헤더 라인 위치는 count 변경만으로는 바뀌지 않기 때문입니다.
- 같은 inventory 한 문장 중간에, `full latest-update natural-reload family closure covering … news-only (…) exact-field, follow-up, and second-follow-up continuity,` 바로 뒤에 새 페어를 한 번만 삽입했습니다: `history-card entity-card / latest-update click reload followed by a browser composer (#user-text + submit-request) plain follow-up (이 결과 한 문장으로 요약해줘) where the /api/chat/stream POST payload omits load_web_search_record_id entirely, entity-card retains #claim-coverage-box visible with the stored 장르 / [단일 출처] slot and history-card .meta exactly 사실 검증 단일 출처 1 · 단일 출처 상태 1건., and latest-update keeps #claim-coverage-box hidden with history-card .meta count 0,`.
- 이 한 삽입 외에는 긴 inventory 문장을 쪼개거나 재배열하지 않았고, 다른 bullet 이나 뒷부분 섹션(`mock remains the stable automated browser smoke baseline`, `tests/test_smoke.py`, Playwright webServer launch 설명 등)은 건드리지 않았습니다.

### `docs/TASK_BACKLOG.md`

`### 현재 shipped browser smoke Playwright coverage` 끝(126 번 항목 `web-search history card header badges` general label+progress-only composition) 바로 뒤에 2개 새 번호 항목을 추가했습니다:

- `127. History-card entity-card 다시 불러오기 click reload → browser composer (#user-text + submit-request) plain follow-up (이 결과 한 문장으로 요약해줘) Playwright smoke coverage (/api/chat/stream POST payload omits load_web_search_record_id after the click reload, #claim-coverage-box visible with #claim-coverage-text containing the stored entity-card 장르 / [단일 출처] slot, history-card .meta exactly 사실 검증 단일 출처 1 · 단일 출처 상태 1건. retained across the plain follow-up)`
- `128. History-card latest-update 다시 불러오기 click reload → … plain follow-up … Playwright smoke coverage (/api/chat/stream POST payload omits load_web_search_record_id after the click reload, #claim-coverage-box hidden, history-card .meta count 0 retained across the plain follow-up)`

`## Current Phase In Progress`, `## Not Implemented`, `## Later`, `## Open Questions` 등 이후 섹션은 건드리지 않았습니다.

### 건드리지 않은 영역

- `e2e/tests/web-smoke.spec.mjs`, `app/static/app.js`, `app/handlers/*`, `core/*`, `app/serializers.py`, `tests/*`, `storage/*`, `controller/*`, `pipeline_gui/*`, `watcher_core.py`, `pipeline_runtime/*`, `scripts/*`, `.pipeline/*`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md` 등은 이번 슬라이스 범위 밖입니다.
- `docs/NEXT_STEPS.md` 의 `tests/test_smoke.py`, `mock remains the stable automated browser smoke baseline`, Playwright webServer launch bullet 등 뒷부분 섹션도 건드리지 않았습니다.
- MILESTONES 의 `In Progress` / 하위 milestone 섹션, ACCEPTANCE_CRITERIA 의 `In Progress` / `Next-Phase Placeholder` / 나머지 contract 섹션도 건드리지 않았습니다.

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음.
- 이번 라운드는 handoff 가 명시한 대로 docs-only 이므로 Playwright 재실행, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행, type check 는 하지 않았습니다. 직전 `/work` + `/verify` 라운드에서 이미 `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "plain follow-up" --reporter=line` 가 통과 (`2 passed`) 한 상태를 truth 로 삼았습니다.

## 남은 리스크

- inventory count `123 → 125` 는 `README.md` 번호 목록(`123 → 125`), `docs/ACCEPTANCE_CRITERIA.md:1352`, `docs/NEXT_STEPS.md:23` 세 곳에서 같이 올렸습니다. 앞으로 browser smoke 가 또 바뀔 때는 이 세 곳을 같이 점검해야 일치가 유지됩니다. `docs/TASK_BACKLOG.md` 의 shipped 번호 목록(`… 126 → 128`)도 같은 날 같은 숫자 체계로 쓰이므로, 다음 라운드에 또 shipped 되는 경우 여기도 같이 올려 주세요.
- MILESTONES 의 browser smoke bullet 묶음은 계속 선형으로 길어지고 있습니다. 이 슬라이스는 그 구조 자체는 건드리지 않고, 같은 자리에 2개만 덧붙였습니다. 구조 정리는 지금 범위 밖이고 별도 슬라이스가 필요합니다.
- 현재 repo 는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, 기존 `docs/*` 일부, 기존 `/work`, `/verify` dirty 상태입니다. 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았고, 오직 5개 루트 docs + 이 closeout 만 수정했습니다. handoff 의 dirty worktree 경고와 "`app.web` browser smoke inventory family 밖은 건드리지 말라" 제약을 유지했습니다.
- 새 페어의 wording 은 `이 결과 한 문장으로 요약해줘` / `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` 등 exact string 을 docs 에 노출합니다. 미래에 해당 브라우저 시나리오의 문구나 store-seed 데이터가 바뀌면 README / ACCEPTANCE_CRITERIA / MILESTONES / NEXT_STEPS / TASK_BACKLOG 5곳에서 같이 업데이트해야 합니다.
