# 2026-04-19 controller role-bound office view

## 변경 파일
- controller/server.py
- controller/js/cozy.js
- tests/test_controller_server.py
- README.md
- docs/PRODUCT_SPEC.md
- docs/ACCEPTANCE_CRITERIA.md
- docs/projectH_pipeline_runtime_docs/02_요구사항_명세서.md
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- doc-sync: controller Office View의 role-bound 표시 변경을 README/runtime 문서와 함께 맞췄습니다.
- work-log-closeout: 이번 라운드 직접 수정 파일과 실제 검증만 기준으로 closeout 형식을 맞췄습니다.

## 변경 이유
- active profile을 A(`implement=Codex`, `verify=Claude`, `advisory=Gemini`)로 바꾼 뒤에도 controller Office View는 여전히 `Claude=implement`, `Codex=verify`를 하드코딩해 잘못 표시하고 있었습니다.
- `index.html`은 DOM shell만 담고 있고, 실제 오인은 shared runtime 모듈 `controller/js/cozy.js`의 고정 owner 가정과 controller status payload의 metadata 부재에서 발생했습니다.

## 핵심 변경
- `controller/server.py`가 `/api/runtime/status`와 placeholder payload에 active profile 기반 `role_owners`, `prompt_owners`, `enabled_lanes`를 함께 넣도록 확장했습니다.
- `controller/js/cozy.js`에 role-bound helper를 추가해 desk label, desk click target, tooltip role, delivery packet source/target, agent home zone이 runtime `role_owners`를 따르도록 바꿨습니다.
- `claude_desk` / `codex_desk` / `gemini_desk`는 각각 implement / verify / advisory role anchor key로 유지하고, visible owner만 바뀌도록 정리했습니다.
- `tests/test_controller_server.py`에 status metadata 포함 테스트를 추가하고, shared cozy runtime이 `role_owners` 기반 표시 helper를 포함하는지 고정했습니다.
- README와 runtime/controller 관련 문서에 Office View가 fixed owner가 아니라 active profile `role_owners` 기준으로 desk label/home-zone을 그린다고 명시했습니다.

## 검증
- `python3 -m py_compile controller/server.py tests/test_controller_server.py` → 통과
- `node --check controller/js/cozy.js` → 통과
- `python3 -m unittest -v tests.test_controller_server` → Ran 24 tests, OK
- `cd e2e && CONTROLLER_SMOKE_PORT=8782 npx playwright test -c playwright.controller.config.mjs --reporter=line` → 12 passed
- `git diff --check -- controller/server.py controller/js/cozy.js tests/test_controller_server.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/projectH_pipeline_runtime_docs/02_요구사항_명세서.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` → 통과

## 남은 리스크
- 이번 라운드는 Office View read-model 표시만 role-bound로 맞춘 것입니다. 다른 internal tooling 중 fixed owner wording이 남아 있는 문서/보조 화면이 있으면 후속 doc-sync가 더 필요할 수 있습니다.
- runtime payload에 `role_owners`가 비어 있는 비정상 profile 상태에서는 browser가 canonical fallback(`Claude/Codex/Gemini`)으로 보일 수 있습니다. 현재는 profile resolution 실패를 완전히 새 UI로 surface하지는 않았습니다.
