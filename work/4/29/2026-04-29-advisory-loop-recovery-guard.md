# 2026-04-29 advisory loop recovery guard

## 변경 파일
- `watcher_core.py`
- `watcher_prompt_assembly.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/harness/advisory.md`
- `.pipeline/README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/4/29/2026-04-29-advisory-loop-recovery-guard.md`

## 사용 skill
- `security-gate`: stale advisory 취소, tmux Escape 회복, control routing 변경이 승인/저장/외부 publish 경계를 넘지 않는지 확인했습니다.
- `doc-sync`: runtime prompt, advisory harness, root memory의 대형 planning 문서 읽기 제한 지침을 같은 방향으로 동기화했습니다.
- `finalize-lite`: 변경 범위, 문서 동기화, 검증 사실, 남은 리스크를 handoff 전 점검했습니다.
- `work-log-closeout`: 구현 라운드의 변경 파일, 검증, 재발방지 근거를 `/work`에 기록했습니다.

## 변경 이유
- Gemini advisory lane이 `Thinking...` 상태에서 대형 planning 문서를 broad `cat`으로 읽고 오래 머무르며, 이전 stale advisory 회복이 다시 긴 대기처럼 보이는 문제가 반복됐습니다.
- 기본 advisory recovery 시간이 900초라 operator UI에서는 약 5분 이상 멈춰 보이는 동안도 회복이 늦었습니다.
- stale advisory request를 `STATUS: superseded`로 바꾼 뒤 다음 `CONTROL_SEQ` 계산이 superseded slot을 보지 않으면 같은 seq가 재사용될 수 있어, 후속 control 판정이 흐려질 수 있었습니다.

## 핵심 변경
- `watcher_core.py`
  - `DEFAULT_ADVISORY_RECOVERY_SEC = 300.0` 상수를 추가해 기본 stale advisory 회복 시간을 5분으로 고정했습니다.
  - `_get_next_control_seq()`가 active/stale slot뿐 아니라 `STATUS: superseded` control slot의 `CONTROL_SEQ`도 스캔하도록 바꿨습니다.
  - 같은 숫자의 control 재사용을 줄여 advisory recovery 이후 implement/verify follow-up이 단조 증가 seq를 받게 했습니다.
- `watcher_prompt_assembly.py`
  - `DEFAULT_ADVISORY_PROMPT`에 대형 planning 문서(`docs/TASK_BACKLOG.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`)를 broad full-file `cat`으로 읽지 말라는 지침을 추가했습니다.
  - 근거가 부족하면 장시간 탐색 대신 `INSUFFICIENT_CONTEXT`를 명시하도록 했습니다.
- `.pipeline/harness/advisory.md`
  - advisory owner의 기본 프로토콜에도 targeted `rg`/section read 우선 지침을 추가했습니다.
- `.pipeline/README.md`
  - 기본 `advisory_recovery_sec`가 300초이고, recovery가 visible busy age도 사용한다는 운영 설명을 맞췄습니다.
  - next `CONTROL_SEQ`가 superseded slot까지 포함해 계산된다는 내용을 추가했습니다.
- root memory 4종(`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`)
  - 대형 planning 문서는 필요한 섹션만 targeted read하고, 근거가 부족하면 `INSUFFICIENT_CONTEXT`로 닫는 규칙을 동기화했습니다.
- 테스트
  - 5분 기본 advisory recovery 상수 경로를 고정했습니다.
  - superseded control slot이 다음 `CONTROL_SEQ` 계산에 포함되는 회귀 테스트를 추가했습니다.
  - runtime supervisor prompt가 대형 문서 broad read 금지 지침을 포함하는지 확인하는 테스트를 추가했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py`
- 통과: `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_default_recovery_uses_five_minute_busy_indicator tests.test_watcher_core.BusyLaneNotificationDeferTest.test_next_control_seq_counts_superseded_control_slots tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_advisory_prompt_bounds_large_document_reads`
- 통과: `git diff --check -- watcher_core.py watcher_prompt_assembly.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/harness/advisory.md .pipeline/README.md AGENTS.md CLAUDE.md GEMINI.md PROJECT_CUSTOM_INSTRUCTIONS.md`
- 확인: `python3 -m pipeline_runtime.cli restart . --no-attach` 후 watcher가 새 pid로 재시작했고, runtime status에서 Gemini lane이 `READY`로 돌아왔습니다.
- 확인: 새 watcher command line에 대형 planning 문서 broad read 금지와 `INSUFFICIENT_CONTEXT` 지침이 포함됐습니다.
- 확인: `python3 -m pipeline_runtime.cli status . --json`에서 stale advisory request는 superseded됐고, verify owner가 후속 `implement_handoff.md`를 만들었습니다.

## 남은 리스크
- 이번 라운드는 runtime/prompt guard와 narrow unit regression에 한정했습니다. 브라우저 E2E와 장시간 soak는 실행하지 않았습니다.
- PR #91은 draft 상태이며, GitHub Actions check는 없는 상태로 확인됐습니다.
- 기존 untracked `work/`, `verify/`, `report/gemini/` 기록은 이번 변경 범위 밖이라 정리하지 않았습니다.
- active `implement_handoff.md`는 최초 6개 파일 기준으로 생성됐지만, 실제 doc-sync로 root memory 4개가 추가 변경됐습니다. 이 closeout은 실제 10개 변경 파일을 기준으로 기록합니다.
