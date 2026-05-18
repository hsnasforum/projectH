STATUS: verified
CONTROL_SEQ: 1451
BASED_ON_WORK: work/4/30/2026-04-30-m100-doc-sync-milestones-task-backlog.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1451

---

# 2026-04-30 M100 doc-sync — verify

## 이번 라운드 범위

CONTROL_SEQ 1450 implement_handoff (m100_doc_sync_milestones_taskbacklog) 실행 결과.
work note 변경 범위: `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 2개 파일.

## 직접 실행 결과 (docs-only, narrowest)

| 체크 | 결과 |
|------|------|
| `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` | **PASS** |
| MILESTONES M99 항목 존재 (`## M99 advisory-loop-recovery-guard`) | ✓ (line 1528) |
| MILESTONES PR #91/#92 merge backlog 기록 | ✓ (lines 1541-1542) |
| MILESTONES `M100 방향: advisory 결정 대기 중` 기록 | ✓ (line 1544) |
| TASK_BACKLOG Remaining M99 기록 | ✓ (M99 advisory-loop-recovery-guard watcher runtime) |
| `python3 -m py_compile` | 미실행 — docs-only 범위 |

## M100 핵심 변경 요약

- `docs/MILESTONES.md`: `## M99 advisory-loop-recovery-guard` 섹션 추가 + `## Next 3 Implementation Priorities` 현재화
- `docs/TASK_BACKLOG.md`: `next phase target` Remaining 끝에 M99 watcher runtime fix 기록

## 추가 발견: M101 dirty 번들

M100 work note 범위 밖의 추가 tracked dirty 파일 발견 (work note 미청구):

| 파일 | 내용 |
|------|------|
| `watcher_core.py` | `ADVISORY_RECOVERY_FOLLOWUP_LIMIT = 2` 상수; `_advisory_recovery_attempt_for_request()` 메서드; 복구 프롬프트에 `RECOVERY_ATTEMPT`/`ADVISORY_FOLLOWUP_ALLOWED` 필드 |
| `watcher_prompt_assembly.py` | `DEFAULT_ADVISORY_RECOVERY_PROMPT`에 `RECOVERY_ATTEMPT`/`ADVISORY_FOLLOWUP_ALLOWED` 추가; OUTPUTS 조건화 |
| `tests/test_watcher_core.py` | 신규 테스트: `test_repeated_stale_advisory_recovery_disallows_advisory_followup` + 기존 테스트 어서션 추가 |
| `.pipeline/harness/council.md` | `ADVISORY_FOLLOWUP_ALLOWED: false` 가드레일 추가 |
| `.pipeline/harness/verify.md` | 동일 가드레일 추가 |
| `CLAUDE.md` | `ADVISORY_FOLLOWUP_ALLOWED: false` 시 implement 수렴 규칙 추가 |
| `AGENTS.md` | 동일 방향 동기화 |
| `GEMINI.md` | 동일 방향 동기화 |
| `PROJECT_CUSTOM_INSTRUCTIONS.md` | 동일 방향 동기화 |
| `.pipeline/README.md` | 관련 운영 설명 갱신 |

신규 테스트 `test_repeated_stale_advisory_recovery_disallows_advisory_followup`: **PASS** (1 test, 0.020s).
`python3 -m py_compile watcher_core.py watcher_prompt_assembly.py`: **PASS**.

이 10개 파일은 "advisory recovery followup 횟수 제한" 번들로 coherent. work note 없음 — M101로 처리 예정.

## 남은 리스크

- M100 doc-sync + M101 advisory-followup-limit 모두 미커밋 상태
- PR #91 (M98) + PR #92 (M99) 여전히 draft, pr_merge_gate 대기
- M101 번들 작업에 대한 `/work` closeout 아직 없음
- 광범위 unittest / Playwright E2E 미실행
