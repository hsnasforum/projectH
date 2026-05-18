STATUS: verified
CONTROL_SEQ: 1452
BASED_ON_WORK: work/4/30/2026-04-30-m101-advisory-followup-limit.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1452

---

# 2026-04-30 M101 advisory-followup-limit — verify

## 이번 라운드 범위

CONTROL_SEQ 1451 implement_handoff (m101_advisory_followup_limit_enforcement) 실행 결과.
work note 변경 범위: 10개 파일 (모두 사전 존재 dirty, 신규 편집 없음).

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py` | **PASS** |
| `test_repeated_stale_advisory_recovery_disallows_advisory_followup` | **PASS** |
| `test_stale_advisory_recovers_to_verify_followup` | **PASS** |
| `git diff --check` (10개 파일) | **PASS** |

Ran 2 tests in 0.036s — OK.

## M101 핵심 변경 요약

- `watcher_core.py`: `ADVISORY_RECOVERY_FOLLOWUP_LIMIT = 2`, `_advisory_recovery_attempt_for_request()` — 반복 stale advisory recovery 시 `ADVISORY_FOLLOWUP_ALLOWED: false` 산출
- `watcher_prompt_assembly.py`: recovery prompt에 `RECOVERY_ATTEMPT`/`ADVISORY_FOLLOWUP_ALLOWED` 필드 추가; OUTPUTS 조건화
- `tests/test_watcher_core.py`: 신규 테스트 (followup 금지 경로) + 기존 테스트 어서션 보강
- harness/root memory/pipeline README: `ADVISORY_FOLLOWUP_ALLOWED: false` 가드레일 동기화

## 전체 commit 대상 dirty tree (12개 파일)

| 라운드 | 파일 |
|--------|------|
| M100 doc-sync | `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` |
| M101 advisory-followup-limit | `watcher_core.py`, `watcher_prompt_assembly.py`, `tests/test_watcher_core.py`, `.pipeline/harness/council.md`, `.pipeline/harness/verify.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/README.md` |

HEAD: `9331c5b` (M99), branch: `fix/m99-advisory-loop-recovery-guard`.
모든 12개 파일 미커밋, staged 없음.

## 남은 리스크

- 12개 파일 모두 미커밋 — commit/push/PR 대기 (CONTROL_SEQ 1452 operator_request)
- PR #91 (M98) + PR #92 (M99) draft, pr_merge_gate operator 대기
- 광범위 unittest / Playwright E2E 미실행 (watcher prompt/limit 변경에 한정 범위)
