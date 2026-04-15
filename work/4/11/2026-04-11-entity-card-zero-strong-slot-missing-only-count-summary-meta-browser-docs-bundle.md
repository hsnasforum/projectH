# entity-card zero-strong-slot missing-only count-summary meta browser docs bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-entity-card-store-seeded-actual-search-empty-meta-browser-docs-bundle.md`) 와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-entity-card-store-seeded-actual-search-empty-meta-browser-docs-verification.md`) 는 store-seeded actual-search empty-meta 여섯 개 Playwright 시나리오를 네 개 doc 에 inventory 동기화했습니다. 같은 날 browser-docs truth-sync 는 entity-card meta-contract, latest-update empty-meta, store-seeded actual-search empty-meta 로 이미 세 번 반복되었고, 한 번 더 한 줄짜리 docs-only micro-slice 를 여는 것보다 인접한 zero-strong-slot missing-only count-summary meta family 세 개를 한 바운드로 닫는 편이 unnecessary micro-split 을 피합니다.

남은 가장 가까운 browser-docs drift 는 entity-card zero-strong-slot missing-only count-summary meta family 입니다. 다음 세 Playwright 시나리오는 이미 `e2e/tests/web-smoke.spec.mjs` 안에 구현되어 통과 상태로 존재하지만, README / ACCEPTANCE_CRITERIA / MILESTONES / TASK_BACKLOG 어디에도 inventory 되어 있지 않았습니다.

- `history-card entity-card zero-strong-slot 다시 불러오기 후 missing-only count-summary meta가 truthfully 유지됩니다` (line 6313)
- `entity-card zero-strong-slot 다시 불러오기 후 두 번째 follow-up 질문에서 missing-only count-summary meta가 truthfully 유지됩니다` (line 6681)
- `entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 missing-only count-summary meta가 truthfully 유지됩니다` (line 7210)

이 슬라이스는 브라우저 동작 자체는 건드리지 않고, 이미 구현되어 있는 세 시나리오가 실제로 assert 하는 사용자-가시 contract 를 네 개 doc 에 일관된 문체로 추가 기록합니다. 새 Playwright 테스트, selector 수정, 다른 family, service 테스트로는 번지지 않습니다.

## 핵심 변경

세 시나리오가 assert 하는 공통 계약:
- 가시 `다시 불러오기` 버튼 유지 (click reload 는 눌림, 자연어 reload 쪽은 채팅 입력으로 reload 발송)
- history-card 최상단 카드의 `.meta` 가 `사실 검증 미확인 5` missing-only count-summary 로 유지 (zero-strong-slot downgrade 후 overstated strong 이 없음을 truthfully 반영)
- `.meta` 안에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak 없음
- `WEB` origin badge, `설명 카드` answer-mode badge, `설명형 단일 출처` verification label, `백과 기반` source role, `namu.wiki` / `ko.wikipedia.org` source path visible continuity 유지
- follow-up / second-follow-up 단계에서는 위 계약이 drift 없이 유지

각 doc 에 다음과 같이 반영했습니다.

### `README.md`

96번 뒤에 97 / 98 / 99번을 추가했습니다.

- 97. zero-strong-slot `다시 불러오기` — `사실 검증 미확인 5` missing-only `.meta` + answer-mode no-leak + WEB / 설명 카드 / 설명형 단일 출처 / 백과 기반 / namu.wiki / ko.wikipedia.org continuity
- 98. zero-strong-slot `다시 불러오기` 후 second follow-up — 동일 계약 drift 없음
- 99. zero-strong-slot 자연어 reload 후 second follow-up — 동일 계약 drift 없음

### `docs/ACCEPTANCE_CRITERIA.md`

- document-level browser coverage inventory count line 을 `96 core browser scenarios` → `99 core browser scenarios` 로 갱신 (count 의미 문맥 주석은 그대로 유지).
- store-seeded actual-search 자연어 reload chain bullet 뒤에 세 zero-strong-slot missing-only count-summary bullet 을 추가 (README 문체와 동일).

### `docs/MILESTONES.md`

- store-seeded actual-search 자연어 reload chain browser smoke milestone 뒤에 세 zero-strong-slot missing-only count-summary browser smoke milestone 을 추가 (기존 browser smoke milestone 문체 그대로).

### `docs/TASK_BACKLOG.md`

- 99번 뒤에 100 / 101 / 102번 항목을 추가.

service 테스트, Playwright 테스트 코드, pipeline 파일, `docs/projectH_pipeline_runtime_docs/`, 다른 family / docs section 은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -c "missing-only count-summary meta|missing-only count-summary|zero-strong-slot" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - `README.md`: 8, `docs/ACCEPTANCE_CRITERIA.md`: 8, `docs/MILESTONES.md`: 8, `docs/TASK_BACKLOG.md`: 8, `e2e/tests/web-smoke.spec.mjs`: 22.
  - 네 doc 에서 각각 기존 zero-strong-slot 엔트리들(reload show-only / follow-up natural / follow-up 등) 위에 세 개 missing-only count-summary meta 엔트리가 새로 추가되었음을 위 카운트 증가로 확인했습니다.
- `rg -n "missing-only count-summary meta" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs` 로 세 시나리오가 doc / spec 양쪽에서 일관 문구로 등장함을 확인했습니다.
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음
- 브라우저/서비스 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright / `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- `docs/ACCEPTANCE_CRITERIA.md` 의 document-level browser coverage inventory count 는 이 라운드에서 `99` 로 갱신되었지만, `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` 가 반환하는 raw file-level `test(...)` 카운트와는 여전히 서로 다른 축의 카운트입니다. 두 축의 실제 매핑 audit 은 이 라운드 범위 밖입니다.
- `e2e/tests/web-smoke.spec.mjs` 에는 zero-strong-slot 외에도 추가 meta-contract / missing-only count-summary 계열 (예: dual-probe mixed count-summary 추가 라인) 이 더 있을 수 있고, 이 라운드에서 재검색되지 않았습니다. 필요 시 별도 audit 라운드에서 다룰 여지가 있습니다.
- TASK_BACKLOG 쪽의 대문자 `History-card` 관행과 README / ACCEPTANCE_CRITERIA / MILESTONES 의 소문자 `history-card` 관행 차이는 기존 inventory 라인과 문체를 맞춘 결과입니다. 별도 문체 정합성 정리가 필요한지 여부는 이 라운드 범위 밖입니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
