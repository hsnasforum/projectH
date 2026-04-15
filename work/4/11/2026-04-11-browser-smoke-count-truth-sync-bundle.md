# browser smoke count truth-sync bundle

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-bundle.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-verification.md`)는 noisy-community latest-update natural-reload reload-only 브라우저 시나리오 자체와 README / ACCEPTANCE_CRITERIA / MILESTONES / TASK_BACKLOG 동기화를 truthfully 마쳤고, 해당 시나리오의 isolated Playwright 재실행도 통과했습니다. 즉, noisy-community latest-update family 쪽 브라우저 gap 자체는 이미 닫혀 있습니다.

남은 drift 는 브라우저 동작이 아니라 카운트 의미의 truth-sync 입니다. 직전 `/work` 노트는 `e2e/tests/web-smoke.spec.mjs` 의 raw `test(...)` 개수를 "이제 105 개" 라고 적었지만, 현재 `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` 는 `104` 를 반환합니다. 또 `docs/ACCEPTANCE_CRITERIA.md` 는 `Playwright smoke covers 83 core browser scenarios:` 라는 라인을 쓰고 있어, 문맥 없이 읽으면 raw file test 카운트로 오해되기 쉬운 document-level coverage inventory count 입니다. 새로운 family 를 열기 전에 이 두 카운트 의미와 노트의 stale 숫자 하나만 정정합니다. 브라우저 테스트 재카운트나 새 시나리오 추가로는 번지지 않습니다.

## 핵심 변경

### `docs/ACCEPTANCE_CRITERIA.md`

- 기존: `- Playwright smoke covers 83 core browser scenarios:`
- 변경: `- Playwright smoke covers 83 core browser scenarios (document-level browser coverage inventory count, not the raw `test(...)` count in `e2e/tests/web-smoke.spec.mjs`):`
- 뒤따르는 bullet 목록 (reload-only 줄 포함) 과 실제 숫자 `83` 은 건드리지 않았습니다. 문맥 괄호 추가만으로 미래 독자가 raw file test 카운트와 document-level inventory 카운트를 혼동하지 않도록 했습니다.

### `work/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-bundle.md`

- 기존 `남은 리스크` 항목의 `"실제 `test(...)` 개수는 이제 105 개입니다"` 문장을 `"rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs 로 재확인한 실제 raw `test(...)` 개수는 `104` 입니다 (이 노트 초기 버전에서 `105` 라고 기술한 것은 사실과 맞지 않아 후속 라운드에서 정정되었습니다)"` 로 수정했습니다.
- 동시에 `docs/ACCEPTANCE_CRITERIA.md` 의 `82 → 83` 증가가 document-level browser coverage inventory count 쪽 동기화이고, file-level raw `test(...)` 카운트와는 다른 축임을 명시적으로 적었습니다.
- reload-only 시나리오 추가 자체를 기술하는 핵심 변경 블록, 문서 bullet 요약, 검증 블록은 건드리지 않았습니다.

다른 `/work` 노트, `/verify` 파일, README / MILESTONES / TASK_BACKLOG, service/browser 테스트 코드, pipeline 파일, `docs/projectH_pipeline_runtime_docs/` 는 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` → `104`
- `rg -n "Playwright smoke covers|document-level|104|105|83 core" docs/ACCEPTANCE_CRITERIA.md work/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-bundle.md`
  - `docs/ACCEPTANCE_CRITERIA.md:1351` 이 `... 83 core browser scenarios (document-level browser coverage inventory count, not the raw `test(...)` count in `e2e/tests/web-smoke.spec.mjs`):` 로 갱신되었습니다.
  - 직전 `/work` 노트의 해당 리스크 항목이 `104` 로 정정되고 `105` 표기는 "초기 버전에서 ... 정정" 문구 안에만 남아 있습니다.
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md work/4/11` → whitespace 경고 없음
- 브라우저/서비스 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright 재실행과 `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- `docs/ACCEPTANCE_CRITERIA.md` 의 `83` 숫자와 `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` 의 `104` 는 여전히 서로 다른 축의 카운트이고, 이 슬라이스는 두 축 사이의 실제 매핑(어떤 raw test 가 어떤 document-level 항목에 해당하는지)을 재카운트하지 않았습니다. 필요 시 별도 inventory audit 라운드에서 다룰 여지가 있습니다.
- `README.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 에도 유사한 카운트 / 항목 번호가 존재하지만, 이 슬라이스는 handoff 의 execution constraint 에 따라 그 파일들을 건드리지 않았습니다. 동일한 문맥 주석이 필요한지 여부는 별도 라운드에서 결정되어야 합니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
