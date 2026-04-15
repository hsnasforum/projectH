# history-card entity-card store-seeded actual-search empty-meta browser docs bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-initial-render-empty-meta-browser-docs-bundle.md`) 와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-initial-render-empty-meta-browser-docs-verification.md`) 는 history-card latest-update initial-render empty-meta 네 개 Playwright 시나리오를 네 개 doc에 inventory 동기화했습니다. 같은 날 browser-docs truth-sync 는 entity-card meta-contract 세 개, latest-update empty-meta 네 개로 이미 두 번 반복되었고, 한 번 더 한 줄짜리 micro-slice 를 여는 것보다 인접한 store-seeded actual-search empty-meta family 여섯 개를 한 바운드로 닫는 편이 불필요한 micro-split 을 피합니다.

남은 가장 가까운 browser-docs drift 는 store-seeded actual-search empty-meta family 입니다. 다음 여섯 Playwright 시나리오는 이미 `e2e/tests/web-smoke.spec.mjs` 안에 구현되어 통과 상태로 존재하지만, README / ACCEPTANCE_CRITERIA / MILESTONES / TASK_BACKLOG 어디에도 inventory 되어 있지 않았습니다.

- `history-card entity-card store-seeded actual-search initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다` (line 4440)
- `history-card entity-card store-seeded actual-search 자연어 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다` (line 4546)
- `history-card entity-card store-seeded actual-search 다시 불러오기 reload-only 단계에서 empty-meta no-leak contract가 유지됩니다` (line 4665)
- `history-card entity-card store-seeded actual-search 다시 불러오기 후 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다` (line 4774)
- `history-card entity-card store-seeded actual-search 다시 불러오기 후 두 번째 follow-up 질문에서 empty-meta no-leak contract가 유지됩니다` (line 4899)
- `history-card entity-card store-seeded actual-search 자연어 reload 체인에서 empty-meta no-leak contract가 유지됩니다` (line 5034)

이 슬라이스는 브라우저 동작 자체는 건드리지 않고, 이미 구현되어 있는 여섯 시나리오가 실제로 assert 하는 사용자-가시 contract 만 네 개 doc 에 일관된 문체로 추가 기록합니다. 새 Playwright 테스트, selector 수정, 다른 family, service 테스트로는 번지지 않습니다.

## 핵심 변경

여섯 시나리오가 assert 하는 공통 / 단계별 계약:
- 모든 단계: 가시 `다시 불러오기` 버튼 유지, history-card 최상단 카드의 `.meta` count 가 `0`, 우발적 `.meta` 생성을 통한 `사실 검증` text leak 없음
- reload-only / follow-up / reload 체인 단계에서는 추가로 `WEB` badge, `설명 카드` answer-mode badge, `설명형 다중 출처 합의` verification label, `백과 기반` source role, `namu.wiki` / `ko.wikipedia.org` source path 가 visible continuity 로 유지

각 doc 에 다음과 같이 반영했습니다.

### `README.md`

90번 뒤에 91 / 92 / 93 / 94 / 95 / 96번을 추가했습니다.

- 91. store-seeded actual-search initial-render — zero-count `.meta` + `사실 검증` no-leak
- 92. store-seeded actual-search 자연어 reload-only — zero-count `.meta` + `사실 검증` no-leak + WEB / 설명 카드 / 설명형 다중 출처 합의 / 백과 기반 / namu.wiki / ko.wikipedia.org continuity
- 93. store-seeded actual-search click reload-only — 동일 계약
- 94. store-seeded actual-search click reload 후 first follow-up — 동일 계약 drift 없음
- 95. store-seeded actual-search click reload 후 second follow-up — 동일 계약 drift 없음
- 96. store-seeded actual-search 자연어 reload 체인(자연어 reload → follow-up → second follow-up) — 동일 계약 drift 없음

### `docs/ACCEPTANCE_CRITERIA.md`

- document-level browser coverage inventory count line 을 `90 core browser scenarios` → `96 core browser scenarios` 로 갱신 (count 의미 문맥 주석은 그대로 유지).
- latest-update news-only initial-render bullet 뒤에 여섯 개 store-seeded actual-search bullet 을 추가 (README 문체와 동일).

### `docs/MILESTONES.md`

- latest-update news-only initial-render browser smoke milestone 뒤에 여섯 개 store-seeded actual-search browser smoke milestone 을 추가 (기존 browser smoke milestone 문체 그대로).

### `docs/TASK_BACKLOG.md`

- 93번 뒤에 94 / 95 / 96 / 97 / 98 / 99번 항목을 추가.

service 테스트, Playwright 테스트 코드, pipeline 파일, `docs/projectH_pipeline_runtime_docs/`, 다른 family / docs section 은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -c "store-seeded actual-search" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - `README.md`: 6, `docs/ACCEPTANCE_CRITERIA.md`: 6, `docs/MILESTONES.md`: 6, `docs/TASK_BACKLOG.md`: 6, `e2e/tests/web-smoke.spec.mjs`: 12 (여섯 `test(...)` 제목 + 여섯 comment 라인).
- `rg -n "store-seeded actual-search|empty-meta no-leak contract|serialized zero-count empty-meta no-leak contract" ...` 로 네 doc 에 모두 여섯 새 bullet 이 원하는 문구로 들어갔음을 확인했습니다.
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음
- 브라우저/서비스 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright / `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- `docs/ACCEPTANCE_CRITERIA.md` 의 document-level browser coverage inventory count 는 이 라운드에서 `96` 으로 갱신되었지만, `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` 가 반환하는 raw file-level `test(...)` 카운트와는 여전히 서로 다른 축의 카운트입니다. 두 축의 실제 매핑 audit 은 이 라운드 범위 밖입니다.
- `e2e/tests/web-smoke.spec.mjs` 에는 entity-card / dual-probe / zero-strong / actual-search 외에도 추가 empty-meta / meta-contract 계열이 더 있을 수 있고, 이 라운드에서 재검색되지 않았습니다. 필요 시 별도 audit 라운드에서 다룰 여지가 있습니다.
- TASK_BACKLOG 쪽의 대문자 `History-card` 관행과 README / ACCEPTANCE_CRITERIA / MILESTONES 의 소문자 `history-card` 관행 차이는 기존 inventory 라인과 문체를 맞춘 결과입니다. 별도 문체 정합성 정리가 필요한지 여부는 이 라운드 범위 밖입니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
