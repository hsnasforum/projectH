# docs/NEXT_STEPS browser smoke checkpoint truth-sync bundle

## 변경 파일

- `docs/NEXT_STEPS.md`
- `work/4/11/2026-04-11-next-steps-browser-smoke-checkpoint-truth-sync-bundle.md`

## 사용 skill

- 없음

## 변경 이유

같은 날 `/work`에서 entity-card meta-contract, latest-update empty-meta, store-seeded actual-search empty-meta, zero-strong-slot missing-only count-summary, dual-probe mixed count-summary, strong-plus-missing count-summary reload-path, single-source count-summary + progress-summary reload-path, 그리고 `web-search history card header badges` `.meta` composition variants까지 browser-docs truth-sync가 이미 여러 번 반복되었습니다. 직전 `/work` + `/verify`가 네 `README.md` / `docs/ACCEPTANCE_CRITERIA.md` / `docs/MILESTONES.md` / `docs/TASK_BACKLOG.md` doc에 composition variants 네 라인을 truthfully 닫았지만, root planning doc인 `docs/NEXT_STEPS.md`는 여전히 `Playwright smoke currently covers 82 browser scenarios`라는 stale 카운트를 쓰고, `web-search history card header badges`도 generic badge/progress-summary 계약 수준에만 머물러 있어 root doc만 혼자 drift 상태였습니다. 또 한 번 한 줄짜리 docs-only micro-slice로 쪼개는 대신, 남은 root planning drift를 한 바운드의 docs 번들로 한꺼번에 닫았습니다. 코드, 테스트, pipeline 파일, 다른 docs family, reviewed-memory 또는 milestone 섹션에는 손대지 않았습니다.

## 핵심 변경

### `docs/NEXT_STEPS.md` — `Current Checkpoint` 브라우저 smoke 단락

- `Playwright smoke currently covers 82 browser scenarios, including` 라인을 `Playwright smoke currently covers 123 core browser scenarios (document-level browser coverage inventory count, aligned with docs/ACCEPTANCE_CRITERIA.md:1351, not the raw test(...) count in e2e/tests/web-smoke.spec.mjs), including`로 교체해 root-doc 카운트를 `docs/ACCEPTANCE_CRITERIA.md:1351`의 `123 core browser scenarios` 계약에 맞췄습니다. 카운트 의미가 raw `test(...)`가 아닌 document-level inventory임을 root doc에서도 명시해 두 축이 섞이지 않도록 했습니다.
- 기존 `web-search history card header badge contract` 조각 바로 뒤에 `web-search history card header badges` `.meta` composition variants 네 종류를 다음 순서로 이어 붙였습니다. 각 variant는 이미 `e2e/tests/web-smoke.spec.mjs:1294/1315/1338/1361`이 잠그고 있고 네 root doc이 동일한 문구로 먼저 닫아 둔 계약입니다.
  - investigation mixed count+progress: `사실 검증 교차 확인 2 · 단일 출처 1 · 혼합 지표: 교차 확인과 단일 출처가 함께 관찰되었습니다.`, count-summary가 progress-summary 앞, `설명 카드` / `최신 확인` / `일반 검색` answer-mode leak 없음, composed line에 leading/trailing separator artifact 없음.
  - general label+count+progress: `일반 검색 · 사실 검증 교차 확인 2 · 단일 출처 1 · 일반 지표: 커뮤니티 단서와 교차 확인이 함께 관찰되었습니다.`, `label → count → progress` 순서 고정, `혼합 지표:` / `설명 카드` / `최신 확인` investigation leak 없음, composed line에 leading/trailing separator artifact 없음.
  - general label+count-only: `일반 검색 · 사실 검증 교차 확인 2`, label 뒤에 count-only segment만, `일반 진행:` / `혼합 지표:` / `일반 지표:` / `설명 카드` / `최신 확인` absent segment leak 없음, composed line에 leading/trailing separator artifact 없음.
  - general label+progress-only: `일반 검색 · 일반 진행: 커뮤니티 단서가 단일 출처 상태로 남아 있습니다.`, label 뒤에 progress-only segment만, `사실 검증` / `혼합 지표:` / `일반 지표:` / `설명 카드` / `최신 확인` absent segment leak 없음, composed line에 leading/trailing separator artifact 없음.

다른 `Current Checkpoint` 불릿, `Recent Memory Entry Slice`, milestone, roadmap 등 `docs/NEXT_STEPS.md`의 다른 섹션과 다른 doc은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -n "82 browser scenarios|123 core browser scenarios|web-search history card header badge contract|history card header badges|일반 검색 · 일반 진행:" docs/NEXT_STEPS.md docs/ACCEPTANCE_CRITERIA.md README.md e2e/tests/web-smoke.spec.mjs`
  - `docs/NEXT_STEPS.md`에서 `82 browser scenarios` 출현이 사라지고 `123 core browser scenarios` + `web-search history card header badges` `.meta` composition 네 variant가 한 라인 내에 나란히 등장함을 확인했습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:1351`과 `README.md`의 기존 browser inventory는 이 슬라이스에서 수정하지 않았고, 여전히 `123 core browser scenarios` 축과 composition literal 네 개를 포함하고 있음을 확인했습니다.
  - `e2e/tests/web-smoke.spec.mjs:1102`의 `web-search history card header badges` 테스트와 `spec.mjs:1361`의 `일반 검색 · 일반 진행:` literal이 문서 문구와 정확히 대응함을 확인했습니다.
- `git diff --check -- docs/NEXT_STEPS.md work/4/11` → whitespace 경고 없음.
- 브라우저 / 서비스 / 코드 계약은 이번 슬라이스에서 건드리지 않았으므로 Playwright `make e2e-test`와 `tests/test_web_app.py` 재실행은 이 라운드 범위 밖입니다.

## 남은 리스크

- `docs/NEXT_STEPS.md`의 `Current Checkpoint` 브라우저 smoke 단락은 여전히 한 개의 매우 긴 줄로 유지되어 있고, 이번 슬라이스는 composition variant 삽입 외에는 문장 재구성을 하지 않았습니다. 가독성을 위한 bullet 재편성 여부는 이번 라운드 범위 밖입니다.
- root-doc `123 core browser scenarios` 축과 `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` raw `test(...)` 카운트는 여전히 서로 다른 축이며, 두 축 사이의 실제 매핑 audit은 여전히 열려 있는 문제입니다.
- `docs/NEXT_STEPS.md` 안의 다른 Current Checkpoint 불릿, reviewed-memory 세부 항목, roadmap / milestone 섹션에도 stale 문구가 남아 있을 수 있지만, 이 슬라이스는 browser smoke checkpoint 카운트와 header-badges composition variants에만 국한된 변경입니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `controller/server.py`, `pipeline_gui/backend.py`, `watcher_core.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `verify/4/10/...`, 기존 `work/4/11/`와 `verify/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았습니다.
