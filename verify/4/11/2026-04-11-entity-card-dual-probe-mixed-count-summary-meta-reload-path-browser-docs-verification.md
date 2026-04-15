## 변경 파일
- `verify/4/11/2026-04-11-entity-card-dual-probe-mixed-count-summary-meta-reload-path-browser-docs-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/11/2026-04-11-entity-card-dual-probe-mixed-count-summary-meta-reload-path-browser-docs-bundle.md`가 주장한 docs-only truth-sync가 실제 Playwright 시나리오와 문서 inventory에 맞는지 다시 확인해야 했습니다.
- 같은 날 같은 browser-docs family에서 docs-only truth-sync가 이미 여러 번 반복된 상태라, 이번 검증 후 다음 handoff도 더 작은 micro-slice가 아니라 남은 인접 drift를 한 번에 닫는 bounded docs bundle로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`는 현재 기준 truthful합니다.
- `e2e/tests/web-smoke.spec.mjs`의 dual-probe mixed count-summary reload-path family 4개 시나리오가 실제로 존재하고, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`가 같은 계약을 4개 inventory 라인으로 반영하고 있음을 다시 확인했습니다.
- `docs/ACCEPTANCE_CRITERIA.md`의 browser inventory count도 현재 `103 core browser scenarios`로 맞춰져 있음을 확인했습니다.
- 다음 단일 슬라이스는 `entity-card strong-plus-missing-count-summary-meta reload-path browser docs bundle`로 정했습니다. `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing meta를 reload-path에서 실제로 assert하는 actual-search/noisy-single-source tests가 여럿 존재하지만, 현재 문서 inventory는 initial-render 두 건만 직접 적고 있기 때문입니다.

## 검증
- 문서/시나리오 대조:
  - `rg -n "교차 확인 1 · 단일 출처 4|103 core browser scenarios|100\\.|101\\.|102\\.|103\\.|104\\.|105\\.|106\\." README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - `rg -c "교차 확인 1 · 단일 출처 4|mixed count-summary meta|dual-probe" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - `nl -ba README.md | sed -n '218,231p'`
  - `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1349,1455p'`
  - `nl -ba docs/MILESTONES.md | sed -n '112,128p'`
  - `nl -ba docs/TASK_BACKLOG.md | sed -n '111,122p'`
  - `rg -n "strong-plus-missing count-summary meta contract|missing-only count-summary meta|mixed count-summary meta|reload-only mixed count-summary meta|second-follow-up.*count-summary meta" e2e/tests/web-smoke.spec.mjs`
  - `rg -n "count-summary|사실 검증 교차 확인 3 · 미확인 2|사실 검증 교차 확인 1 · 단일 출처 4|사실 검증 미확인 5" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - `rg -n "^test\\(\\\".*(noisy single-source|actual-search|붉은사막 검색 결과 자연어 reload|다시 불러오기 후).*" e2e/tests/web-smoke.spec.mjs`
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3200,3260p'`
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5280,5465p'`
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '7448,7575p'`
  - `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '8320,8775p'`
- 포맷 확인:
  - `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/11`
  - 결과: 출력 없음
- docs-only truth-sync 라운드라서 Playwright, `tests/test_web_app.py`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `사실 검증 교차 확인 3 · 미확인 2` strong-plus-missing meta는 actual-search와 noisy single-source의 reload/follow-up/second-follow-up/natural-reload 경로들에서 이미 직접 assert되지만, 현재 문서 inventory는 initial-render 두 건만 직접 적고 있습니다.
- 같은 날 같은 browser-docs family에서 docs-only truth-sync가 여러 번 이어졌으므로, 다음 slice는 더 좁은 한 줄짜리 보정보다 위 strong-plus-missing reload-path 묶음을 한 번에 닫는 bounded docs bundle이어야 합니다.
- 저장소는 여전히 dirty 상태이며 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, `verify/4/10/2026-04-10-simple-entity-card-stored-origin-handoff-fixture-mismatch-verification.md`, `docs/projectH_pipeline_runtime_docs/`, 기존 `work/4/11/`, 기존 `verify/4/11/` 변경이 남아 있습니다.
