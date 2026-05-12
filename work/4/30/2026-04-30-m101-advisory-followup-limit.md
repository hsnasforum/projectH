# 2026-04-30 M101 advisory recovery followup limit 검증

## 변경 파일

- `watcher_core.py` — 사전 존재 dirty 변경 검증: `ADVISORY_RECOVERY_FOLLOWUP_LIMIT = 2`, `_advisory_recovery_attempt_for_request()`, recovery prompt의 follow-up 허용 여부 계산
- `watcher_prompt_assembly.py` — 사전 존재 dirty 변경 검증: `DEFAULT_ADVISORY_RECOVERY_PROMPT`에 `RECOVERY_ATTEMPT` / `ADVISORY_FOLLOWUP_ALLOWED` 필드와 조건부 OUTPUTS 지침 추가
- `tests/test_watcher_core.py` — 사전 존재 dirty 변경 검증: 반복 stale advisory recovery가 advisory follow-up을 금지하는 테스트 및 기존 recovery 테스트 어서션 보강
- `.pipeline/harness/council.md` — 사전 존재 dirty 변경 검증: `ADVISORY_FOLLOWUP_ALLOWED: false` 가드레일 추가
- `.pipeline/harness/verify.md` — 사전 존재 dirty 변경 검증: 동일 가드레일 추가
- `CLAUDE.md` — 사전 존재 dirty 변경 검증: advisory follow-up 금지 시 implement 또는 실제 operator boundary로 수렴하는 규칙 추가
- `AGENTS.md` — 사전 존재 dirty 변경 검증: 동일 방향 동기화
- `GEMINI.md` — 사전 존재 dirty 변경 검증: 동일 방향 동기화
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 사전 존재 dirty 변경 검증: 동일 방향 동기화
- `.pipeline/README.md` — 사전 존재 dirty 변경 검증: advisory recovery follow-up limit 관련 운영 설명 갱신
- `work/4/30/2026-04-30-m101-advisory-followup-limit.md` — 이번 closeout

## 사용 skill

- `work-log-closeout` — `/work` closeout 필수 섹션, 실제 검증 기록, 남은 리스크 형식을 맞추기 위해 사용

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1451이 M101 advisory recovery followup limit 번들에 대해 신규 코드 편집 없이 지정 검증만 실행하고 `/work` closeout을 남기도록 지시했다.
- handoff SHA `37798041ab109c8ac044290472f56c03267982ea0a1c49693d26c6351279e375`가 요청값과 일치해 stale handoff가 아님을 확인했다.

## 핵심 변경

- 이번 implement 라운드에서 신규 코드 편집은 하지 않았다.
- `watcher_core.py`와 `watcher_prompt_assembly.py` 대상 `py_compile`을 통과했다.
- 반복 stale advisory recovery가 `ADVISORY_FOLLOWUP_ALLOWED: false`로 수렴하는 신규 단위 테스트를 통과했다.
- 기존 stale advisory recovery follow-up 테스트를 다시 실행해 회귀가 없음을 확인했다.
- handoff가 지정한 10개 파일 대상 `git diff --check`를 통과했다.

## 검증

- `sha256sum .pipeline/implement_handoff.md` — PASS, `37798041ab109c8ac044290472f56c03267982ea0a1c49693d26c6351279e375`
- `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py` — PASS
- `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_repeated_stale_advisory_recovery_disallows_advisory_followup` — PASS, 1 test
- `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_advisory_recovers_to_verify_followup` — PASS, 1 test
- `git diff --check -- watcher_core.py watcher_prompt_assembly.py tests/test_watcher_core.py .pipeline/harness/council.md .pipeline/harness/verify.md CLAUDE.md AGENTS.md GEMINI.md PROJECT_CUSTOM_INSTRUCTIONS.md .pipeline/README.md` — PASS

## 남은 리스크

- 광범위 unittest, Playwright E2E, 장시간 soak는 handoff 범위가 아니어서 실행하지 않았다.
- `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`의 M100 doc-sync dirty 변경은 이번 M101 handoff 범위 밖이라 손대지 않았다.
- PR #91 (M98)과 PR #92 (M99)는 여전히 draft 및 `pr_merge_gate` operator 승인 대기 상태다.
- commit, push, PR publish는 implement role 제약에 따라 수행하지 않았다.
