# 2026-04-16 controller background asset path fix verification

## 변경 파일

- `verify/4/16/2026-04-16-controller-office-reset-base-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 인 `work/4/16/2026-04-16-controller-background-asset-path-fix.md` 의 주장을 현재 tree 기준으로 다시 확인하고, 이번 round 에 실제 필요한 최소 검증만 재실행한 뒤 다음 exact slice 하나를 고정하기 위한 verification 라운드입니다. 현재 범위는 shipped `app.web` 가 아니라 internal `controller.server` tooling 이므로, 다음 슬라이스도 같은 controller Office View family 안의 current-risk reduction 으로만 좁혔습니다.

## 핵심 변경

- 최신 `/work` 의 핵심 주장은 현재 tree 와 맞습니다.
  - `controller/index.html` 의 Office View background preload 는 현재 `_bgImg.src = '/controller-assets/background.png';` 를 사용합니다.
  - `tests/test_controller_server.py` 의 정적 HTML contract test 도 `/controller-assets/background.png` 포함을 확인합니다.
  - `rg -n "background\\.png|bg-office\\.png" controller/index.html tests/test_controller_server.py` 결과, live code/test 에는 더 이상 `bg-office.png` 참조가 남아 있지 않습니다.
- asset layout 에는 `/work` 보다 조금 더 넓은 nuance 가 있습니다.
  - 현재 tree 에는 `controller/assets/background.png` 와 `controller/assets/generated/bg-office.png` 가 둘 다 존재합니다.
  - 다만 `controller/server.py` asset shim 은 `/controller-assets/<rel_path>` 를 `controller/assets/` 기준으로 그대로 해석하므로, 이전 `/controller-assets/bg-office.png` 경로는 현재 layout 에서 generated copy 를 자동으로 찾지 못합니다.
  - 따라서 이번 `/work` 의 실질적 결론, 즉 "현재 truthful 한 root asset route 는 `/controller-assets/background.png` 다" 는 유지됩니다.
- focused 자동 검증은 모두 통과했습니다.
  - `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - `git diff --check -- controller/index.html tests/test_controller_server.py`
- docs/root scope 도 다시 확인했습니다.
  - root docs 와 runtime docs 는 controller Office View 를 internal read-model tooling 으로만 설명하고 있으며, 배경 자산의 구체 경로를 shipped contract 로 고정하지 않습니다.
  - 따라서 이번 verify 기준으로는 product/runtime docs sync 가 새로 필요하지 않습니다.
- 다음 exact slice 는 `controller office background preload readiness hardening` 으로 고정합니다.
  - 현재 background preload 는 `_bgImg.src` 를 먼저 할당하고 `onload` 를 나중에 붙입니다.
  - 같은 파일 안의 `SpriteManager` 는 `complete` / `naturalWidth` 기반 readiness 를 매 tick 다시 확인하지만, background path 는 `_bgReady` boolean 하나에만 의존합니다.
  - 그래서 경로가 바로잡힌 뒤에도 cached fast-path readiness 누락이나 silent flat-color fallback 이 남을 수 있으므로, 이 지점이 같은 family 의 가장 가까운 current-risk reduction 입니다.

## 검증

- `ls -lt work/4/16 verify/4/16`
  - 결과: `work/4/16/2026-04-16-controller-background-asset-path-fix.md` 가 오늘 최신 `/work` 임을 확인했고, current `/verify` note 는 그보다 오래된 stale content 였습니다.
- `nl -ba controller/index.html | sed -n '770,785p'`
  - 결과: `_bgImg.src = '/controller-assets/background.png';` 와 `_bgImg.onload = () => { _bgReady = true; };` 의 현재 구현 위치를 재확인했습니다.
- `nl -ba tests/test_controller_server.py | sed -n '85,100p'`
  - 결과: controller HTML contract test 가 `/controller-assets/background.png` 포함을 실제로 확인하고 있음을 재확인했습니다.
- `ls -l controller/assets controller/assets/generated`
  - 결과: `controller/assets/background.png` 와 `controller/assets/generated/bg-office.png` 가 함께 존재함을 확인했습니다.
- `rg -n "background\\.png|bg-office\\.png" controller/index.html tests/test_controller_server.py`
  - 결과: live code/test 에는 `/controller-assets/background.png` 만 남고, `bg-office.png` 는 더 이상 참조되지 않습니다.
- `rg -n "Office View|controller.server|generated/office-sprite-manifest|animation assets" README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: controller Office View 는 internal/operator tooling read-model 로만 문서화되어 있고, 이번 라운드와 충돌하는 background path hardcode 는 찾지 못했습니다.
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.001s`, `OK`
- `git diff --check -- controller/index.html tests/test_controller_server.py`
  - 결과: 출력 없음
- full browser suite / manual controller smoke
  - 결과: 미실행. 이번 변경은 static HTML background path 와 contract test 확인 범위였고, shared browser helper 나 controller server route contract 자체를 바꾸지 않았으므로 wider rerun 은 과했습니다.

## 남은 리스크

- `_bgImg` preload 는 여전히 `src` 할당이 `onload` 등록보다 먼저라서 cached asset fast-path readiness 를 명시적으로 latch 하지 못합니다.
- background asset load failure 는 현재 flat-color fallback 외에 별도 operator-facing signal 이 없어, 다시 비슷한 자산 경로 문제가 생기면 진단이 늦을 수 있습니다.
- `controller/assets/generated/bg-office.png` duplicate copy 는 현재 live contract 밖에 남아 있어, background asset source-of-truth 를 어디에 둘지는 후속 라운드에서 더 명확히 정리할 여지가 있습니다.
