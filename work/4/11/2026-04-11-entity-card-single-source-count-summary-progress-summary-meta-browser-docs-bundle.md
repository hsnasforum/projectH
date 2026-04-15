# entity-card single-source count-summary + progress-summary meta browser docs bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-entity-card-strong-plus-missing-count-summary-meta-reload-path-browser-docs-bundle.md`) 와 대응 `/verify` (`verify/4/11/2026-04-11-entity-card-strong-plus-missing-count-summary-meta-reload-path-browser-docs-verification.md`) 는 strong-plus-missing count-summary meta reload-path 열두 Playwright 시나리오를 네 개 doc 에 inventory 동기화했습니다. 같은 날 browser-docs truth-sync 는 entity-card meta-contract, latest-update empty-meta, store-seeded actual-search empty-meta, zero-strong-slot missing-only count-summary, dual-probe mixed count-summary, strong-plus-missing count-summary reload-path 로 이미 여러 번 반복되었고, 한 번 더 한 줄짜리 docs-only micro-slice 를 여는 것보다 인접한 single-source count-summary + progress-summary meta composition family 를 한 바운드로 닫는 편이 unnecessary micro-split 을 피합니다.

기존 docs inventory 는 history-card entity-card single-source 쪽의 reload/follow-up 경로에서 `WEB` / `설명 카드` / `설명형 단일 출처` / `백과 기반` visible continuity 만 적어 두고, 동일 시나리오가 이미 assert 하고 있는 count-summary + progress-summary composed `.meta` 줄 (`사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건.` 또는 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.`) 은 inventory 에 한 줄도 반영되어 있지 않았습니다. 이 슬라이스는 브라우저 동작 자체는 건드리지 않고, 해당 네 reload-path 시나리오가 실제로 assert 하는 composed `.meta` 계약만 네 개 doc 에 일관된 문체로 추가 기록합니다. 새 Playwright 테스트, selector 수정, 다른 family, service 테스트로는 번지지 않습니다.

## 핵심 변경

네 시나리오가 assert 하는 composed `.meta` 계약:
- click reload 단계 (`test("history-card entity-card 다시 불러오기 클릭 후 ...")` / `spec.mjs:1379`) : stored `{weak:1, missing:1}` count-summary + `단일 출처 상태 1건, 미확인 1건.` progress summary 가 합쳐져 `.meta` 가 정확히 `사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건.` 로 유지되고, count-summary 가 progress-summary 앞에 오며, `.meta` 안에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak 없고, composed line 에 leading/trailing separator artifact 없음.
- click reload follow-up (`spec.mjs:1645`) : stored `{weak:1}` count-summary + `단일 출처 상태 1건.` progress summary 가 합쳐져 `.meta` 가 정확히 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` 로 유지되고, 동일한 순서 / no-leak / no-artifact 계약.
- click reload second follow-up (`spec.mjs:1793`) : 같은 `{weak:1}` + `단일 출처 상태 1건.` composition 이 drift 없이 유지.
- 자연어 reload second follow-up (`spec.mjs:1951`) : 같은 `{weak:1}` + `단일 출처 상태 1건.` composition 이 drift 없이 유지.

각 doc 에 다음과 같이 반영했습니다.

### `README.md`

115번 뒤에 116 / 117 / 118 / 119번을 추가했습니다. click reload 라인은 `사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건.` composed `.meta` 를, 나머지 세 follow-up 라인은 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` composed `.meta` 를 각각 명시합니다.

### `docs/ACCEPTANCE_CRITERIA.md`

- document-level browser coverage inventory count line 을 `115 core browser scenarios` → `119 core browser scenarios` 로 갱신 (count 의미 문맥 주석은 그대로 유지).
- 직전 strong-plus-missing reload-path noisy single-source 자연어 reload second follow-up bullet 뒤에 네 single-source count-summary + progress-summary bullet 을 추가 (README 문체와 동일).

### `docs/MILESTONES.md`

- 직전 strong-plus-missing reload-path noisy single-source 자연어 reload second follow-up browser smoke milestone 뒤에 네 single-source count-summary + progress-summary browser smoke milestone 을 추가.

### `docs/TASK_BACKLOG.md`

- 118번 뒤에 119 / 120 / 121 / 122번 항목을 추가.

service 테스트, Playwright 테스트 코드, pipeline 파일, `docs/projectH_pipeline_runtime_docs/`, 다른 family / docs section 은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -c "사실 검증 단일 출처 1|단일 출처 상태 1건" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - `README.md`: 4, `docs/ACCEPTANCE_CRITERIA.md`: 4, `docs/MILESTONES.md`: 4, `docs/TASK_BACKLOG.md`: 4.
  - 네 doc 모두에서 신규 네 개 bullet 이 대칭으로 들어갔음을 확인했습니다.
- `rg -n "사실 검증 단일 출처 1 · 단일 출처 상태 1건|사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` 로 composed literal 이 doc 전반에 일관된 문구로 등장함을 확인했습니다.
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음
- 브라우저/서비스 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright / `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- `docs/ACCEPTANCE_CRITERIA.md` 의 document-level browser coverage inventory count 는 이 라운드에서 `119` 로 갱신되었지만, `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` 가 반환하는 raw file-level `test(...)` 카운트와는 여전히 서로 다른 축의 카운트입니다. 두 축의 실제 매핑 audit 은 이 라운드 범위 밖입니다.
- `e2e/tests/web-smoke.spec.mjs` 에는 single-source `.meta` composed-line 계약이 asserted 되는 지점이 위 네 곳 외에도 다른 family 에 존재할 수 있으며 (예: latest-update 또는 noisy 쪽 composed progress-summary 경로), 이 라운드에서는 추가 재검색을 하지 않았습니다. 필요 시 별도 audit 라운드에서 다룰 여지가 있습니다.
- TASK_BACKLOG 쪽의 대문자 `History-card` / `Entity-card` 관행과 README / ACCEPTANCE_CRITERIA / MILESTONES 의 소문자 관행 차이는 기존 inventory 라인과 문체를 맞춘 결과입니다. 별도 문체 정합성 정리가 필요한지 여부는 이 라운드 범위 밖입니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
