# verify: 2026-05-21 pane_text_fallback_used telemetry

## 대상 work
`work/5/21/2026-05-21-pane-text-fallback-telemetry.md`

## 검증 결과: READY

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` supervisor.py | PASS |
| `unittest` supervisor 203개 | PASS (1.166s) |
| `git diff --check` | PASS |

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `_last_pane_fallback_key: dict[str, str] = {}` | supervisor.py:190 | ✓ |
| dedupe key `model_state\|control_status\|tail_captured` | supervisor.py:1783 | ✓ |
| per-lane 비교 후 변경 시에만 emit | supervisor.py:1784–1785 | ✓ |
| payload 필드 6개 (raw pane text 없음) | supervisor.py:1787–1795 | ✓ |
| `tail_text` 문자열 payload 미포함 확인 | grep 결과 | ✓ |

## payload 구조

```json
{
  "lane": "Codex",
  "model_state": "READY",
  "active_lane": "Codex",
  "control_status": "implement",
  "tail_captured": true,
  "surface_reason": "WORKING"
}
```

raw pane text 없음. 감사 이벤트에 프롬프트/사용자 입력 미포함.

## Step 1~4 완료 현황

| 단계 | 내용 |
|---|---|
| Step 1 | wrapper_events schema 정식화 |
| Step 2 | supervisor wrapper-first 판정 계층 분리 |
| Step 3 | Claude lane stream-json → wrapper event 변환 |
| Step 4 | pane text fallback 텔레메트리 (이번) |

## 다음 슬라이스

**live Claude stream-json 검증** — 실제 claude 바이너리가 `--output-format stream-json`을
지원하는지 확인하고, 지원 시 JSONL이 wrapper event로 정상 변환되는지 관찰.
지원 안 할 경우 fallback 경로가 작동하는지(jsonl_mode=False 전환 후 pane text 복귀) 확인.
이 검증은 live runtime 환경이 필요하므로 Codex가 아닌 operator가 직접 실행.
