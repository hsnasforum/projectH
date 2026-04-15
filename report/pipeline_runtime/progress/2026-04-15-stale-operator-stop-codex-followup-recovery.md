## 변경 파일
- watcher_core.py
- pipeline_runtime/supervisor.py
- tests/test_watcher_core.py
- tests/test_pipeline_runtime_supervisor.py
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- doc-sync

## 변경 이유
- stale operator stop을 suppression해서 `control=none`까지는 내렸지만, 그 뒤 runtime이 그냥 `READY` 셋으로 멈춰 보이는 빈칸이 남아 있었습니다.
- 사용자 관점에서는 “멈췄다”로 보였고, 실제 기대는 Codex가 다음 control을 다시 고르거나 Gemini 요청을 열도록 follow-up이 자동 재개되는 쪽이었습니다.

## 핵심 변경
- `watcher_core.py`
  - stale operator stop을 startup/rolling turn resolver에서도 정식 인식하게 했습니다.
  - stale stop이 active일 때는 `operator` 대신 `CODEX_FOLLOWUP`으로 전이합니다.
  - Codex에 `control_recovery` prompt를 보내 next control outcome(`claude_handoff` / `gemini_request` / `operator_request`) 중 하나를 다시 쓰게 합니다.
  - raw event에 `operator_request_stale_ignored`, `codex_control_recovery_notify`를 남깁니다.
- `pipeline_runtime/supervisor.py`
  - `turn_state=CODEX_FOLLOWUP`이면 active control seq가 없어도 Codex lane을 `WORKING`, note `followup`으로 surface하도록 보정했습니다.
- runtime 문서 세트에 stale stop auto-followup 규칙과 QA 항목을 추가했습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
- `python3 -m unittest -v tests.test_watcher_core tests.test_pipeline_runtime_supervisor`
- live restart:
  - `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --mode experimental --session aip-projectH --no-attach`
  - restart 후 `status.control = none`, `turn_state = CODEX_FOLLOWUP`, `Codex = WORKING/followup` 확인
  - Codex pane tail에서 stale stop control-recovery prompt와 `Working` 상태 확인

## 남은 리스크
- 이 변경은 “Codex follow-up을 다시 여는 것”까지입니다. Codex가 실제로 어떤 next control을 쓰는지는 여전히 prompt와 lane 상태, 그리고 후속 판단 품질에 달려 있습니다.
- stale operator stop 판정은 현재도 operator 문서 본문 안의 `work/...md` 경로와 job state `VERIFY_DONE` 일치에 의존합니다.
