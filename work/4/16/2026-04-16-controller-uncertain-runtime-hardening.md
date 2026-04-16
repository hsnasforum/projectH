# 2026-04-16 controller uncertain runtime hardening

## 변경 파일
- `pipeline_gui/backend.py`
- `tests/test_pipeline_gui_backend.py`
- `controller/index.html`
- `tests/test_controller_server.py`
- `README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-uncertain-runtime-hardening.md`

## 사용 skill
- `doc-sync`: ambiguous runtime surface와 controller UI 계약 변화를 README/runtime docs에 맞췄습니다.
- `work-log-closeout`: 이번 라운드의 실제 변경, 검증, 남은 리스크를 `/work` 형식으로 정리했습니다.

## 변경 이유
- recent snapshot인데 supervisor/pid는 비어 있고 field는 덜 정리된 경우가 stale timeout 전까지 clean `RUNNING`처럼 보일 수 있었습니다.
- Office View는 compat/debug drift보다 시각 표현 정리가 남은 상태여서, runtime truth를 더 보수적으로 드러내고 modal/sidebar 표현도 함께 맞출 필요가 있었습니다.

## 핵심 변경
- `pipeline_gui/backend.py`
  - recent `RUNNING/DEGRADED` snapshot이 supervisor 없이 남아 있으면서 activity claim은 있지만 watcher/active lane pid로 live identity를 증명하지 못하면 `DEGRADED(supervisor_missing_recent_ambiguous)`로 정규화하도록 추가했습니다.
  - quiescent fast-path와 stale timeout `BROKEN(supervisor_missing)` fallback은 그대로 유지했습니다.
- `tests/test_pipeline_gui_backend.py`
  - recent ambiguous snapshot의 `DEGRADED` 정규화, aged ambiguous snapshot의 `BROKEN` 전환, supervisor alive 예외를 회귀 테스트로 고정했습니다.
- `controller/index.html`
  - runtime presentation helper를 추가해 toolbar badge, sidebar runtime info, event log가 같은 uncertain runtime 규칙을 공유하도록 맞췄습니다.
  - uncertain runtime에서는 `Control=uncertain`, `Round=uncertain`, `Watcher=Unknown`으로 내리고, ambiguous 진입/해제는 event log에 1회만 남기도록 조정했습니다.
  - log modal info strip에 wrap을 허용해 좁은 viewport에서도 잘리지 않게 했고, modal body의 전체 폭 사용은 유지했습니다.
- `tests/test_controller_server.py`
  - controller HTML static contract에 uncertain runtime helper, new badge classes, modal wrap CSS를 추가로 고정했습니다.
- `README.md`, `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - ambiguous recent incomplete snapshot은 즉시 `STOPPED/BROKEN`으로 단정하지 않고 uncertain `DEGRADED` surface로 보인다는 truth를 반영했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_controller_server`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/server.py tests/test_controller_server.py`
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/index.html tests/test_controller_server.py README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 남은 리스크
- `updated_at`이 없어서 recent/stale 판단 자체를 못 하는 snapshot은 여전히 기존 safety net 밖에 남습니다.
- watcher가 `alive=true`만 남기고 pid가 비어 있는 half-broken payload는 live identity 근거가 애매해, 이번 라운드에서는 즉시 추가 정규화하지 않았습니다.
- 실제 controller 서버를 띄운 수동 브라우저 smoke는 이번 라운드에서 미실행입니다. 현재 검증은 backend unit + controller static contract 범위입니다.
