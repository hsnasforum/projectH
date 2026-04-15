# entity-card strong-plus-missing count-summary meta reload-path browser docs bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-entity-card-dual-probe-mixed-count-summary-meta-reload-path-browser-docs-bundle.md`) 와 대응 `/verify` (`verify/4/11/2026-04-11-entity-card-dual-probe-mixed-count-summary-meta-reload-path-browser-docs-verification.md`) 는 dual-probe mixed count-summary meta reload-path 네 개 Playwright 시나리오를 네 개 doc 에 inventory 동기화했습니다. 같은 날 browser-docs truth-sync 가 entity-card meta-contract, latest-update empty-meta, store-seeded actual-search empty-meta, zero-strong-slot missing-only count-summary, dual-probe mixed count-summary 로 이미 다섯 번 반복되었고, 한 번 더 한 줄짜리 docs-only micro-slice 를 여는 것보다 인접한 strong-plus-missing count-summary meta reload-path family 를 한 바운드로 닫는 편이 unnecessary micro-split 을 피합니다.

기존 docs inventory 는 strong-plus-missing count-summary `사실 검증 교차 확인 3 · 미확인 2` 를 actual-search / noisy single-source 두 initial-render bullet (README 84 · 85) 에만 명시적으로 적어 두고, 같은 meta contract 를 이미 assert 하는 click reload / click reload follow-up / click reload second follow-up / 자연어 reload / 자연어 reload follow-up / 자연어 reload second follow-up 경로 쪽에는 visible continuity 만 적어 둔 상태였습니다. 이 슬라이스는 브라우저 동작 자체는 건드리지 않고, 해당 열두 개 reload-path 시나리오가 실제로 assert 하는 strong-plus-missing count-summary meta contract 를 네 개 doc 에 일관된 문체로 추가 기록합니다. 새 Playwright 테스트, selector 수정, 다른 family, service 테스트로는 번지지 않습니다.

## 핵심 변경

열두 시나리오가 assert 하는 공통 / 단계별 계약:
- 모든 단계: history-card 최상단 카드의 `.meta` 가 정확히 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary 로 유지, `.meta` 안에 `설명 카드` / `최신 확인` / `일반 검색` answer-mode label leak 없음
- 더 깊은 follow-up / second follow-up 단계 : 같은 `.meta` 가 drift 없이 유지되고 count-summary line 에 leading/trailing separator artifact 가 생기지 않음

각 doc 에 다음과 같이 반영했습니다.

### `README.md`

103번 뒤에 104–115번 열두 항목을 추가했습니다.

- actual-search click reload / click follow-up / click second follow-up / 자연어 reload / 자연어 reload follow-up / 자연어 reload second follow-up 여섯 bullet
- noisy single-source click reload / click follow-up / click second follow-up / 자연어 reload / 자연어 reload follow-up / 자연어 reload second follow-up 여섯 bullet

모두 `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing count-summary 와 answer-mode label no-leak 을 명시합니다. reload 단계 이후 bullet 에는 추가로 drift 없음과 leading/trailing separator artifact 없음을 명시했습니다.

### `docs/ACCEPTANCE_CRITERIA.md`

- document-level browser coverage inventory count line 을 `103 core browser scenarios` → `115 core browser scenarios` 로 갱신 (count 의미 문맥 주석은 그대로 유지).
- dual-probe 자연어 reload second-follow-up bullet 뒤에 열두 strong-plus-missing count-summary bullet 을 추가 (README 문체와 동일).

### `docs/MILESTONES.md`

- dual-probe 자연어 reload second-follow-up browser smoke milestone 뒤에 열두 strong-plus-missing count-summary browser smoke milestone 을 추가 (기존 browser smoke milestone 문체 그대로).

### `docs/TASK_BACKLOG.md`

- 106번 뒤에 107 – 118번 항목을 추가.

service 테스트, Playwright 테스트 코드, pipeline 파일, `docs/projectH_pipeline_runtime_docs/`, 다른 family / docs section 은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -c "사실 검증 교차 확인 3 · 미확인 2|strong-plus-missing count-summary" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - `README.md`: 14, `docs/ACCEPTANCE_CRITERIA.md`: 14, `docs/MILESTONES.md`: 14, `docs/TASK_BACKLOG.md`: 14.
  - 14 = 2 initial-render (기존) + 12 reload-path (신규) 로, 네 doc 에 동일한 개수로 일관되게 들어갔습니다.
- `rg -n "actual-search|noisy single-source|strong-plus-missing count-summary" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` 로 열두 새 bullet 이 각 doc 에 연속적으로 잘 붙어 있음을 확인했습니다.
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음
- 브라우저/서비스 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright / `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- `docs/ACCEPTANCE_CRITERIA.md` 의 document-level browser coverage inventory count 는 이 라운드에서 `115` 로 갱신되었지만, `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` 가 반환하는 raw file-level `test(...)` 카운트와는 여전히 서로 다른 축의 카운트입니다. 두 축의 실제 매핑 audit 은 이 라운드 범위 밖입니다.
- `e2e/tests/web-smoke.spec.mjs` 에는 `사실 검증 교차 확인 3 · 미확인 2` 를 assert 하는 라인이 아직 많이 남아 있으며 (특히 same-family 반복 시나리오 20 라인 이상), 이번 inventory 는 handoff 가 열거한 actual-search + noisy single-source reload-path 계열만 추가했습니다. 다른 entity-card 변종이나 noisy community source 쪽 같은 meta contract 가 추가로 필요한지는 별도 audit 라운드에서 확인할 여지가 있습니다.
- TASK_BACKLOG 쪽의 대문자 `History-card` / `Entity-card` 관행과 README / ACCEPTANCE_CRITERIA / MILESTONES 의 소문자 관행 차이는 기존 inventory 라인과 문체를 맞춘 결과입니다. 별도 문체 정합성 정리가 필요한지 여부는 이 라운드 범위 밖입니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
