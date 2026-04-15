## 변경 파일
- `verify/4/11/2026-04-11-history-card-latest-update-noisy-community-click-reload-browser-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/11/2026-04-11-history-card-latest-update-noisy-community-click-reload-browser-truth-sync-bundle.md`가 주장한 noisy-community click-reload browser truth-sync가 실제 Playwright fixture/assertion과 isolated rerun 결과에 부합하는지 truthfully 다시 확인해야 했습니다.
- 확인이 끝난 뒤에는 같은 noisy-community latest-update family 안에서 남은 user-visible browser gap 한 개만 다음 Claude 구현 슬라이스로 남겨야 했습니다.

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs`의 noisy-community click-reload show-only 시나리오가 실제로 current service/docs truth로 정렬되어 있음을 확인했습니다 (`e2e/tests/web-smoke.spec.mjs:2361`).
- 프리시드 `record.response_origin`은 이제 `label: "외부 웹 최신 확인"`, `kind: "assistant"`, `model: null`, `verification_label: "기사 교차 확인"`, `source_roles: ["보조 기사"]`를 직접 사용합니다 (`e2e/tests/web-smoke.spec.mjs:2414`, `e2e/tests/web-smoke.spec.mjs:2423`).
- history item fixture도 `verification_label: "기사 교차 확인"` / `source_roles: ["보조 기사"]`로 정렬되어 있습니다 (`e2e/tests/web-smoke.spec.mjs:2437`, `e2e/tests/web-smoke.spec.mjs:2447`).
- visible assertion도 같은 truth를 직접 잠그고, stale mixed-source 값 `공식 기반` / `공식+기사 교차 확인` 누출까지 음수로 막고 있습니다 (`e2e/tests/web-smoke.spec.mjs:2466`, `e2e/tests/web-smoke.spec.mjs:2477`).
- latest `/work` 설명처럼 full-title `-g`는 실제로 Playwright regex 매칭에 실패했습니다. 같은 제목을 가진 시나리오는 파일 내 1건뿐이어서, prefix `-g "history-card latest-update 다시 불러오기 후 noisy community source"`로 재실행했을 때 정확히 그 시나리오 1건만 선택되어 통과했습니다.
- same-family next slice는 `history-card latest-update noisy-community natural-reload reload-only browser smoke + docs bundle`로 좁혔습니다. 현재 docs와 browser smoke는 mixed/single/news-only natural-reload reload-only는 적고 있지만 noisy-community natural-reload reload-only는 비어 있습니다 (`README.md:183`, `README.md:185`, `README.md:192`, `docs/ACCEPTANCE_CRITERIA.md:1410`, `docs/ACCEPTANCE_CRITERIA.md:1412`, `docs/ACCEPTANCE_CRITERIA.md:1419`, `docs/MILESTONES.md:93`, `docs/MILESTONES.md:95`, `docs/MILESTONES.md:99`, `docs/TASK_BACKLOG.md:79`, `docs/TASK_BACKLOG.md:81`, `docs/TASK_BACKLOG.md:88`). 현재 `e2e/tests/web-smoke.spec.mjs`도 noisy natural-reload browser coverage는 follow-up / second-follow-up 2건만 있고 reload-only는 없습니다 (`e2e/tests/web-smoke.spec.mjs:9369`, `e2e/tests/web-smoke.spec.mjs:9446`).

## 검증
- 코드 대조:
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2361,2498p'`
  - `rg -n "history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 \\+ 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - `nl -ba README.md | sed -n '140,196p'`
  - `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1368,1424p'`
  - `nl -ba docs/MILESTONES.md | sed -n '50,102p'`
  - `nl -ba docs/TASK_BACKLOG.md | sed -n '24,92p'`
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '9365,9520p'`
- isolated browser rerun:
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다" --reporter=line`
  - 결과: `Error: No tests found.`
  - 해석: `/work` note가 적은 것처럼 full-title regex는 `+` / `·` 등 특수문자 때문에 안정적으로 매칭되지 않았습니다.
  - 재실행: `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source" --reporter=line`
  - 결과: `Running 1 test using 1 worker` 후 `1 passed (7.8s)`
- 포맷 확인:
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/11`
  - 결과: 출력 없음
- service 파일은 이번 라운드에서 바뀌지 않았으므로 `tests/test_web_app.py` 재실행은 하지 않았습니다.

## 남은 리스크
- noisy-community latest-update browser family에는 natural-reload reload-only branch의 직접 smoke coverage와 문서 항목이 아직 없습니다.
- 그 reload-only browser branch를 닫기 전까지는 same-family user-visible 흐름 한 개가 Playwright와 README/acceptance/milestone/backlog coverage 밖에 남습니다.
- 작업 트리는 여전히 dirty 상태이므로 다음 구현 라운드는 기존 pending `/verify`, `/work`, 그리고 untracked `docs/projectH_pipeline_runtime_docs/`를 되돌리거나 정리하지 않고 지정된 파일 범위만 좁게 수정해야 합니다.
