# history-card latest-update noisy-community natural-reload reload-only browser smoke bundle

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-noisy-community-click-reload-browser-truth-sync-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-noisy-community-click-reload-browser-truth-sync-verification.md`)는 noisy-community latest-update click-reload show-only Playwright 시나리오의 pre-seed fixture와 visible assertion을 현재 shipped truth (`기사 교차 확인` / `보조 기사`)로 정렬했습니다. 또한 앞선 service 라운드들에서 noisy-community latest-update family (initial / click-reload show-only / natural-reload show-only / click-reload first·second follow-up / natural-reload first·second follow-up) 전체가 surface + stored 두 층 exact-field 계약으로 닫혀 있습니다.

남은 same-family user-visible gap은 natural-reload reload-only branch (`"방금 검색한 결과 다시 보여줘"` 만 호출하고 follow-up 없이 끝나는 경로) 의 browser smoke 커버리지였습니다. 브라우저 smoke에는 non-noisy 쪽에 해당 branch 시나리오가 이미 있고, noisy 쪽에는 follow-up / 두 번째 follow-up 시나리오만 존재하고 reload-only 단독 branch가 없어 docs 쪽에서도 drift가 남아 있었습니다. 이 슬라이스는 그 단일 branch 만 bounded 하나의 Playwright 시나리오로 추가하고, 동일 커버리지 truth를 README / ACCEPTANCE_CRITERIA / MILESTONES / TASK_BACKLOG 에 동기화합니다. service 테스트, 새 helper, 다른 family, 노이즈 follow-up 시나리오로는 번지지 않습니다.

## 핵심 변경

### `e2e/tests/web-smoke.spec.mjs`

- 기존 `history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다` 시나리오 바로 뒤에 새 시나리오 `history-card latest-update 자연어 reload noisy community 보조 커뮤니티 brunch 미노출 기사 교차 확인 보조 기사 hankyung mk 유지됩니다` 를 추가했습니다. 제목에서 regex-fragile punctuation (`·`, `/`, `+`) 을 제거했습니다.
- fixture 는 기존 noisy click-reload 시나리오 shape 을 그대로 재사용하고, `record.response_origin` 을 현재 shipped truth 로 고정했습니다:
  - `label: "외부 웹 최신 확인"`, `kind: "assistant"`, `model: null`
  - `verification_label: "기사 교차 확인"`, `source_roles: ["보조 기사"]`
  - stored `results` 는 여전히 `hankyung.com`, `mk.co.kr`, `brunch.co.kr` 세 개를 provenance 로 유지
- 실행 흐름은 기존 entity-card zero-strong-slot 자연어 reload 브라우저 시나리오 패턴 (`renderSearchHistory` + history-card `다시 불러오기` 클릭으로 서버 세션에 레코드 등록 → `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` 로 자연어 reload 호출) 을 그대로 따라갑니다. follow-up 호출은 추가하지 않았습니다.
- 자연어 reload 뒤 다음 assertion 을 잠급니다:
  - `#response-origin-badge` = `WEB`
  - `#response-answer-mode-badge` = `최신 확인`
  - `#response-origin-detail` 에 `기사 교차 확인` 과 `보조 기사` 포함
  - origin detail 에 `보조 커뮤니티`, `brunch`, `공식 기반`, `공식+기사 교차 확인` 없음 (현재 truth 와 stale mixed-source label 양쪽 leak 금지)
  - 응답 본문에 `brunch`, `로그인 회원가입 구독 광고` 없음
  - `#context-box` 에 `hankyung.com`, `mk.co.kr` 포함, `brunch` 없음
  - `historyBox .history-item` 첫 카드의 `.meta` count 가 0, `사실 검증` leak 없음
- 레코드 파일은 best-effort cleanup 으로 삭제합니다.

### Docs truth-sync

네 개 문서에 동일 branch 커버리지를 반영했습니다. 기존 follow-up / 두 번째 follow-up noisy 시나리오 라인과 문체를 맞춰 추가만 했고, 기존 라인 의미는 건드리지 않았습니다.

- `README.md`: 82번 뒤에 83번 항목 추가 (`history-card latest-update noisy community source가 "방금 검색한 결과 다시 보여줘" 자연어 reload-only 경로 ...`).
- `docs/ACCEPTANCE_CRITERIA.md`:
  - `Playwright smoke covers 82 core browser scenarios:` → `Playwright smoke covers 83 core browser scenarios:`
  - `latest-update noisy community source browser 자연어 reload 후 두 번째 follow-up → ...` 라인 뒤에 reload-only 라인 추가
- `docs/MILESTONES.md`: `latest-update noisy-community click-reload follow-up + second-follow-up exclusion ...` 라인 뒤에 natural-reload reload-only 라인 추가.
- `docs/TASK_BACKLOG.md`: 85번 뒤에 86번 항목 추가 (`History-card latest-update noisy-community natural-reload reload-only ... Playwright smoke coverage`).

service 테스트, pipeline 파일, 브라우저 helper, 다른 family, noisy follow-up 시나리오, `docs/projectH_pipeline_runtime_docs/` 는 건드리지 않았습니다.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 자연어 reload noisy community" --reporter=line` → `1 passed (6.9s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음
- service 계약은 이 슬라이스에서 건드리지 않았으므로 `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- 이 슬라이스는 new Playwright scenario 1 개만 추가했고, `rg -c '^\s*test\(' e2e/tests/web-smoke.spec.mjs` 로 재확인한 실제 raw `test(...)` 개수는 `104` 입니다 (이 노트 초기 버전에서 `105` 라고 기술한 것은 사실과 맞지 않아 후속 라운드에서 정정되었습니다). `docs/ACCEPTANCE_CRITERIA.md` 의 scenario count (`82` → `83`) 는 raw file-level `test(...)` 카운트가 아니라 document-level browser coverage inventory count 입니다. 두 숫자는 서로 다른 목적의 카운트이며, 이 슬라이스는 document-level inventory count 쪽만 `82 → 83` 으로 동기화했습니다. 실제 file-level `test(...)` 카운트와의 drift 는 이 라운드 범위 밖으로 남겨 두었습니다.
- entity-card / dual-probe / zero-strong / actual-search family 의 noisy natural-reload reload-only browser 시나리오 필요 여부는 이 라운드에서 확인하지 않았습니다.
- 저장소는 여전히 dirty 상태입니다 (`tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
