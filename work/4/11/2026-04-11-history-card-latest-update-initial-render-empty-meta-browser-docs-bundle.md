# history-card latest-update initial-render empty-meta browser docs bundle

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-entity-card-initial-render-meta-contract-browser-docs-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-entity-card-initial-render-meta-contract-browser-docs-verification.md`)는 history-card entity-card initial-render meta-contract 세 개 Playwright 시나리오를 네 개 doc에 inventory 동기화했습니다. 그 라운드의 마이너 기록 mismatch는 이미 최신 `/verify`에 잡혀 있고, 이 슬라이스에서 retroactive record-only 수정은 하지 않습니다.

남은 가장 가까운 browser-docs drift는 history-card latest-update initial-render empty-meta family입니다. 네 개 Playwright 시나리오가 이미 `e2e/tests/web-smoke.spec.mjs` 안에 구현되어 통과 상태로 존재하지만, README / ACCEPTANCE_CRITERIA / MILESTONES / TASK_BACKLOG 어디에도 inventory 되어 있지 않았습니다.

- `history-card latest-update noisy community source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다` (line 2250)
- `history-card latest-update mixed-source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다` (line 3397)
- `history-card latest-update single-source initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다` (line 3488)
- `history-card latest-update news-only initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다` (line 3566)

이 슬라이스는 브라우저 동작 자체는 건드리지 않고, 이미 구현되어 있는 네 시나리오가 실제로 assert하는 사용자-가시 contract를 네 개 doc에 일관된 문체로 추가 기록합니다. 새 Playwright 테스트, selector 수정, 다른 family (entity-card / dual-probe / zero-strong / actual-search), service 테스트로는 번지지 않습니다.

## 핵심 변경

네 시나리오가 공통으로 assert하는 계약:
- initial-render 단계만; click reload / 자연어 reload / follow-up 없음
- 가시 `다시 불러오기` 버튼 (클릭하지 않음)
- history-card 최상단 카드의 `.meta` count가 `0`
- 우발적 `.meta` 생성을 통한 `사실 검증` text leak 없음
- noisy-community variant는 추가로 history-card 전체에 `보조 커뮤니티` / `brunch` noisy 잔재가 노출되지 않음

각 doc에 다음과 같이 반영했습니다.

### `README.md`

86번 항목 뒤에 87 / 88 / 89 / 90번을 추가:
- 87. noisy community source initial-render — zero-count `.meta` + `사실 검증` no-leak + `보조 커뮤니티` / `brunch` negative
- 88. mixed-source initial-render — zero-count `.meta` + `사실 검증` no-leak
- 89. single-source initial-render — zero-count `.meta` + `사실 검증` no-leak
- 90. news-only initial-render — zero-count `.meta` + `사실 검증` no-leak

### `docs/ACCEPTANCE_CRITERIA.md`

- document-level browser coverage inventory count line을 `86 core browser scenarios` → `90 core browser scenarios`로 갱신 (count 의미 문맥 주석은 그대로 유지).
- history-card entity-card dual-probe initial-render bullet 뒤에 네 개 latest-update initial-render bullet을 추가.

### `docs/MILESTONES.md`

- history-card entity-card dual-probe initial-render browser smoke milestone 뒤에 네 개 latest-update initial-render browser smoke milestone을 추가.

### `docs/TASK_BACKLOG.md`

- 89번 뒤에 90 / 91 / 92 / 93번 항목을 추가.

service 테스트, Playwright 테스트 코드, pipeline 파일, `docs/projectH_pipeline_runtime_docs/`, 다른 family / docs section은 이 슬라이스에서 건드리지 않았습니다.

## 검증

- `rg -n "history-card latest-update noisy community source initial-render|history-card latest-update mixed-source initial-render|history-card latest-update single-source initial-render|history-card latest-update news-only initial-render|serialized zero-count empty-meta no-leak contract" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - `e2e/tests/web-smoke.spec.mjs:2250`, `:3397`, `:3488`, `:3566`에 네 시나리오 정의가 그대로 있습니다. README `87–90`, ACCEPTANCE_CRITERIA `1425–1428` 네 bullet, MILESTONES `105–108` 네 라인이 동일 시나리오를 doc-level 로 기록합니다.
  - `docs/TASK_BACKLOG.md`의 90 / 91 / 92 / 93번 항목은 handoff 의 정확 grep 패턴(`history-card ...`)과 capitalization (`History-card ...`)이 달라 위 `rg` 출력엔 직접 나오지 않지만, 직접 `grep -n "initial-render" docs/TASK_BACKLOG.md` 확인 시 90–93이 예상 문구로 존재하고, 이전 entity-card round에서도 동일 capitalization 기준으로 87–89 가 이미 들어가 있어 일관된 문체입니다.
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음
- 브라우저/서비스 계약은 이 슬라이스에서 건드리지 않았으므로 Playwright / `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- `docs/ACCEPTANCE_CRITERIA.md`의 document-level browser coverage inventory count는 이 라운드에서 `90`으로 갱신되었지만, `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs`가 반환하는 raw file-level `test(...)` 카운트와는 여전히 서로 다른 축의 카운트입니다. 두 축의 실제 매핑 audit은 이 라운드 범위 밖입니다.
- 같은 `e2e/tests/web-smoke.spec.mjs` 안에는 `history-card entity-card store-seeded actual-search initial-render 단계에서 serialized zero-count empty-meta no-leak contract가 유지됩니다` (line 4440) 과 같은 추가 initial-render 계열이 더 있을 수 있으며, 이 라운드에서 재검색되지 않았습니다. 필요 시 별도 audit 라운드에서 다룰 여지가 있습니다.
- TASK_BACKLOG 쪽의 대문자 `History-card` 관행과 README / ACCEPTANCE_CRITERIA / MILESTONES 의 소문자 `history-card` 관행 차이는 기존 inventory 라인과 문체를 맞춘 결과입니다. 별도 문체 정합성 정리가 필요한지 여부는 이 라운드 범위 밖입니다.
- 저장소는 여전히 dirty 상태입니다 (`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
