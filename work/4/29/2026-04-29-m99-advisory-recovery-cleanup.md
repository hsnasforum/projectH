# 2026-04-29 M99 advisory recovery cleanup 검증

## 변경 파일

- `watcher_core.py` — 사전 존재 dirty 변경 검증: `DEFAULT_ADVISORY_RECOVERY_SEC = 300.0` 상수화, stale advisory 다음 `CONTROL_SEQ` 계산이 superseded control slot까지 포함하도록 보강
- `tests/test_watcher_core.py` — 사전 존재 dirty 변경 검증: 5분 busy indicator 기반 advisory recovery 테스트와 superseded control slot seq 테스트 추가
- `watcher_prompt_assembly.py` — 사전 존재 dirty 변경 검증: advisory prompt에 대형 planning doc broad read 금지 및 `INSUFFICIENT_CONTEXT` 지침 추가
- `tests/test_pipeline_runtime_supervisor.py` — 사전 존재 dirty 변경 검증: supervisor advisory prompt가 shared default와 bounded read 지침을 포함하는지 확인
- `.pipeline/harness/advisory.md` — 사전 존재 dirty 변경 검증: advisory owner targeted reads 지침 추가
- `.pipeline/README.md` — 사전 존재 dirty 변경 검증: advisory recovery window 기본 300초 설명 및 superseded control seq 단조 증가 설명 반영
- `work/4/29/2026-04-29-m99-advisory-recovery-cleanup.md` — 이번 closeout

## 사용 skill

- `work-log-closeout` — `/work` closeout 필수 섹션, 실제 검증 기록, 남은 리스크 형식을 맞추기 위해 사용

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1445가 M99 advisory recovery cleanup follow-on에 대해 신규 코드 편집 없이 지정 검증만 실행하고 `/work` closeout을 남기도록 지시했다.
- handoff SHA `d9e1095736b7fcc82e7507f84c10eaf2102707b8ed8ad43ca947d085dd4f7751`가 요청값과 일치해 stale handoff가 아님을 확인했다.

## 핵심 변경

- 이번 implement 라운드에서 신규 코드 편집은 하지 않았다.
- `watcher_core.py`와 `watcher_prompt_assembly.py` 대상 `py_compile`을 통과했다.
- stale advisory default recovery 5분 busy indicator 단위 테스트를 통과했다.
- advisory prompt bounded read 단위 테스트를 통과했다.
- handoff가 지정한 6개 파일 대상 `git diff --check`를 통과했다.

## 검증

- `sha256sum .pipeline/implement_handoff.md` — PASS, `d9e1095736b7fcc82e7507f84c10eaf2102707b8ed8ad43ca947d085dd4f7751`
- `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py` — PASS
- `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_default_recovery_uses_five_minute_busy_indicator` — PASS, 1 test
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_advisory_prompt_bounds_large_document_reads` — PASS, 1 test
- `git diff --check -- watcher_core.py watcher_prompt_assembly.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/harness/advisory.md .pipeline/README.md` — PASS

## 남은 리스크

- 광범위 unittest, Playwright E2E, 장시간 soak는 handoff 범위가 아니어서 실행하지 않았다.
- `git status --short`에서 handoff가 지목한 6개 파일 외 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`의 기존 tracked dirty 변경이 관찰됐지만 이번 handoff 범위 밖이라 손대지 않았다.
- PR #91 CI와 이후 merge gate는 이번 implement handoff 범위가 아니며 기존 verify note의 남은 리스크로 유지된다.
