# verify: 2026-05-21 supervisor wrapper-first lane status (Step 2)

## 대상 work
`work/5/21/2026-05-21-supervisor-wrapper-first-lane-status.md`

## 검증 결과: READY

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` supervisor.py | PASS |
| `unittest` supervisor 199개 | PASS (1.122s) |
| `git diff --check` | PASS |

## 코드 구조 확인

`_build_lane_statuses()` 판정 계층 (line 1720~):

```
1) not enabled                   → OFF
2) duplicate_control (implement) → READY (wrapper 기반)
3) wrapper_status_decisive       → WORKING / READY / BROKEN
   (tail capture 없음)
4) not health.alive              → BROKEN / OFF
5) failure_reason                → BROKEN
6) else (pane text fallback)     → tail capture 후 판정
```

`wrapper_status_decisive` 조건:
- `has_accepted_task` (TASK_ACCEPTED event)
- `model_state == "READY" and has_done_task` (TASK_DONE event)
- `model_state == "BROKEN"` (BROKEN event / heartbeat timeout)

## 잔여 코드 품질 이슈 (블로커 아님)

`else` 브랜치(pane text fallback) 내부에 `if has_accepted_task:` 체크가 남아 있음.
`wrapper_status_decisive = has_accepted_task or ...`이므로 해당 분기는
실제로 도달 불가능한 dead code. Step 3 전에 정리 권장.

## Step 1~2 달성 내용

| 단계 | 파일 | 내용 |
|---|---|---|
| Step 1 | wrapper_events.py | 공식 schema, validate, schema_version |
| Step 2 | supervisor.py | wrapper event 우선 판정, pane text fallback |

## 다음 슬라이스

**Step 3**: Claude lane에 `--output-format stream-json` 적용.
JSONL 파싱 후 wrapper event 포맷으로 변환 → supervisor는 lane-specific 포맷 몰라도 됨.
Step 2 dead code 정리를 Step 3 시작 전에 포함 권장.
