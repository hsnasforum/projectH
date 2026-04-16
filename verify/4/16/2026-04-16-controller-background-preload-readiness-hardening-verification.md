# 2026-04-16 controller office toolbar storage-unavailable indicator verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-controller-office-toolbar-storage-unavailable-indicator.md`가 주장한 toolbar-level storage fallback visibility가 현재 코드, docs, focused 검증 기준으로 사실인지 다시 확인하는 라운드입니다.
- 사용자가 이번 round에서도 기존 verify 경로 `verify/4/16/2026-04-16-controller-background-preload-readiness-hardening-verification.md`를 재사용하도록 지정했으므로, 이번 note는 같은 경로를 update-in-place 하되 내용은 최신 `/work` 검증 truth로 갱신합니다.

## 핵심 변경
- `work/4/16/2026-04-16-controller-office-toolbar-storage-unavailable-indicator.md`의 핵심 주장은 현재 tree와 맞습니다.
  - `controller/index.html`에는 `.toolbar .storage-warn` 스타일, toolbar의 `#storage-warn` element, 그리고 BOOT 구간의 `if (!PrefStore.available) { ... }` 표시 gate가 실제로 들어 있습니다.
  - warning chip tooltip은 `localStorage 사용 불가 — 새로고침 시 toolbar 설정이 초기화됩니다`로 명시돼 있고, 현재 구현은 runtime authority가 아니라 browser-local persistence fallback만 안내합니다.
  - `tests/test_controller_server.py`의 `ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`는 `storage-warn`, `설정 비저장`, `PrefStore.available` 토큰을 정적으로 확인하며 focused rerun이 통과했습니다.
  - `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`에도 toolbar chip 계약과 browser-local 안내 성격이 실제로 들어 있습니다.
- `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/superpowers/plans/2026-04-16-controller-office-view-projecth-adaptation.md`를 다시 확인한 결과, controller/Office View는 여전히 shipped `app.web` release gate 밖 internal/operator tooling입니다. 따라서 다음 슬라이스도 같은 controller Office View family 안의 bounded current-risk reduction으로만 좁히는 편이 맞습니다.
- 현재 tree에는 controller 전용 real-browser smoke가 아직 없습니다. `e2e/tests/`에는 `web-smoke.spec.mjs`만 있고, controller 관련 검증은 이번 라운드 기준 여전히 `tests/test_controller_server.py` 중심의 static/unit 계약에 머물러 있습니다.

## 검증
- `ls -lt work/4/16 | sed -n '1,20p'`
  - 결과: `work/4/16/2026-04-16-controller-office-toolbar-storage-unavailable-indicator.md`가 오늘 최신 `/work`임을 확인했습니다.
- `ls -lt verify/4/16 | sed -n '1,20p'`
  - 결과: `verify/4/16/2026-04-16-controller-background-preload-readiness-hardening-verification.md`가 오늘 최신 `/verify`였고, 사용자 지정대로 같은 경로를 update-in-place 대상으로 재사용합니다.
- `nl -ba controller/index.html | sed -n '35,60p;228,240p;1968,1984p'`
  - 결과: `.toolbar .storage-warn`, toolbar `#storage-warn`, `PrefStore.available` boot gate를 재확인했습니다.
- `nl -ba tests/test_controller_server.py | sed -n '158,176p'`
  - 결과: `storage-warn`, `설정 비저장`, `PrefStore.available` static regression assertion이 실제로 들어 있음을 재확인했습니다.
- `nl -ba docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md | sed -n '220,232p'`
- `nl -ba docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md | sed -n '208,220p'`
  - 결과: toolbar chip contract와 browser-local fallback 안내가 두 runtime docs에 모두 반영돼 있음을 확인했습니다.
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.003s`, `OK`
- `git diff --check -- controller/index.html tests/test_controller_server.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: 출력 없음
- `tmp=$(mktemp --suffix=.js); trap 'rm -f "$tmp"' EXIT; awk '/<script>/{flag=1;next}/<\\/script>/{flag=0}flag' controller/index.html > "$tmp"; node --check "$tmp"`
  - 결과: 출력 없음
- `rg -n "storage-warn|설정 비저장|PrefStore\\.available" controller/index.html tests/test_controller_server.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: HTML/test/docs에서 storage warning token과 `PrefStore.available` 사용이 모두 확인됐습니다.
- `rg -n "/api/.*storage|/api/.*pref|route.*storage|route.*pref" controller/index.html controller/server.py || true`
  - 결과: 출력 없음 — backend route 추가 없음
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,240p' docs/TASK_BACKLOG.md`
- `sed -n '1,260p' docs/superpowers/plans/2026-04-16-controller-office-view-projecth-adaptation.md`
  - 결과: controller Office View가 internal/operator tooling으로 유지되고, browser-local preference는 허용되지만 shared runtime state로 승격되지 않음을 다시 확인했습니다.
- `find e2e/tests -maxdepth 2 -type f | sort`
- `rg -n "controller" e2e/tests tests | sed -n '1,240p'`
  - 결과: `e2e/tests/web-smoke.spec.mjs`만 존재하며 controller 전용 browser smoke는 아직 없음을 확인했습니다.
- manual controller/browser smoke
  - 결과: 미실행. 이번 verify round는 코드·docs·focused unit/static regression 재확인까지만 수행했습니다. 실제 브라우저에서 blocked-storage indicator가 어떻게 보이는지는 직접 실행하지 않았습니다.

## 남은 리스크
- `localStorage` 차단 환경에서 `#storage-warn` chip과 event log warning이 실제 browser에서 함께 보이는지는 아직 자동화되지 않았습니다.
- controller Office View는 internal/operator tooling이므로 현재 `app.web` release gate smoke와 분리돼 있습니다. 다음 슬라이스는 controller-only browser smoke로 좁히는 편이 맞습니다.
- selected-lane, layout/zoom 같은 다른 persistence 대상과 cross-browser sync는 여전히 현재 범위 밖입니다.
