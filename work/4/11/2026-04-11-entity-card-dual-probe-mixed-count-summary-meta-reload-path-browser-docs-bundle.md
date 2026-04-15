# entity-card dual-probe mixed count-summary meta reload-path browser docs bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-entity-card-zero-strong-slot-missing-only-count-summary-meta-browser-docs-bundle.md`) 와 대응 `/verify` (`verify/4/11/2026-04-11-entity-card-zero-strong-slot-missing-only-count-summary-meta-browser-docs-verification.md`) 는 zero-strong-slot missing-only count-summary meta 세 개 Playwright 시나리오를 네 개 doc 에 inventory 동기화했습니다. 같은 날 browser-docs truth-sync 가 entity-card meta-contract, latest-update empty-meta, store-seeded actual-search empty-meta, zero-strong-slot missing-only count-summary 로 이미 네 번 반복되었고, 한 번 더 한 줄짜리 docs-only micro-slice 를 여는 것보다 인접한 dual-probe mixed count-summary meta reload-path family 네 개를 한 바운드로 닫는 편이 unnecessary micro-split 을 피합니다.

기존 docs inventory 는 dual-probe mixed count-summary `사실 검증 교차 확인 1 · 단일 출처 4` 를 initial-render 한 줄에 대해서만 명시적으로 적어 두고, click reload / click reload second follow-up / 자연어 reload / 자연어 reload second follow-up 네 reload-path 쪽에는 `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `공식 기반` · `백과 기반` / `pearlabyss.com/200` · `pearlabyss.com/300` visible continuity 만 적어 둔 상태였습니다. 해당 네 Playwright 시나리오는 이미 동일 meta 계약을 정확히 assert 하고 있음에도, docs 쪽에 그 mixed count-summary meta 줄이 반영되지 않아 drift 가 남아 있었습니다.

이 슬라이스는 브라우저 동작 자체는 건드리지 않고, 이미 구현되어 있는 네 시나리오가 실제로 assert 하는 mixed count-summary meta contract 를 네 개 doc 에 일관된 문체로 추가 기록합니다. 새 Playwright 테스트, selector 수정, 다른 family, service 테스트로는 번지지 않습니다.

## 핵심 변경

네 시나리오가 assert 하는 공통 / 단계별 계약:
- 모든 단계: history-card 최상단 카드의 `.meta` 가 정확히 `사실 검증 교차 확인 1 · 단일 출처 4` mixed count-summary 로 유지, `.meta` 안에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak 없음, mixed count-summary line 에 leading/trailing separator artifact 없음
- click reload 쪽: `WEB` / `설명 카드` / `설명형 다중 출처 합의` / `공식 기반` · `백과 기반` visible continuity 와 `pearlabyss.com/200` · `pearlabyss.com/300` source path continuity 유지
- click reload second follow-up / 자연어 reload / 자연어 reload second follow-up 단계: 같은 시각적 계약이 drift 없이 유지

각 doc 에 다음과 같이 반영했습니다.

### `README.md`

99번 뒤에 100 / 101 / 102 / 103번을 추가했습니다.

- 100. dual-probe `다시 불러오기` reload — `사실 검증 교차 확인 1 · 단일 출처 4` mixed `.meta` + answer-mode no-leak + WEB / 설명 카드 / 설명형 다중 출처 합의 / 공식 기반 · 백과 기반 / pearlabyss.com/200 / pearlabyss.com/300 continuity
- 101. dual-probe `다시 불러오기` 후 second follow-up — 동일 meta drift 없음 + continuity drift 없음
- 102. dual-probe 자연어 reload — 동일 meta + continuity
- 103. dual-probe 자연어 reload 후 second follow-up — 동일 meta drift 없음 + continuity drift 없음

### `docs/ACCEPTANCE_CRITERIA.md`

- document-level browser coverage inventory count line 을 `99 core browser scenarios` → `103 core browser scenarios` 로 갱신 (count 의미 문맥 주석은 그대로 유지).
- zero-strong-slot 자연어 reload second follow-up bullet 뒤에 네 dual-probe mixed count-summary bullet 을 추가 (README 문체와 동일).

### `docs/MILESTONES.md`

- zero-strong-slot 자연어 reload second-follow-up browser smoke milestone 뒤에 네 dual-probe mixed count-summary browser smoke milestone 을 추가 (기존 browser smoke milestone 문체 그대로).

### `docs/TASK_BACKLOG.md`

- 102번 뒤에 103 / 104 / 105 / 106번 항목을 추가.

service 테스트, Playwright 테스트 코드, pipeline 파일, `docs/projectH_pipeline_runtime_docs/`, 다른 family / docs section 은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -c "교차 확인 1 · 단일 출처 4|mixed count-summary meta|dual-probe" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - `README.md`: 13, `docs/ACCEPTANCE_CRITERIA.md`: 13, `docs/MILESTONES.md`: 13, `docs/TASK_BACKLOG.md`: 13, `e2e/tests/web-smoke.spec.mjs`: 53.
  - 네 doc 에서 각각 기존 dual-probe 엔트리들 위에 네 개 mixed count-summary meta 엔트리가 새로 추가되었음을 위 카운트 증가로 확인했습니다.
- `rg -n "교차 확인 1 · 단일 출처 4" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` 로 네 doc 에 새 meta literal 이 일관된 문구로 등장함을 확인했습니다 (기존 초기-render bullet 1 개 + 신규 reload-path bullet 4 개).
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음
- 브라우저/서비스 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright / `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- `docs/ACCEPTANCE_CRITERIA.md` 의 document-level browser coverage inventory count 는 이 라운드에서 `103` 으로 갱신되었지만, `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` 가 반환하는 raw file-level `test(...)` 카운트와는 여전히 서로 다른 축의 카운트입니다. 두 축의 실제 매핑 audit 은 이 라운드 범위 밖입니다.
- dual-probe follow-up (non-second) 경로의 `.meta` 계약이 기존 docs 에 explicit 하게 적혀 있는지는 이 라운드에서 재검색되지 않았습니다. 필요 시 별도 audit 라운드에서 다룰 여지가 있습니다.
- TASK_BACKLOG 쪽의 대문자 `History-card` / `Entity-card` 관행과 README / ACCEPTANCE_CRITERIA / MILESTONES 의 소문자 관행 차이는 기존 inventory 라인과 문체를 맞춘 결과입니다. 별도 문체 정합성 정리가 필요한지 여부는 이 라운드 범위 밖입니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
