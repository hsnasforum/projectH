# 2026-04-16 controller remaining risk hardening

## 변경 파일
- `pipeline_gui/backend.py`
- `tests/test_pipeline_gui_backend.py`
- `controller/index.html`
- `tests/test_controller_server.py`
- `README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-remaining-risk-hardening.md`

## 사용 skill
- `security-gate`: runtime read-model hardening과 controller asset fallback이 local-first bounded surface 안에 머무는지 점검했습니다.
- `doc-sync`: background fallback/scene signal, stale reader fast-path truth를 README/runtime docs에 맞췄습니다.
- `work-log-closeout`: 이번 라운드의 실제 변경/검증/남은 리스크를 `/work` 형식으로 정리했습니다.

## 변경 이유
- 이전 라운드 기준 남은 리스크는 세 가지였습니다.
  - supervisor 비정상 종료 뒤 recent snapshot 에 pid 가 비어 있으면 stale fast-path 가 늦게 발동할 수 있음
  - raw `BROKEN` payload 는 supervisor 가 이미 없더라도 inactive field 정리가 보장되지 않음
  - controller background preload 는 `src` 할당이 `onload` 등록보다 먼저라 cached fast-path 누락과 무신호 fallback 위험이 있었음
- 추가 점검 결과 `controller/index.html` 에서 active compat/debug surface (`compat.control_slots`, `turn_state`, `/api/state`) 를 실제로 소비하는 흔적은 남아 있지 않았습니다. 따라서 controller 쪽 실질 원인은 dead-code 자체보다 background loader 경계였습니다.

## 핵심 변경
- `pipeline_gui/backend.py`
  - recent `RUNNING/DEGRADED` snapshot 이더라도 supervisor 가 없고 field 자체가 이미 `control=none`, `active_round=null`, watcher inactive, lane inactive 면 stale timeout 전에도 즉시 `BROKEN(supervisor_missing)` 으로 정규화하도록 보강했습니다.
  - raw `BROKEN` snapshot 도 supervisor 가 이미 없으면 reader 가 inactive field 를 함께 정리하도록 맞췄습니다.
- `tests/test_pipeline_gui_backend.py`
  - recent field-quiescent `RUNNING` snapshot 정규화 회귀 테스트와 `BROKEN + supervisor missing` inactive-field 정규화 회귀 테스트를 추가했습니다.
- `controller/index.html`
  - background loader 를 `background.png -> generated/bg-office.png` 순서의 fallback 체인으로 바꿨습니다.
  - `onload`/`onerror` 를 `src` 할당 전에 등록하고, `complete && naturalWidth` fast-path 를 명시적으로 latch 하도록 수정했습니다.
  - background fallback/error 는 event log 로 남기고, sidebar runtime info 에 `Scene` 상태(`loading`/`root`/`fallback`/`asset_error`)를 표시하도록 보강했습니다.
- `tests/test_controller_server.py`
  - background fallback 경로, `Scene` surface, `compat`/`turn_state` 미참조를 정적 HTML 계약으로 고정했습니다.
- `README.md`, `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - controller background fallback/readiness signal 과 reader stale fast-path 확장 truth 를 문서에 반영했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_controller_server`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/server.py tests/test_controller_server.py`
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/index.html tests/test_controller_server.py README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- 점검:
  - `rg -n "compat|control_slots|turn_state|runtimeData\\.compat|data\\.compat" controller/index.html tests/test_controller_server.py`
  - 결과: active compat/debug surface 참조 없음
  - `rg -n "_bgImg|_bgReady|background\\.png|bg-office|SpriteManager|generated/office-sprite-manifest|Office View|office-toggle|toggleOfficeView|compat|debug|attach|pause|resume|restart" controller/index.html`
  - 결과: controller 쪽 남은 actionable risk 는 background preload/readiness 경계로 수렴

## 남은 리스크
- recent snapshot 이면서 field 도 pid 도 모두 불완전한 경우는 여전히 stale timeout safety net 에 의존합니다.
- background fallback 은 root asset missing/cached race 를 흡수하지만, 자산 품질 자체가 어색하면 rendering 품질 문제는 별도 자산 정리 라운드가 필요합니다.
- `controller/index.html` 대규모 Office View diff 는 이제 compat/debug surface 문제보다 visual/layout polish 성격의 점검이 남아 있습니다.
