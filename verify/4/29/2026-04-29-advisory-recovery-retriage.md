STATUS: verified
CONTROL_SEQ: 1429
BASED_ON_WORK: work/4/29/2026-04-29-gemini-active-advisory-recovery.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1430

---

# 2026-04-29 Advisory Recovery Full Bundle — retriage verify

## 이번 라운드 범위

operator_retriage CONTROL_SEQ 1429 재트리아지.
safety_stop 조건(Gemini advisory 루프 guard 검토 필요) → 구현 완료로 해소 확인.

1차 커밋(71b256f)에 포함되지 않은 나머지 dirty 파일 전체 검증:
- `watcher_core.py`: inactive advisory lane cancel guard + prompt order fix
- `watcher_prompt_assembly.py`: recovery prompt에 "같은 stale request 재오픈 금지" 명시
- `tests/test_watcher_core.py`: inactive guard 테스트 포함 회귀 커버
- `.pipeline/README.md`: 재개 금지 규칙 동기화
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`: 동기화
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`: 동기화

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `py_compile watcher_core.py watcher_prompt_assembly.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py` | **PASS** |
| `python3 -m unittest tests.test_watcher_core` | **212 tests OK** (9.136s) |
| `git diff --check` (dirty 파일 전체) | **PASS** |

## safety_stop 조건 해소 확인

| 조건 | 상태 |
|------|------|
| Gemini advisory loop 취소 | ✓ Escape 전송, READY 복귀 확인 |
| inactive advisory lane busy cancel guard | ✓ watcher_core.py |
| prompt order: inactive cancel → operator_retriage_no_next_control 이전 실행 | ✓ watcher_core.py |
| advisory request supersede: 동일 request 재투입 방지 | ✓ watcher_core.py |
| recovery prompt: 같은 stale request 재오픈 금지 | ✓ watcher_prompt_assembly.py |

## Dirty Tree (브랜치: fix/advisory-recovery-pane-busy-age, HEAD 71b256f)

| 파일 | 상태 |
|------|------|
| `watcher_core.py` | M (uncommitted) |
| `watcher_prompt_assembly.py` | M (uncommitted) |
| `tests/test_watcher_core.py` | M (uncommitted) |
| `.pipeline/README.md` | M (staged) |
| `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md` | M (uncommitted) |
| `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` | M (uncommitted) |

## 남은 리스크

- PR #88 (fix/advisory-recovery-pane-busy-age, base: feat/m96-bundle) 머지 대기.
- PR #71-#86 (M88-M96 스택) 머지 게이트: operator 결정 대기.
- M97 방향: Gemini CONTROL_SEQ 1394 — 머지 우선(Option C) 권고.
- E2E smoke: watcher-only 변경으로 미실행.
