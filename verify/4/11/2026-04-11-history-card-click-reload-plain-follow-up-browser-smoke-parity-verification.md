## 변경 파일
- `verify/4/11/2026-04-11-history-card-click-reload-plain-follow-up-browser-smoke-parity-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/11/2026-04-11-history-card-click-reload-plain-follow-up-browser-smoke-parity.md`가 browser click-reload 뒤 composer plain follow-up exact path용 Playwright smoke 2건을 추가했다고 기록했으므로, 실제 시나리오 정의와 isolated rerun 결과가 그 주장과 맞는지 다시 확인해야 했습니다.
- 이번 검증 뒤에는 같은 history reload browser family 안에서 다음 한 슬라이스만 정확히 고정해야 했습니다.

## 핵심 변경
- 최신 `/work`의 코드/테스트 설명은 대체로 현재 트리와 일치합니다. 새 시나리오 2건은 실제로 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1793)와 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L2388)에 존재하고, 둘 다 click reload 뒤 일반 composer 제출이 raw request body와 parsed payload 양쪽에서 `load_web_search_record_id`를 다시 보내지 않는다는 점을 직접 잠급니다.
- `/work`가 말한 브라우저 payload 분리 설명도 코드와 맞습니다. 일반 composer submit은 [app.js](/home/xpdlqj/code/projectH/app/static/app.js#L372)에서 `collectPayload()`가 `user_text`만 채우고, reload helper는 [app.js](/home/xpdlqj/code/projectH/app/static/app.js#L412) / `loadWebSearchRecord()` 경로에서만 `load_web_search_record_id`를 보냅니다. 이번 신규 Playwright도 그 실제 composer 경로를 타도록 작성돼 있습니다.
- isolated Playwright rerun 결과도 `/work` 주장과 일치했습니다. `-g "plain follow-up"` rerun은 정확히 위 두 신규 시나리오만 매치했고 `2 passed`로 끝났습니다.
- 다만 이번 라운드는 repo의 doc-sync 규칙까지 포함하면 아직 fully closed는 아닙니다. smoke coverage가 늘었는데도 현재 루트 문서군은 아직 그 변화를 truth-sync 하지 않았습니다. [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L23)와 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1352)는 아직 `123 core browser scenarios`를 유지하고 있고, [README.md](/home/xpdlqj/code/projectH/README.md#L243)는 browser smoke inventory가 item `123`에서 끝나며 이번 composer plain-follow-up 2건을 포함하지 않습니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L133)도 implemented Playwright inventory가 header-badge family에서 끝나고, 이번 exact browser contract pair는 아직 반영되지 않았습니다. `docs/MILESTONES.md`의 Playwright smoke suite bullet도 이번 exact contract를 따로 동기화하지 않았습니다.
- 따라서 최신 `/work`의 "바뀐 파일은 e2e/tests + /work"라는 사실 기록은 맞지만, 이 round는 AGENTS의 "test scenarios or smoke coverage changes" 문서 동기화 의무까지는 아직 닫지 못했습니다. 다음 control은 같은 family의 docs-only micro-slice가 아니라, 남은 smoke-doc drift를 한 번에 정리하는 bounded docs bundle로 고정했습니다.

## 검증
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "plain follow-up" --reporter=line` → `Running 2 tests using 1 worker` / 신규 entity-card plain-follow-up 시나리오 + 신규 latest-update plain-follow-up 시나리오 매치 / `2 passed (19.0s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/11` → 성공
- 이번 라운드는 Playwright-only smoke tightening 검수이므로 전체 `make e2e-test`나 전체 Python suite는 재실행하지 않았습니다.

## 남은 리스크
- 현재 가장 큰 same-family 리스크는 구현 동작이 아니라 문서 truth-sync입니다. browser smoke coverage가 늘었는데 root docs set이 아직 그 시나리오 pair와 inventory count를 같은 라운드 family 안에서 닫지 못했습니다.
- 저장소는 여전히 dirty 상태이며 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, 기존 docs family, 기존 `/work`와 `/verify`가 동시에 열려 있습니다. 다음 슬라이스도 `app.web` browser smoke docs bundle 안에만 묶는 편이 안전합니다.
