# verify: 2026-05-22 live Claude verify trigger 3

## 대상 work
`work/5/22/2026-05-22-live-claude-verify-trigger-3.md`

## 검증 결과: PARTIAL — Codex TASK_DONE 확인, Claude TASK_DONE 미확인

---

## run_id: 20260522T040034Z-p31147 이벤트 분석

### Codex 레인 (trigger-2 디스패치)

| 이벤트 | source | lane | 시각 | 비고 |
|---|---|---|---|---|
| dispatch_selection | supervisor | — | 04:00:36 | latest_work=trigger-2 |
| DISPATCH_SEEN | wrapper | Codex | 04:00:50 | ✓ |
| TASK_ACCEPTED | wrapper | Codex | 04:01:17 | ✓ (27초 후, 현실적) |
| **TASK_DONE** | **wrapper** | **Codex** | **04:01:57** | **✓ 확인** |

TASK_DONE payload: `job_id: ctrl-2128, control_seq: 2128, reason: task_hint_cleared`

### Claude 레인 (trigger-3 디스패치)

| 이벤트 | source | lane | 시각 | 비고 |
|---|---|---|---|---|
| dispatch_selection | supervisor | — | 04:01:54 | latest_work=trigger-3 |
| DISPATCH_SEEN | wrapper | Claude | 04:02:09 | ✓ |
| TASK_ACCEPTED | wrapper | Claude | 04:02:09 | ✓ (동시 발생 — jsonl_mode 정상) |
| lane_working | pane | Claude | 04:02:11 | 실제 동작 중 확인 |
| **completion_stall_detected** | supervisor | Claude | **04:02:58** | **TASK_DONE 미수신** |
| control_changed | supervisor | — | 04:03:37 | control 소거 (seq → -1) |
| runtime_stopped | supervisor | — | 04:03:41 | — |

---

## pane_text_fallback_used 분석 (Claude 레인)

| 발생 시각 | 상태 | 판정 |
|---|---|---|
| 04:00:36 | BOOTING | 허용 (초기 부팅) |
| 04:00:47 | 초기 부팅 | 허용 |
| 04:00:49 | Codex 디스패치 직전, Claude READY | 허용 |
| 04:02:01 | Codex TASK_DONE 직후, Claude 디스패치 전 READY | 허용 |

총 4회, 모두 BOOTING/READY/pre-dispatch 구간 → 정상 범위 (기준: run당 2~4회) ✓

---

## Claude TASK_DONE 미수신 원인 분석

`completion_stall_detected` 세부:
```
stage: task_done_missing
reason: waiting_task_done_after_accept
action: requeue
lane: Claude
attempt: 1
```

**39초 갭 해석 (04:02:58 → 04:03:37 → 04:03:41):**

events.jsonl에서 stall(04:02:58) → control_changed(04:03:37, seq→-1) → runtime_stopped(04:03:41) 흐름 확인. supervisor.log는 비어 있음. control_changed 시 `active_control_seq: -1` + `control_age_cycles: 97`로 implement #2128이 소거됨. 이 패턴은 **TASK_ACCEPTED 확인 후 사용자가 runtime을 수동 종료**한 경우와 일치. requeue 후 Claude가 실제로 완료했는지는 알 수 없으나, runtime이 종료되면서 TASK_DONE 발행 기회가 사라진 것은 사실.

**근본 원인: `verify_done_deadline_sec=45.0` 기본값이 LLM verify 레인에 비현실적으로 짧음.**

| 레인 | 태스크 | TASK_ACCEPTED → TASK_DONE |
|---|---|---|
| Codex (trigger-2) | docs-only trigger verify | 40초 (임계값 45s 아슬아슬 통과) |
| Claude (trigger-3) | docs-only trigger verify | 48초 초과 → stall |

Codex조차 40초 걸린 docs-only 태스크 기준으로, 실제 코드 verify 태스크라면 Codex도 같은 stall에 빠질 수 있음. 45초는 모든 LLM verify lane에 비현실적.

**이번 fix 범위 (false positive stall)**:
- `verify_done_deadline_sec` 기본값을 45s → 300s로 확장 (API 지연 + 실제 처리 시간 감안)

**이번 fix가 다루지 않는 것 (별도 슬라이스 필요)**:
- lane kill 시 `finish_stream()` 미호출 → TASK_DONE 손실: supervisor가 stall requeue로 lane을 kill하면 claude-print-jsonl-pipe 프로세스도 함께 종료되어 TASK_DONE이 발행되지 않을 수 있음. SIGTERM 핸들링으로 `finish_stream()`을 보장하는 개선이 필요 (현재는 deadline을 늘려 kill 자체를 방지하는 방향으로 대응).

---

## 완료 상태 요약

| 항목 | 상태 |
|---|---|
| TASK_DONE source=wrapper lane=Codex | ✓ 확인 (04:01:57) |
| TASK_DONE source=wrapper lane=Claude | 미확인 (completion_stall) |
| pane_text_fallback_used Claude 정상 범위 | ✓ 4회 모두 허용 구간 |
| Claude TASK_ACCEPTED 경로 동작 | ✓ (DISPATCH_SEEN + TASK_ACCEPTED 동시 발생, jsonl_mode 정상) |

---

## 다음 슬라이스 방향

Claude 레인 TASK_DONE 신뢰성 개선이 필요한 항목:
- supervisor `completion_stall_detected` 임계값 vs Claude 실제 처리 시간 검토
- `claude-print-jsonl-pipe` SIGINT/SIGTERM 핸들링 — 인터럽트 시 `finish_stream()` 호출 보장
- A3 Step 6 (WatcherCore turn state machine) 진입 전 Claude TASK_DONE end-to-end 확인 필요
