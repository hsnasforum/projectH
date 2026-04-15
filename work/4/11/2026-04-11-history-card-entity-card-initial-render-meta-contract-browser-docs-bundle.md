# history-card entity-card initial-render meta-contract browser docs bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-bundle.md`, `2026-04-11-browser-smoke-count-truth-sync-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-noisy-community-natural-reload-reload-only-browser-smoke-verification.md`, `verify/4/11/2026-04-11-browser-smoke-count-truth-sync-verification.md`)는 noisy-community latest-update natural-reload reload-only 브라우저 시나리오와 카운트 의미 drift를 truthfully 닫았습니다. `e2e/tests/web-smoke.spec.mjs`의 실제 raw `test(...)` 개수는 `104`이고 `docs/ACCEPTANCE_CRITERIA.md`는 document-level browser coverage inventory count로 `83`을 쓴다는 의미 구분도 이미 반영되어 있습니다.

남은 가장 가까운 browser-docs drift는 이제 history-card entity-card initial-render meta-contract family입니다. 다음 세 Playwright 시나리오는 이미 `e2e/tests/web-smoke.spec.mjs` 안에 구현되어 통과 상태로 존재하지만, README / ACCEPTANCE_CRITERIA / MILESTONES / TASK_BACKLOG 어디에도 문서화되어 있지 않았습니다.

- `history-card entity-card noisy single-source initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다` (line 2661)
- `history-card entity-card actual-search initial-render 단계에서 strong-plus-missing count-summary meta contract가 유지됩니다` (line 2933)
- `history-card entity-card dual-probe initial-render 단계에서 mixed count-summary meta contract가 유지됩니다` (line 3036)

이 슬라이스는 브라우저 동작 자체는 건드리지 않고, 이미 구현되어 있는 세 시나리오가 실제로 assert하는 사용자-가시 contract만 네 개 doc에 일관된 문체로 추가 기록합니다. 새 Playwright 테스트, selector 수정, 다른 family, service 테스트로는 번지지 않습니다.

## 핵심 변경

세 시나리오가 공통으로 assert하는 계약:
- initial-render 단계만; click reload / 자연어 reload / follow-up 없음
- 가시 `다시 불러오기` 버튼 (클릭하지 않음)
- history-card 최상단 카드의 `.meta`는 count가 1이고 정확한 문자열 하나만 보유
  - noisy single-source / actual-search: `사실 검증 교차 확인 3 · 미확인 2`
  - dual-probe: `사실 검증 교차 확인 1 · 단일 출처 4`
- `.meta` 안에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label이 새지 않음
- noisy single-source variant는 추가로 history-card 전체에 `출시일` / `2025` / `blog.example.com` noisy-single-source 잔재가 노출되지 않음

각 doc에 다음과 같이 반영했습니다.

### `README.md`

82 / 83번 항목 뒤에 84 / 85 / 86번을 추가:
- 84. noisy single-source initial-render — `사실 검증 교차 확인 3 · 미확인 2` exact `.meta` + answer-mode no-leak + `출시일` / `2025` / `blog.example.com` negative
- 85. actual-search initial-render — `사실 검증 교차 확인 3 · 미확인 2` exact `.meta` + answer-mode no-leak
- 86. dual-probe initial-render — `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary exact `.meta` + answer-mode no-leak

### `docs/ACCEPTANCE_CRITERIA.md`

- document-level browser coverage inventory count line을 `83 core browser scenarios` → `86 core browser scenarios`로 갱신 (count 의미 문맥 주석은 그대로 유지).
- noisy natural-reload reload-only bullet 뒤에 세 initial-render bullet 추가 (README 문체와 동일).

### `docs/MILESTONES.md`

- noisy-community natural-reload reload-only milestone 뒤에 세 initial-render browser smoke milestone 추가 (기존 browser smoke milestone 문체 그대로).

### `docs/TASK_BACKLOG.md`

- 86번 뒤에 87 / 88 / 89번 항목 추가.

service 테스트, Playwright 테스트 코드, pipeline 파일, `docs/projectH_pipeline_runtime_docs/`, 다른 family / docs section은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -n "history-card entity-card noisy single-source initial-render|history-card entity-card actual-search initial-render|history-card entity-card dual-probe initial-render|strong-plus-missing count-summary meta contract|mixed count-summary meta contract" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - `e2e/tests/web-smoke.spec.mjs:2661`, `:2933`, `:3036`에 세 시나리오 정의가 그대로 있고, 세 doc에서는 동일 시나리오가 README `84–86`, ACCEPTANCE_CRITERIA bullets, MILESTONES lines, TASK_BACKLOG `87–89`로 잡혀 있음을 확인했습니다.
  - `docs/TASK_BACKLOG.md`의 항목은 위 grep 패턴에 정확히 매치되지 않지만, `grep -n "initial-render" docs/TASK_BACKLOG.md`로 87 / 88 / 89번 라인이 예상 문구로 들어가 있음을 직접 확인했습니다.
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음
- 브라우저/서비스 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright / `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- `docs/ACCEPTANCE_CRITERIA.md`의 document-level browser coverage inventory count는 `86`으로 갱신되었지만, `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs`가 반환하는 raw file-level `test(...)` 카운트(`104`)와는 여전히 다른 축의 카운트입니다. 두 축의 실제 매핑 audit은 이 라운드 범위 밖입니다.
- history-card latest-update initial-render 쪽 `.meta` contract나 다른 family (latest-update / dual-probe / zero-strong / actual-search)의 initial-render 시나리오가 추가로 필요/문서화 누락되었는지는 이 라운드에서 확인하지 않았습니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
