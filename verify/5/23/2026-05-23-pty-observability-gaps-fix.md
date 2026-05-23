# verify: 2026-05-23 PTY observability gaps fix

## 대상 work
`work/5/23/2026-05-23-pty-observability-gaps-fix.md`

## 검증 결과
PASS — PTY observability gaps 코드 검증 완료.

## 변경 파일
- `.pipeline/README.md`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `watcher_pty_adapter.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_watcher_pty_adapter.py`
- `work/5/23/2026-05-23-pty-observability-gaps-fix.md`
- `verify/5/23/2026-05-23-pty-observability-gaps-fix.md`

## 검증 실행
| 검사 | 결과 |
|---|---|
| `python3 -m py_compile watcher_core.py watcher_pty_adapter.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_watcher_pty_adapter.py tests/test_pipeline_runtime_supervisor.py` | PASS |
| `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_raw_pty_pilot_event_is_mirrored_and_surfaces_lane_health tests.test_watcher_core.PtyPilotWiringTest tests.test_watcher_pty_adapter -v` | PASS — 14 tests OK |
| `python3 -m unittest tests.test_watcher_core tests.test_watcher_pty_adapter tests.test_watcher_status_writer tests.test_watcher_lane_status -v` | PASS — 286 tests OK |
| `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core tests.test_watcher_status_writer tests.test_watcher_lane_status tests.test_watcher_recovery tests.test_watcher_pty_adapter 2>&1 \| tail -5` | PASS — 574 tests OK |
| `git diff --check -- watcher_core.py watcher_pty_adapter.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_watcher_pty_adapter.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md` | PASS |
| `git diff --check -- .pipeline/README.md pipeline_runtime/supervisor.py watcher_core.py watcher_pty_adapter.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py tests/test_watcher_pty_adapter.py work/5/23/2026-05-23-pty-observability-gaps-fix.md` | PASS |
| live re-smoke run `20260523T033000Z-p92980` `events.jsonl` 확인 | PASS — `pty_pilot_lane_register` 1회, `result=registered`, `pty.alive=true`, `pid=93707`, `exit_code=null` |
| live re-smoke run `20260523T033000Z-p92980` `status.json` 확인 | PASS — Gemini lane에 `pty: {alive:true,pid:93707,exit_code:null}` 노출 |
| patched watcher graceful shutdown 확인 | PASS — 직전 run PTY pid `91883`/child `91910` 재시작 후 종료 |
| watcher log 오류 확인 | PASS — live re-smoke 중 `ERROR`, `Traceback`, `Exception` 없음 |

## 확인된 변경 사항
| 파일 | 변경 내용 |
|---|---|
| `watcher_core.py` | `_setup_pty_pilot_bridge()`에서 raw log 유지, `result`, `command`, `pty` health를 포함한 deferred register payload 저장 |
| `watcher_core.py` | `_poll()` 첫 runtime export tick에서 `pty_pilot_lane_register`를 한 번만 emit |
| `watcher_core.py` | SIGTERM/SIGINT에서 `finally`를 타고 PTY bridge `teardown()`이 실행되도록 graceful shutdown 처리 |
| `watcher_core.py` | watcher-exporter status 경로에서 Gemini lane에만 additive `pty` health 노출 |
| `pipeline_runtime/supervisor.py` | production supervisor writer 경로에서 watcher raw `pty_pilot_lane_register`를 current run `events.jsonl`로 1회 mirror |
| `pipeline_runtime/supervisor.py` | raw log tail이 밀려도 같은 register 이벤트가 중복 mirror되지 않도록 mirror key 안정화 |
| `pipeline_runtime/supervisor.py` | mirrored PTY health를 Gemini lane status `pty` 필드로 표면화 |
| `watcher_pty_adapter.py` | `PtyLaneBridge.is_registered()` / `health()` 추가 |
| `tests/*` | watcher standalone exporter, supervisor production writer, Gemini-only status health, Codex/Claude status shape 보존을 검증 |
| `.pipeline/README.md` | raw log, events mirror, `status.json` `pty` payload 계약 문서화 |

## 선행 smoke gap 처리 상태
| 갭 | 이번 처리 |
|---|---|
| `pty_pilot_lane_register`가 `raw.jsonl`에만 기록됨 | watcher standalone exporter + supervisor production writer 양쪽에서 current run `events.jsonl` 기록 경로 추가 |
| Gemini PTY health dict 미노출 | watcher status 및 supervisor status 양쪽에 Gemini-only `pty: {alive, pid, exit_code}` 추가 |
| `payload.result` 형태 차이 | `result=registered|failed` 추가, 기존 `registered: bool`도 유지 |
| fail-open 경로 | 코드상 `registered=False`, `result=failed`, `pty=None` 표면화. 실제 `gemini` binary 미존재 live smoke는 미실행 |

## live 관찰 상태
- 완료: run `20260523T033000Z-p92980` 기준 `events.jsonl`에 `pty_pilot_lane_register`가 1회 기록됐습니다.
- 완료: 같은 run의 `status.json`에서 Gemini lane에 additive `pty: {alive:true,pid:93707,exit_code:null}`가 노출됐습니다.
- 완료: live 중 첫 재시작에서 같은 register 이벤트가 중복 mirror되는 문제가 발견되어 payload 기반 mirror key로 보강했고, 재시작 후 1회 기록을 확인했습니다.
- 완료: patched watcher가 SIGTERM에서 PTY bridge teardown을 실행하는지 확인하기 위해 직전 run의 Gemini PTY pid `91883`/child `91910` 종료를 재시작 후 `ps`로 확인했습니다.
- 참고: 이번 re-smoke는 active control이 `operator_request.md` (`needs_operator`, `CONTROL_SEQ 2167`)인 상태라 새 Codex implement / Claude verify dispatch cycle은 실행하지 않았습니다.

## 현재 worktree 참고
- 선행 live smoke 산출물과 advisory/report 산출물이 같은 worktree에 남아 있습니다.
- `.pipeline/config/runtime_policy.json`은 선행 smoke의 `"pty_pilot_lane": "Gemini"` 변경 상태를 유지합니다.
- commit, push, PR, merge는 실행하지 않았습니다.

## 남은 리스크
- `pty` health는 등록 시점 및 mirrored raw payload 기반입니다. 장시간 후 child 종료까지 지속 갱신하는 별도 telemetry는 후속 개선 후보입니다.
- 선행 중복 관찰 이전에 시작된 오래된 Gemini PTY 프로세스들은 이번 검증에서 정리하지 않았습니다. patched watcher 이후의 현재 종료 경로는 직전 run pid 기준으로 검증했습니다.
- `gemini` binary가 현재 환경에 존재해 fail-open `result=failed` live 경로는 이번 re-smoke에서 실행되지 않았습니다.
