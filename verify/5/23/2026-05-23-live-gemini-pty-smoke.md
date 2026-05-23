# verify: 2026-05-23 live Gemini PTY smoke enable (2160→2161)

## 대상 work
`work/5/23/2026-05-23-live-gemini-pty-smoke.md`

## 검증 결과: PASS — live Gemini PTY smoke 완료

---

## 사전 검증 (CONTROL_SEQ 2161 재확인)

| 검사 | 결과 |
|---|---|
| `python3 -m json.tool runtime_policy.json` | PASS |
| `assert d['pty_pilot_lane']=='Gemini'` | PASS – `"Gemini"` 확인 |
| `git diff --check` | PASS – 공백 이슈 없음 |
| `git diff` 단일 1줄 변경 | PASS – `""` → `"Gemini"` 정확히 일치 |
| 코드 파일 변경 없음 | ✓ |

## 변경 내용

| 파일 | 변경 |
|---|---|
| `.pipeline/config/runtime_policy.json` | `"pty_pilot_lane": "Gemini"` (unstaged, 워킹트리 dirty) |
| `work/5/23/2026-05-23-live-gemini-pty-smoke.md` | 관찰 가이드 작성 (untracked) |

## 런타임 상태 (dispatcher 기준)

| 항목 | 값 |
|---|---|
| `runtime_state` | STARTING |
| `automation_health` | recovering |
| `active_round` | VERIFY_PENDING |
| `active_control` | none#-1 |

dispatcher 기준 파이프라인이 STARTING이므로, 새 `pty_pilot_lane="Gemini"` 설정이 이번 재시작 사이클에서 처음 적용될 예정.

---

## 파이프라인 재시작 후 관찰 결과 (run: 20260523T023623Z-p39768)

| # | 확인 항목 | 실제 결과 |
|---|---|---|
| 1 | `pty_pilot_lane_register` 이벤트 | **확인** — `raw.jsonl`에서 `{"lane":"Gemini","pane_target":"%2","registered":true}` (events.jsonl 미기록, 아래 갭 참조) |
| 2 | `profile_adoption.state` | **current 유지** ✓ |
| 3 | Gemini PTY lane health dict | **프로세스 레벨 alive** — `gemini --yolo` 실행 중. status.json/events.jsonl 미노출 (아래 갭 참조) |
| 4 | watcher log | **ERROR/Traceback/Exception 없음** ✓ |
| 5 | Codex/Claude TASK_DONE 사이클 | **회귀 없음** ✓ — TASK_DONE source=wrapper lane=Claude 02:41:10 확인 (seq 22) |
| 6 | gemini binary 미존재 시 | **미검증** — gemini binary 존재해 fail-open 경로 미실행 |

---

## run 20260523T023623Z-p39768 key events

| 이벤트 | 시각 | 내용 |
|---|---|---|
| DISPATCH_SEEN | 02:37:44 | source=wrapper, lane=Claude |
| TASK_ACCEPTED | 02:37:44 | source=wrapper, lane=Claude |
| **TASK_DONE** | **02:41:10** | **source=wrapper, lane=Claude** ✓ |
| receipt_written | 02:41:11 | verify 완료 |

---

## 관찰된 갭 (후속 개선 후보)

| 갭 | 내용 | 우선순위 |
|---|---|---|
| `pty_pilot_lane_register` 위치 | `raw.jsonl` 기록됨, `events.jsonl` 미기록 → 운영 관찰성 부족 | 중 |
| Gemini PTY health dict | status.json/events.jsonl에 미노출 → black box | 중 |
| fail-open 경로 | gemini binary 존재로 이번 run에서 미검증 | 낮음 |
| payload 형태 차이 | 예상: `result: registered`, 실제: `registered: true` | 낮음 |

---

## 잔여 항목

- `pty_pilot_lane: "Gemini"` — unstaged 상태. smoke PASS이므로 local commit 권장.
- `pty_pilot_lane_register` → `events.jsonl` 라우팅 개선: 별도 슬라이스.
- Codex/Claude PTY 전환: 이번 범위 밖, 별도 결정 필요.

---

## 후속 re-smoke (CONTROL_SEQ 2164/2167, observability gaps fix 이후)

| 항목 | 결과 |
|---|---|
| 최종 live run | `20260523T033000Z-p92980` |
| `events.jsonl` register | PASS — `pty_pilot_lane_register` 1회, `payload.result=registered`, `payload.lane=Gemini` |
| `events.jsonl` PTY health | PASS — `payload.pty={alive:true,pid:93707,exit_code:null}` |
| `status.json` Gemini `pty` | PASS — Gemini lane에 `pty: {alive:true,pid:93707,exit_code:null}` 노출 |
| watcher log | PASS — `ERROR`, `Traceback`, `Exception` 없음 |
| `profile_adoption.state` | PASS — `current` 유지 |
| patched watcher shutdown | PASS — 직전 patched run의 PTY pid `91883`/child `91910` 재시작 후 종료 확인 |

### 후속 re-smoke 중 추가 보강

- 첫 re-smoke에서 `events.jsonl` register mirror가 같은 run에 중복 기록되는 문제가 발견되어 `pipeline_runtime/supervisor.py`의 mirror key를 payload 기반으로 안정화했습니다.
- live `pgrep`에서 선행 재시작으로 생긴 오래된 Gemini PTY 프로세스들이 남아 있는 것이 보여 `watcher_core.py`에 SIGTERM/SIGINT graceful shutdown을 추가했습니다.
- 최종 run `20260523T033000Z-p92980`에서는 register 이벤트가 1회만 남고 Gemini `pty` status가 유지됨을 확인했습니다.

### 후속 re-smoke 제한

- active control이 `operator_request.md` (`needs_operator`, `CONTROL_SEQ 2167`)였으므로 새 Codex implement / Claude verify dispatch cycle은 실행되지 않았습니다.
- `gemini` binary가 존재해 fail-open `result=failed` live 경로는 이번 run에서 실행되지 않았습니다.
- 선행 중복 관찰 전에 시작된 오래된 Gemini PTY 프로세스 cleanup은 별도 operator 승인 범위로 남겼습니다.
