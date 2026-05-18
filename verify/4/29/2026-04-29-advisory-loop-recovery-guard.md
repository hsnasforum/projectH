STATUS: verified
CONTROL_SEQ: 1446
BASED_ON_WORK: work/4/29/2026-04-29-advisory-loop-recovery-guard.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1446

---

# 2026-04-29 advisory-loop-recovery-guard — verify

## 이번 라운드 범위

CONTROL_SEQ 1445 implement_handoff (m99_advisory_recovery_cleanup_continuation) 실행 결과.
work note가 10개 파일 변경을 기록함:

| 파일 | 분류 |
|------|------|
| `watcher_core.py` | runtime |
| `watcher_prompt_assembly.py` | runtime |
| `tests/test_watcher_core.py` | tests |
| `tests/test_pipeline_runtime_supervisor.py` | tests |
| `.pipeline/harness/advisory.md` | harness |
| `.pipeline/README.md` | pipeline docs |
| `AGENTS.md` | root memory |
| `CLAUDE.md` | root memory |
| `GEMINI.md` | root memory |
| `PROJECT_CUSTOM_INSTRUCTIONS.md` | root memory |

**주의**: implement_handoff.md는 6개 파일 기준으로 작성됐으나 실제 변경은 10개.
root memory 4종 doc-sync 추가는 same-family 동기화이며 work note가 이를 솔직하게 기록함.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py` | **PASS** |
| `test_stale_advisory_default_recovery_uses_five_minute_busy_indicator` | **PASS** |
| `test_next_control_seq_counts_superseded_control_slots` | **PASS** |
| `test_advisory_prompt_bounds_large_document_reads` | **PASS** |
| `git diff --check` (10개 파일) | **PASS** |
| `git diff HEAD --name-only` 10개 일치 | ✓ (staged 없음, 미커밋 상태) |
| `DEFAULT_ADVISORY_RECOVERY_SEC`, `_get_next_control_seq`, `superseded` 키워드 확인 | ✓ 3개 hit |

Ran 3 tests in 0.035s — OK.

## 핵심 변경 사항 요약

- `watcher_core.py`: `DEFAULT_ADVISORY_RECOVERY_SEC = 300.0` 상수 추출;
  `_get_next_control_seq()`가 superseded slot까지 스캔하여 control seq 단조 증가 보장
- `watcher_prompt_assembly.py`: 대형 planning docs broad-read 금지 + `INSUFFICIENT_CONTEXT` 지침
- root memory 4종 + harness/advisory + pipeline README: 동일 방향 동기화

## 남은 리스크

- 모든 10개 파일이 미커밋 상태 (HEAD: `0d48d9b`) — commit/push/PR 필요
- PR #91 (M98) draft 상태 유지 중; M99는 별도 브랜치/PR 필요
- 브라우저 E2E / 장시간 soak 미실행 (watcher prompt guard에 한정 범위)
- PR #91 머지 후 `feat/m96-bundle → main` merge gate는 별도 operator 경계
