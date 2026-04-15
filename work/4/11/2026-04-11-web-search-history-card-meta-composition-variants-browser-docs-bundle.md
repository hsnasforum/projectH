# web-search history-card meta-composition variants browser docs bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `work/4/11/2026-04-11-web-search-history-card-meta-composition-variants-browser-docs-bundle.md`

## 사용 skill

- 없음

## 변경 이유

같은 날 `/work`에서 entity-card meta-contract, latest-update empty-meta, store-seeded actual-search empty-meta, zero-strong-slot missing-only count-summary, dual-probe mixed count-summary, strong-plus-missing count-summary reload-path, single-source count-summary + progress-summary reload-path까지 browser-docs truth-sync가 여러 번 반복되었습니다. 가장 최근 `/work` + `/verify`가 single-source count-summary + progress-summary 라인을 닫았지만, `e2e/tests/web-smoke.spec.mjs`의 `web-search history card header badges` 시나리오가 이미 잠그고 있는 exact `.meta` composition variants 네 종류(card6 investigation mixed count+progress, card7 general label+count+progress, card8 general label+count-only, card9 general label+progress-only)는 여전히 네 doc 어디에도 한 줄도 반영되어 있지 않아 인접한 docs drift로 남아 있었습니다. 또 한 번 한 줄짜리 docs-only micro-slice로 쪼개는 대신, 이 네 variant를 한 바운드의 docs 번들로 한꺼번에 닫았습니다. 브라우저 동작, Playwright 테스트, service 테스트, pipeline 파일, `docs/projectH_pipeline_runtime_docs/`, 다른 family에는 손대지 않았습니다.

## 핵심 변경

Playwright `web-search history card header badges` 시나리오가 이미 assert 하고 있는 네 composition variant:

- investigation mixed count+progress (`spec.mjs:1294`, card6): multi-category count-summary + non-empty progress summary → `.meta` = `사실 검증 교차 확인 2 · 단일 출처 1 · 혼합 지표: 교차 확인과 단일 출처가 함께 관찰되었습니다.`, count-summary가 progress-summary 앞에, `설명 카드` / `최신 확인` / `일반 검색` answer-mode leak 없음, composed line에 leading/trailing separator artifact 없음.
- general label+count+progress (`spec.mjs:1315`, card7): general answer-mode + multi-category count-summary + non-empty progress summary → `.meta` = `일반 검색 · 사실 검증 교차 확인 2 · 단일 출처 1 · 일반 지표: 커뮤니티 단서와 교차 확인이 함께 관찰되었습니다.`, 순서는 `label → count → progress`로 고정, `혼합 지표:` / `설명 카드` / `최신 확인` investigation leak 없음, composed line에 leading/trailing separator artifact 없음.
- general label+count-only (`spec.mjs:1338`, card8): general answer-mode + single-category count-summary + empty progress summary → `.meta` = `일반 검색 · 사실 검증 교차 확인 2`, label 뒤에 count-only segment만, `일반 진행:` / `혼합 지표:` / `일반 지표:` / `설명 카드` / `최신 확인` absent segment leak 없음, composed line에 leading/trailing separator artifact 없음.
- general label+progress-only (`spec.mjs:1361`, card9): general answer-mode + empty count-summary + non-empty progress summary → `.meta` = `일반 검색 · 일반 진행: 커뮤니티 단서가 단일 출처 상태로 남아 있습니다.`, label 뒤에 progress-only segment만, `사실 검증` / `혼합 지표:` / `일반 지표:` / `설명 카드` / `최신 확인` absent segment leak 없음, composed line에 leading/trailing separator artifact 없음.

각 doc에 다음과 같이 반영했습니다.

### `README.md`

기존 119번 뒤에 120 / 121 / 122 / 123번을 추가해 네 variant를 한국어 inventory 문체로 기술했고, 각 라인에서 `label → count → progress` 순서와 no-leak / no-artifact 계약을 명시했습니다.

### `docs/ACCEPTANCE_CRITERIA.md`

- document-level browser coverage inventory count 문장을 `119 core browser scenarios` → `123 core browser scenarios`로 갱신(문맥 주석은 그대로 유지).
- 직전 single-source count-summary + progress-summary 자연어 reload second-follow-up bullet 뒤에 네 variant bullet을 한국어 문체로 동일하게 추가.

### `docs/MILESTONES.md`

- 직전 single-source count-summary + progress-summary 자연어 reload second-follow-up browser smoke milestone 뒤에 네 variant browser smoke milestone을 영어 문체로 추가.

### `docs/TASK_BACKLOG.md`

- 122번 뒤에 123 / 124 / 125 / 126번 항목을 영어 문체로 추가.

service 테스트, Playwright 테스트 코드, pipeline 파일, `docs/projectH_pipeline_runtime_docs/`, 다른 family / docs section은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -n "사실 검증 교차 확인 2 · 단일 출처 1 · 혼합 지표:|일반 검색 · 사실 검증 교차 확인 2 · 단일 출처 1 · 일반 지표:|일반 검색 · 사실 검증 교차 확인 2|일반 검색 · 일반 진행:" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - 네 doc 각각에 네 composition literal이 한 줄씩 모두 등장했고, 대응 Playwright assert 라인(`spec.mjs:1294`, `spec.mjs:1315`, `spec.mjs:1338`, `spec.mjs:1361`)과 문자열이 정확히 일치함을 확인했습니다.
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음.
- 브라우저 / 서비스 / 코드 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright `make e2e-test`와 `tests/test_web_app.py` 재실행은 이번 라운드 범위 밖입니다.

## 남은 리스크

- `docs/ACCEPTANCE_CRITERIA.md`의 document-level browser coverage inventory count는 이번 라운드에서 `123`으로 갱신되었지만, `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs`가 반환하는 raw file-level `test(...)` 카운트와는 여전히 서로 다른 축의 숫자이고, 두 축 사이의 실제 매핑 audit은 이 라운드 범위 밖입니다.
- `e2e/tests/web-smoke.spec.mjs`의 같은 `web-search history card header badges` 시나리오에는 card1~card5 등 다른 `.meta` assertion도 존재하며 (예: 초기 WEB badge / single-source count / investigation latest-update progress 진행 라인), 이 라운드에서는 card6~card9 composition variants에만 문서 inventory를 맞췄습니다. 나머지 card 라인에 대해 별도 docs drift가 있는지 여부는 이번 라운드 범위 밖입니다.
- TASK_BACKLOG 쪽의 대문자 `History-card` / `Entity-card` 관행과 README / ACCEPTANCE_CRITERIA / MILESTONES의 소문자 관행 차이는 기존 inventory 라인 문체에 맞춘 결과이며, 별도 문체 정합성 정리가 필요한지 여부는 이번 라운드 범위 밖입니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `controller/server.py`, `pipeline_gui/backend.py`, `watcher_core.py`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `verify/4/10/...`, 기존 `work/4/11/`와 `verify/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았습니다.
