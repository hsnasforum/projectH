# history-card click-reload plain-follow-up browser smoke parity

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`
- `work/4/11/2026-04-11-history-card-click-reload-plain-follow-up-browser-smoke-parity.md`

## 사용 skill

- `superpowers:using-superpowers`

## 변경 이유

직전 `/work`와 `/verify`는 이미 service/backend 층에서 "브라우저 click reload 뒤 record id 없이 이어지는 plain follow-up" 경로에 대한 proof gap 을 `tests/test_web_app.py` 의 click-reload plain-follow-up 회귀 2건으로 닫았습니다. 같은 history-record reload 가족 안에 남은 current-risk 는 제품 동작 문제가 아니라, 실제 브라우저가 타는 shipped user-visible 경로 — 사용자가 history-card `다시 불러오기` 버튼을 눌러 `load_web_search_record_id` 만 보낸 뒤, 곧바로 일반 composer 에 입력해 plain follow-up 을 제출하는 흐름 — 에 대한 Playwright 브라우저 계약 proof 입니다.

기존 Playwright click-reload follow-up 시나리오들(entity-card `e2e/tests/web-smoke.spec.mjs:1751-1758`, latest-update `e2e/tests/web-smoke.spec.mjs:2217-2224`, noisy entity-card `e2e/tests/web-smoke.spec.mjs:10040-10041`)은 여전히 page-scope `sendRequest({ ..., load_web_search_record_id: rid }, "follow_up")` 로 두 번째 호출에도 `load_web_search_record_id` 를 수동으로 다시 실어 줍니다. 이는 실제 브라우저 경로가 아니며, click 뒤 평범한 입력창으로 보내는 post-click plain follow-up 계약을 lock 하지 못합니다. 실제 브라우저 코드는 이미 이 분리를 지원합니다 — reload 버튼은 `app/static/app.js:3064-3069` 에서만 `load_web_search_record_id` 를 실어 보내고, 일반 composer 제출은 `collectPayload()` / `buildSharedRequestSettings()` 기반이라 해당 필드를 포함하지 않습니다(`app/static/app.js:372-420`).

이 슬라이스는 tests-only 로 해당 정확한 browser click-reload → composer plain follow-up 경로를 entity-card 와 latest-update 양쪽에서 추가로 잠급니다. 구현/제품 docs/runtime/controller/pipeline 은 건드리지 않았습니다.

## 핵심 변경

### `e2e/tests/web-smoke.spec.mjs`

기존 entity-card click-reload follow-up 시나리오(`e2e/tests/web-smoke.spec.mjs:1645`) 바로 뒤, latest-update click-reload follow-up 시나리오(`e2e/tests/web-smoke.spec.mjs:2126`) 바로 뒤에 각각 신규 회귀 1건씩을 추가했습니다. 테스트 제목에는 `plain follow-up` 고정 substring 을 넣어 `-g "plain follow-up"` 개별 재실행이 항상 같은 두 시나리오만 집도록 했습니다.

- `history-card entity-card click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 top-level claim_coverage를 유지합니다`
  - 기존 entity-card follow-up 시나리오와 같은 single-weak-slot(`장르`, `단일 출처`, `단일 출처 상태 1건.`) 레코드를 디스크에 seed 하고 `renderSearchHistory(...)` 로 history card 를 그립니다.
  - Step 1 은 실제 브라우저 click: history-card 의 `다시 불러오기` 버튼을 누르고, `#response-origin-badge == WEB`, `#response-answer-mode-badge == 설명 카드`, `submit-request` 재-enable 까지 대기해 show-only reload 가 끝났음을 확인합니다. 이 경로는 `loadWebSearchRecord()` 가 `user_text: ""`, `load_web_search_record_id` 만 보내는 진짜 브라우저 reload 호출입니다.
  - Step 2 는 composer 경로로 plain follow-up 을 보냅니다. chat mode radio 를 체크하고, `#web-search-permission` 을 `enabled` 로 맞추고, `#user-text` 에 `"이 결과 한 문장으로 요약해줘"` 를 채운 뒤 `submit-request` 를 누릅니다. 이 submit 은 `collectPayload()` 를 통해 `/api/chat/stream` 으로 나가므로 `load_web_search_record_id` 를 재삽입하지 않습니다.
  - Playwright `page.waitForRequest` 로 실제 follow-up `/api/chat/stream` POST 를 잡고, `postData()` 원문과 파싱된 객체 양쪽에서 `load_web_search_record_id` 가 전혀 없음을 assert 합니다. raw body 의 `.toContain("load_web_search_record_id")` 금지, 파싱된 객체의 `hasOwnProperty` false 양쪽을 같이 잠가, 향후 key rename 이 되어도 회귀가 같이 터집니다. `user_text` 가 정확히 `"이 결과 한 문장으로 요약해줘"` 인지도 lock 합니다.
  - follow-up 이 settle 된 뒤 `#claim-coverage-box` 가 visible, `#claim-coverage-text` 에 `장르` 와 `[단일 출처]` 가 포함되어 있어 `_respond_with_active_context()` 의 entity-card claim_coverage propagation 이 top-level 로 올라왔음을 확인합니다. `historyBox` 의 첫 `.history-item .meta` 도 여전히 `사실 검증 단일 출처 1 · 단일 출처 상태 1건.` 을 유지합니다.

- `history-card latest-update click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 empty claim_coverage surfaces를 유지합니다`
  - 기존 latest-update follow-up 시나리오와 같은 mixed-source `스팀 여름 할인` 레코드(`claim_coverage=[]`, 빈 progress)를 디스크에 seed 하고 history card 를 그립니다.
  - Step 1 로 실제 `다시 불러오기` 클릭, `answerModeBadge == 최신 확인`, `submit-request` 재-enable 까지 대기.
  - Step 2 로 entity-card 쪽과 동일한 composer 경로(chat radio, `#web-search-permission=enabled`, `"이 결과 한 문장으로 요약해줘"`, submit)를 거쳐 plain follow-up 을 제출.
  - `page.waitForRequest` 로 실제 follow-up `/api/chat/stream` POST 를 잡고 raw body + 파싱된 객체 양쪽에서 `load_web_search_record_id` 부재를 assert. `user_text` 도 동일 lock.
  - follow-up settle 뒤 `#claim-coverage-box` 가 hidden, `historyBox` 의 `.history-item .meta` 가 여전히 `toHaveCount(0)` 임을 확인해 `_respond_with_active_context()` 의 latest-update / no-claim-coverage 게이트가 click-reload 진입로에서도 깨끗하게 유지된다는 걸 직접 증명합니다.

두 시나리오 모두 기존 reload-by-id / click-reload-by-id follow-up 패밀리는 수정하지 않고, 위치와 seed 데이터만 그 옆에 대칭으로 붙였습니다. 같은 `"이 결과 한 문장으로 요약해줘"` follow-up 문구를 공유해 기존 natural-language plain-follow-up 회귀 및 backend/service click-reload plain-follow-up 회귀와 쉽게 짝을 맞출 수 있습니다.

### 구현 / 제품 docs / runtime / controller / pipeline

`app/static/app.js`, `app/handlers/chat.py`, `core/agent_loop.py`, `app/serializers.py`, `docs/*`, `README.md`, `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, `scripts/`, `storage/web_search_store.py`, `tests/`(Playwright 외), 기타 docs family 는 이번 슬라이스에서 건드리지 않았습니다. 현재 구현이 이미 바르게 동작하고 있고(Playwright rerun 통과), 이 슬라이스가 필요한 것은 browser-level 계약 proof 뿐이기 때문입니다.

## 검증

- 신규 시나리오 isolated Playwright rerun:
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "plain follow-up" --reporter=line`
  - 결과: `Running 2 tests using 1 worker` → `2 passed (25.7s)`. 매치된 2건은 신규 entity-card click-reload plain-follow-up 시나리오와 신규 latest-update click-reload plain-follow-up 시나리오입니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/11` → whitespace 경고 없음.
- 이번 슬라이스는 browser smoke 추가만 했고 `app/static/app.js` 및 실제 구현/shared browser helper 는 건드리지 않았습니다. handoff 지시에 따라 `make e2e-test` 전체 rerun 은 생략했습니다(`다음 슬라이스가 실제로 shared browser drift 를 건드릴 때까지 isolated rerun 으로 충분`).

## 남은 리스크

- 두 신규 시나리오 모두 backend/service 층 click-reload plain-follow-up 회귀와 같은 `"이 결과 한 문장으로 요약해줘"` 문구를 공유합니다. 미래에 이 문구가 entity reinvestigation 슬롯 키워드(`개발`, `장르`, `플랫폼`, `출시`, `상태`)나 새 web-search 트리거(`검색`)에 포함되면, 백엔드가 `_respond_with_active_context()` 가 아닌 reinvestigation / 새 search 경로로 빠지면서 두 테스트가 같이 경로를 바꿉니다. 그 경우 문구와 어휘를 같은 라운드에서 같이 점검해야 합니다.
- 이 슬라이스는 Playwright tests-only 라 구현 회귀를 직접 막지는 못합니다. 미래에 `app/static/app.js:412-419` 의 `buildSharedRequestSettings()` / `collectPayload()` 가 실수로 `load_web_search_record_id` 를 자동 첨부하도록 바뀌거나, `_respond_with_active_context()` 의 propagation 블록이 사라지면, 두 시나리오가 entity-card 쪽(raw body `.not.toContain` + `claim-coverage-box` visibility + `.meta` 유지)과 latest-update 쪽(raw body `.not.toContain` + `claim-coverage-box` hidden + `.meta` 부재)에서 먼저 빨갛게 터집니다.
- 저장소는 여전히 기존 `/work`, `/verify`, `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, `docs/` 등 dirty 상태입니다. 이번 슬라이스는 `e2e/tests/web-smoke.spec.mjs` 와 이 closeout 노트만 추가로 수정했고, pending 파일들을 되돌리거나 커밋하지 않았습니다. handoff 의 "dirty worktree warning" 과 "app.web history reload browser contract 바깥은 건드리지 말라" 제약을 유지했습니다.
