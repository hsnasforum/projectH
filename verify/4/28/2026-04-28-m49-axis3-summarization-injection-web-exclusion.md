STATUS: verified
CONTROL_SEQ: 1159
BASED_ON_WORK: work/4/28/2026-04-28-m49-axis3-summarization-injection-web-exclusion.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 1159
VERIFIED_BY: Claude
NEXT_CONTROL: operator_request.md CONTROL_SEQ 1160

---

# 2026-04-28 M49 Axis 3 — summarization 주입 + 웹 조사 제외 검증

## 이번 라운드 범위

코드 + 문서 — `model_adapter/base.py`, `model_adapter/ollama.py`, `model_adapter/mock.py`,
`core/agent_loop.py`, `tests/test_agent_loop.py`, `tests/test_preference_injection.py`,
`tests/test_agent_loop_model_routing.py`, `tests/test_smoke.py`, `tests/test_web_app.py`,
`docs/MILESTONES.md`.

M49 Axis 1 계약의 남은 두 위반을 함께 닫음:
1. `stream_summarize()` — `active_preferences` 파라미터 없음 → 주입 추가
2. `stream_answer_with_context()` line 7181 — `_is_web=True` 시에도 주입됨 → 제외

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `git diff --check` (10개 파일) | **PASS** (exit 0) |
| `python3 -m py_compile` (9개 Python 파일) | **PASS** (exit 0) |
| `python3 -m unittest` test_agent_loop + model_routing + preference_injection + ollama_adapter | **PASS (52 tests OK)** |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|--------|---------|
| `model_adapter/base.py` `summarize()` / `stream_summarize(active_preferences=...)` | ✓ (line 51, 85) |
| `model_adapter/ollama.py` — `_format_preference_block()` system prompt 주입 | ✓ |
| `model_adapter/mock.py` — 시그니처 맞춤 | ✓ |
| `core/agent_loop.py` — `_summarize_text_with_chunking()` 에서 `_routed_preferences(task="summarize")` 전달 | ✓ |
| `core/agent_loop.py` line 7181 — `None if _is_web else _routed_preferences(...)` | ✓ |
| `docs/MILESTONES.md` M49 Axis 3 ACTIVE 항목 | ✓ (line 1099) |
| `tests/test_preference_injection.py` — `test_summarize_with_preferences`, `test_stream_summarize_includes_preferences_in_system_prompt`, `test_summarize_without_preferences_keeps_existing_system_prompt` 등 12개 테스트 | ✓ |
| approval flow / storage / session / artifact 경계 미수정 | ✓ |
| commit / push / PR 미실행 | ✓ |

## M49 계약 완성 상태

| 계약 항목 | Axis | 상태 |
|-----------|------|------|
| 주입 대상: ACTIVE + is_highly_reliable=True | Axis 2 | ✓ |
| 주입 포맷: 시스템 프롬프트 텍스트 블록 | 기존 구현 | ✓ |
| 범위: document summary / chat 적용 | Axis 3 | ✓ |
| 범위: 웹 조사 제외 | Axis 3 | ✓ |
| 승인 경계: 기존 approval 유지 | 미수정 | ✓ |

## Dirty Tree 상태

| 파일 | 상태 | 라운드 |
|------|------|--------|
| `model_adapter/base.py` | 수정됨, 미커밋 | 이번 라운드 (M49 Axis 3) |
| `model_adapter/ollama.py` | 수정됨, 미커밋 | 이번 라운드 |
| `model_adapter/mock.py` | 수정됨, 미커밋 | 이번 라운드 |
| `core/agent_loop.py` | 수정됨, 미커밋 | 이번 라운드 |
| `tests/test_agent_loop.py` | 수정됨, 미커밋 | 이번 라운드 |
| `tests/test_preference_injection.py` | 수정됨, 미커밋 | 이번 라운드 |
| `tests/test_agent_loop_model_routing.py` | 수정됨, 미커밋 | 이번 라운드 |
| `tests/test_smoke.py` | 수정됨, 미커밋 | 이번 라운드 |
| `tests/test_web_app.py` | 수정됨, 미커밋 | 이번 라운드 |
| `docs/MILESTONES.md` | 수정됨, 미커밋 | M49 Axis 1+2+3 누적 |
| `work/4/28/2026-04-28-m49-axis3-summarization-injection-web-exclusion.md` | untracked | 이번 라운드 |
| `work/4/28/2026-04-28-operator-retriage-bundle-push.md` | untracked | retriage 라운드 |

PR #47 (`feat/m47-m48-dist-rebuild`, OPEN, CLEAN): Axis 1+2 포함. Axis 3은 미커밋으로 별도 번들 필요.

## 다음 행동

M49 Axis 3까지 검증 완료 — M49 계약 완전히 닫힘.
PR #47이 아직 머지 대기 중이므로 M49 Axis 3 번들을 스택 child branch + PR로 발행.
→ `operator_request.md` CONTROL_SEQ 1160 — stacked commit+push+PR + pr_merge_gate 권한 요청.
