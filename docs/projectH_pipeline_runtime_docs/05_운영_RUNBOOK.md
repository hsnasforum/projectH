# projectH Pipeline Runtime 운영 RUNBOOK
버전: v1.0  
작성일: 2026-04-10  
문서 성격: 운영 절차 / 장애 대응

## 1. 목적

본 문서는 목표 runtime 구조(supervisor + backend adapter + run-scoped state)를 기준으로 운영 절차를 정의합니다.  
현행 구조에서도 일부 절차는 바로 적용 가능하지만, 본 문서는 **목표 구조 기준** 운영 절차입니다.

## 2. 운영 원칙

1. 현재 상태는 supervisor만 신뢰합니다.
2. pane 화면, artifact 파일, watcher.log는 보조 증거입니다.
3. round close는 receipt 없이는 인정하지 않습니다.
4. 장애 시 “억지 재시도”보다 “현재 run 상태 보존 후 복구”를 우선합니다.
5. next-slice ambiguity는 Gemini arbitration을 먼저 사용하고, `needs_operator`는 real operator-only decision에만 남깁니다.
6. fresh `needs_operator`는 즉시 stop slot current truth가 아니라 24시간 gate 후보일 수 있으므로, `status.control`보다 `status.autonomy`를 먼저 확인합니다.
7. operator stop 판정은 free-form prose가 아니라 `OPERATOR_POLICY` 우선, `REASON_CODE` 다음 순서로 봅니다. 구조화 metadata가 없거나 알 수 없으면 fail-safe로 즉시 publish합니다.
8. runtime/script가 `operator_request.md`나 `implement_blocked` sentinel을 machine-write해야 할 때는 `pipeline_runtime.control_writers` helper와 classification-source 검사를 우선 사용합니다.

## 3. 일상 운영 절차

## 3.1 시작 전 점검
- 최근 run이 `STOPPED` 또는 명시적 `BROKEN` 종료인지 확인
- `current_run.json` 확인
- 디스크 여유 공간 확인
- 최근 3개 run의 degraded reason 확인
- backend health 사전 체크

## 3.2 시작
1. launcher에서 start 요청
2. status가 `STARTING`인지 확인
3. 모든 필수 lane이 `READY` 또는 정책상 허용 가능한 상태인지 확인
4. current_run_id를 기록

추가 규칙:

- 같은 `project_root + session`에 supervisor가 중복으로 살아 있으면 `start`/`restart`는 먼저 이를 reconcile해야 합니다.
- 정상 상태에서는 live supervisor가 정확히 1개여야 하며, `.pipeline/supervisor.pid`와 `current_run.json`이 그 run을 함께 가리켜야 합니다.

## 3.3 운영 중 확인
주기적으로 아래를 확인합니다.

- runtime_state
- last_heartbeat_at
- lane별 상태
- `waiting_next_control` note 유무
- active round 체류 시간
- degraded reason
- recent events
- 마지막 receipt 시각

## 3.4 정상 종료
1. stop 요청
2. `STOPPING` 진입 확인
3. active round 처리 정책 확인
4. `STOPPED` 및 final receipt flush 확인
5. run 종료 보고 작성
- stop 성공은 supervisor pid 소멸만으로 판단하지 않습니다. final status에 `runtime_state=STOPPED`, `control=none`, `active_round=null`, watcher dead, lane inactive가 함께 flush되었는지 확인합니다.
- 최신 CLI stop은 먼저 graceful flush를 기다리고, timeout 뒤에만 강제 종료 fallback을 사용합니다. `STOPPING`이 오래 남았는데 supervisor가 이미 사라졌다면 graceful flush miss 가능성을 먼저 의심합니다.
- supervisor가 이미 죽었지만 watcher/tmux session 같은 orphan runtime이 남아 있으면, stop CLI는 orphan cleanup 뒤 `status.json`을 `STOPPED + inactive truth`로 보정합니다.
- controller가 오래된 `STOPPING` run을 다시 읽더라도 supervisor PID가 이미 없으면 UI는 이를 `STOPPED`로 정규화하고 `Control=none`, `Round=IDLE`로 보여야 합니다. 이 reader 정규화는 graceful flush 실패에 대비한 fallback safety net입니다.

## 3.5 현재 검증 원칙
runtime long soak는 baseline evidence로 유지하되, 기본 검증 메뉴는 아닙니다.

현재 기본 검증은 아래 세 축입니다.

1. launcher live stability gate
2. incident replay
3. 실제 작업 세션

long soak 재실행은 아래 경우에만 수행합니다.

1. supervisor / watcher / tmux adapter / wrapper event 계약을 크게 바꾼 경우
2. control / receipt / state writer 계약을 바꾼 경우
3. adoption 직전 최종 gate가 필요한 경우

launcher live stability gate는 아래를 현재 통과 기준으로 둡니다.

- `handoff_dispatch -> TASK_ACCEPTED -> TASK_DONE -> receipt_close` chain이 실작업에서 끊기지 않을 것
- READY/WORKING 오표시가 없을 것
- 불필요한 `needs_operator` 승격이 없을 것
- `classification_fallback_detected`가 없을 것
- stop/restart 후 stale `RUNNING/STOPPING`이 남지 않을 것
- orphan watcher/session이 없을 것
- dispatch/completion/receipt close incident가 named event로 surface될 것
- 반복된 실전 incident가 replay test로 고정되어 재발 시 즉시 드러날 것
- thin client drift triage는 runtime `status.json` / `events.jsonl` 기준으로만 하고, pane/log/file scan은 current truth 재판정이 아니라 mismatch evidence로만 사용할 것
- current `accepted_task`가 살아 있는 lane은 tail prompt가 보여도 `READY`로 내리지 말고 `WORKING`으로 유지할 것. verify lane이 이미 `TASK_DONE` 뒤 receipt close만 기다리는 경우는 launcher snapshot에 `active_round.state`, `dispatch_id`, `completion_stage`, `Receipt: pending close`로 그대로 드러나야 합니다.
- pane busy/ready marker는 `pipeline_runtime/lane_surface.py` shared helper/profile을 single source로 유지할 것. watcher, supervisor, cli wrapper가 각자 marker 확장을 따로 들고 있으면 READY/WORKING drift triage가 다시 흔들립니다.
- `RECEIPT_PENDING` round가 있다고 해서 current turn이 이미 follow-up/advisory/idle로 넘어간 상태까지 Codex active lane을 계속 유지하지는 않을 것. receipt close 대기는 `active_round`/lane note로 surface하고, active lane은 current turn/control 우선으로 본다.

synthetic soak는 아래처럼 채택용 보조 게이트로만 남깁니다.

- short smoke:
  `python3 scripts/pipeline_runtime_gate.py --mode experimental synthetic-soak --duration-sec 30 --sample-interval-sec 1 --min-receipts 1 --report report/pipeline_runtime/verification/<date>-synthetic-soak-short.md`
- fault check:
  `python3 scripts/pipeline_runtime_gate.py --project-root <project-root> --mode experimental fault-check --report report/pipeline_runtime/verification/<date>-fault-check.md`
- 6h mini soak:
  `python3 scripts/pipeline_runtime_gate.py --mode experimental synthetic-soak --duration-sec 21600 --sample-interval-sec 10 --min-receipts 10 --report report/pipeline_runtime/verification/<date>-6h-synthetic-soak.md`
- 24h soak:
  `python3 scripts/pipeline_runtime_gate.py --mode experimental synthetic-soak --duration-sec 86400 --sample-interval-sec 10 --min-receipts 20 --report report/pipeline_runtime/verification/<date>-24h-synthetic-soak.md`
- operator metadata quick gate:
  `python3 scripts/pipeline_runtime_gate.py --project-root <project-root> --mode experimental check-operator-classification --report report/pipeline_runtime/verification/<date>-operator-classification-gate.md`

이 보조 게이트 경로의 기준:
- temp workspace에서 supervisor + watcher + wrapper + receipt/control 전이를 실제로 밟습니다.
- `fault-check`도 동일하게 synthetic workspace에서 실행하며, 실 repo truth를 직접 오염시키지 않습니다.
- synthetic soak는 sample loop에 들어가기 전에 `fault-check`와 같은 readiness barrier를 먼저 통과해야 합니다. 기본 gate는 최대 45초 동안 `runtime_state ∈ {RUNNING, DEGRADED}`이면서 attachable lane 하나 이상이 `READY/WORKING`으로 올라오는지 기다립니다.
- readiness barrier timeout 시 report에는 마지막 status snapshot을 남깁니다. 최소 덤프 항목은 `runtime_state`, `watcher.alive/pid`, lane별 `state/attachable/pid/note/last_event_at/last_heartbeat_at`, `control.active_control_status`, `active_round.state`입니다.
- report에는 `receipt_count`, `duplicate_dispatch_count`, `control_mismatch_samples`, `control_mismatch_max_streak`, `orphan_session`를 함께 남깁니다.
- report/check에는 `classification_gate_failures`와 `classification_fallback_detected` 여부도 함께 남깁니다.
- `control_mismatch_samples`는 transition 시점에 1회 관측될 수 있으므로, 채택 판단은 persistent mismatch(`control_mismatch_max_streak > 1`) 기준으로 봅니다.
- 현재 실전 로그는 장시간 샘플링보다 상태 전이 이벤트 위주로 남기는 편이 맞습니다. 최소 이벤트는 `handoff_dispatch`, `TASK_ACCEPTED`, `TASK_DONE`, `receipt_close`, `dispatch_stall_detected`, `completion_stall_detected`, `stale_cleanup`, `lane_broken`입니다.

## 4. 알림 및 모니터링

## 4.1 필수 상태 알림
다음은 알림 대상입니다.

- runtime_state = `DEGRADED`
- lane_state = `BROKEN`
- heartbeat gap 초과
- receipt 쓰기 실패
- manifest mismatch
- stale lease cleanup 반복 실패
- supervisor restart 발생
- duplicate dispatch 감지

## 4.2 권장 지표
| 지표 | 의미 |
|---|---|
| runtime_uptime_sec | 현재 run 가동 시간 |
| lane_ready_ratio | lane 준비 상태 비율 |
| active_round_age_sec | 현재 round 체류 시간 |
| receipt_lag_sec | verify 완료 후 receipt까지 지연 |
| degraded_count | run 내 degraded 횟수 |
| recovery_success_ratio | 자동복구 성공률 |

## 5. 장애 분류

### P1
- duplicate dispatch
- false CLOSED
- receipt 누락으로 잘못된 close
- supervisor/state 손상으로 운영 중단
- manual intervention 필요

### P2
- lane 자동복구 실패
- 장시간 degraded
- backend attach 불가
- restart 실패 반복

### P3
- 상태 표시는 되나 detail 부족
- 일부 로그 손실
- 경미한 operator UX 문제

## 6. 장애 대응 절차

## 6.1 runtime_state = DEGRADED
1. degraded reason 확인
2. 최근 50개 events 확인
3. 어떤 lane 또는 어떤 state resource가 원인인지 식별
4. 자동복구 대기 정책 시간 확인
5. 자동복구 실패 시 controlled restart 실행

## 6.2 lane BROKEN
1. lane name과 pid 확인
2. active round와 해당 lane의 연관 확인
3. `restart_lane` 또는 전체 restart 정책 적용
4. recovery 결과 확인
5. 동일 lane 반복 장애면 run 종료 후 분석

예외:

- lane note가 `auth_login_required`면 blind restart보다 인증 복구를 먼저 해야 합니다.
- 이 경우 pane tail의 `401`, `Invalid authentication credentials`, `Please run /login`를 확인하고, 해당 vendor CLI 로그인 복구 후에만 restart 또는 attach를 진행합니다.
- auth/login failure는 operator가 해결하기 전까지 `READY`로 다시 해석하면 안 됩니다.

## 6.3 receipt write 실패
1. verify result와 manifest 존재 확인
2. hash mismatch 여부 확인
3. receipt 재시도 정책 범위 내에서만 재시도
4. 실패 지속 시 `DEGRADED`
5. 운영자는 artifact만 보고 close 판단하지 않음

## 6.4 stale lease
1. lease owner와 last heartbeat 확인
2. TTL 경과 여부 확인
3. cleanup 이벤트 발생 확인
4. cleanup 실패 시 supervisor restart 고려

- verify lane이 `VERIFY_RUNNING` idle timeout 뒤 `VERIFY_PENDING`으로 복귀했는데 pane이 이미 idle prompt인 경우, same-snapshot guard는 short backoff만 적용하고 이후 재dispatch를 허용해야 합니다.
- 이런 상황에서 `dispatch_backoff_same_snapshot`만 반복되고 새 dispatch가 다시 일어나지 않으면 stale retry loop로 보고 watcher retry state를 먼저 점검합니다.
- 새 verify dispatch는 `dispatch_id`, `dispatched_at`, `accept_deadline_at`을 기준으로 wrapper `DISPATCH_SEEN`, `TASK_ACCEPTED`, `TASK_DONE`를 직접 연결해서 보는 편이 맞습니다.
- verify lane은 `control=none`이어도 `active_round.dispatch_control_seq`, `job_id`, `dispatch_id`를 가진 round-scoped Codex task hint로 dispatch를 이어갈 수 있습니다. `active_control_seq < 0`만 보고 hint를 inactive로 내려 false `dispatch_stall`을 만들면 안 됩니다.
- 다만 `CODEX_FOLLOWUP` / `GEMINI_ADVISORY` turn에서는 stale verify `job_id`/`dispatch_id`/`dispatch_control_seq`를 current hint나 status에 남기면 안 됩니다. 이 구간의 active truth는 current control seq이며, 예전 verify round는 current runtime surface에서 비워야 합니다.
- wrapper `TASK_DONE`는 task hint clear를 기다리지 않고, accepted된 same dispatch가 prompt-visible + no-busy 상태로 짧게 settle되면 직접 emit될 수 있어야 합니다.
- verify lane이 busy indicator 없이 idle prompt로 먼저 돌아왔더라도 `DISPATCH_SEEN`/`TASK_ACCEPTED` deadline이 아직 남아 있으면 pre-accept stall로 확정하지 않습니다. 늦게 오는 seen/accept를 기다리는 구간과 post-accept idle retry를 분리하는 편이 맞습니다.
- verify lane은 `TASK_ACCEPTED -> TASK_DONE -> current-round /verify receipt + next control -> receipt close` 순서로만 닫는 편이 맞습니다. matching `TASK_DONE` 없이 `/verify`나 control output만 먼저 바뀌면 success close가 아니라 completion wait로 유지합니다.
- wrapper가 active verify hint를 읽었는데 `control_seq` metadata가 누락되었거나 비정상이면 `DISPATCH_SEEN`을 조용히 빼먹지 말고 `BRIDGE_DIAGNOSTIC(code=active_task_hint_metadata_invalid)`를 남겨 write-side 누락을 바로 드러내는 편이 맞습니다.
- verify lane이 busy indicator 없이 idle prompt로 먼저 돌아왔는데 `TASK_ACCEPTED` 이후에도 `TASK_DONE`이 done deadline 안에 안 오면 `waiting_task_done_after_accept`으로 보고, `TASK_DONE` 뒤에도 current-round `/verify` receipt나 next control output이 still incomplete하면 `waiting_receipt_close_after_task_done`으로 두는 편이 맞습니다.
- 다만 pane이 `Waiting for background terminal` 같은 explicit busy wait를 계속 보여주는 동안에는 post-accept stall이 아니라 active wait로 유지하고 done deadline을 연장하는 편이 맞습니다.
- `DISPATCH_SEEN` 없이 deadline을 넘기면 lane note는 `waiting_dispatch_seen_after_dispatch`, `DISPATCH_SEEN` 뒤에도 `TASK_ACCEPTED` 없이 deadline을 넘기면 lane note는 `waiting_task_accept_after_dispatch`로 남기는 편이 맞습니다.
- 같은 fingerprint에서 이 pre-accept stall이나 short idle retry가 한 번 더 반복되면 runtime은 이를 `dispatch_stall` incident로 승격하고, 추가 자동 재큐잉 대신 `degraded_reason=dispatch_stall`과 해당 lane note를 남기는 편이 맞습니다.
- 같은 fingerprint에서 post-accept completion wait가 한 번 더 반복되면 runtime은 이를 `post_accept_completion_stall` incident로 승격하고, 추가 자동 재큐잉 대신 `degraded_reason=post_accept_completion_stall`과 lane note(`waiting_task_done_after_accept` 또는 `waiting_receipt_close_after_task_done`)를 남기는 편이 맞습니다.
- 이 incident는 supervisor events에 `dispatch_stall_detected` 또는 `completion_stall_detected`로 기록되고 launcher recent log에도 그대로 보여야 합니다. long soak를 다시 기본 게이트로 돌리기보다, live launcher session에서 이 이벤트가 0회인지와 실제 재발 replay가 막히는지를 우선 확인합니다.
- follow-up/advisory/operator/blocked-triage notify가 lane busy 때문에 바로 못 들어가면 watcher는 silent retry 대신 `lane_input_deferred`를 남기고 prompt-ready가 확인될 때까지 pending defer로 유지해야 합니다. launcher recent log는 이 named event를 그대로 보여줘 queued paste contamination과 normal dispatch를 구분해야 합니다.
- 이때 queue/defer/flush/drop 처리는 `watcher_dispatch.py`가 single implementation이 되는 편이 맞습니다. `watcher_core.py`가 notify family마다 별도 send branch를 다시 들고 있으면 같은 busy-lane contamination replay가 반복됩니다.
- verify round 전이와 incident 승격은 `verify_fsm.py` single implementation으로 유지하는 편이 맞습니다. 운영 triage는 watcher core loop보다 FSM state/receipt-close chain 기준으로 읽어야 재시도와 실제 멈춤을 구분하기 쉽습니다.
- turn drift triage도 `turn_arbitration.py` single implementation을 기준으로 읽는 편이 맞습니다. watcher와 supervisor가 각자 `RECEIPT_PENDING`, follow-up, operator gate를 다시 해석하기 시작하면 READY/WORKING drift와 stale verify surface가 다시 생기기 쉽습니다.
- prompt drift triage도 `watcher_prompt_assembly.py` single implementation을 기준으로 읽는 편이 맞습니다. `_notify_*`가 core loop 안에서 다시 multi-line prompt 본문을 조립하기 시작하면 dispatch queue/FSM/arbitration을 분리해도 wrong prompt payload drift가 다시 생기기 쉽습니다.
- 다만 pending defer가 남아 있는 동안 active control이 더 높은 seq handoff나 다른 family로 바뀌면, 그 예전 pending prompt는 flush하지 말고 drop해야 합니다. 그렇지 않으면 Claude handoff 직전 stale Codex prompt가 뒤늦게 paste되어 wrong-lane contamination처럼 보일 수 있습니다.
- readiness triage에서 pane busy 여부는 최근 visible tail만 기준으로 보고, 오래된 scrollback의 `Working (...)` 줄은 현재 busy truth로 쓰지 않습니다. 그렇지 않으면 실제로는 prompt-ready인 Claude/Codex pane이 계속 defer 상태로 남을 수 있습니다.
- runtime이 `STOPPED`로 내려가거나 active round가 더 새 `/work`로 넘어가면 old `dispatch_stall`, old operator/autonomy gate, 이전 round artifact를 가리키는 degraded reason은 current truth에서 같이 비워야 합니다.
- 재dispatch 전 pane prompt 입력줄에 남은 미전송 draft text를 먼저 비워서, stray input이 새 verify/control prompt와 이어 붙지 않게 유지해야 합니다.

## 6.5 corrupt state
1. quarantine 이벤트 확인
2. 손상된 파일 백업 경로 확인
3. 복구 가능한 마지막 snapshot/receipt 확인
4. 필요 시 해당 job만 failed 처리하고 전체 runtime 유지

## 6.6 backend session loss
1. backend health 확인
2. attach 가능 여부 확인
3. lane 재생성 또는 전체 backend 재기동
4. current_run continuity 확인

메모:

- supervisor pid 가 이미 없고 recent status 안의 watcher/lane pid 도 모두 dead 로 확인되면, browser/controller 는 stale timeout 을 기다리지 않고 runtime 을 즉시 `BROKEN(supervisor_missing)` 으로 강등할 수 있습니다.
- pid 가 비어 있더라도 recent status 가 이미 `control=none`, `active_round=null`, watcher dead, lane inactive 로 정리돼 있으면 같은 fast-path 를 적용할 수 있습니다.
- recent status 이고 supervisor 는 없지만 `control != none`, `active_round != null`, active lane state 같은 activity claim 이 남아 있고 watcher/active lane pid 로 live identity 를 증명하지 못하면, browser/controller 는 이를 `DEGRADED(supervisor_missing_recent_ambiguous)` uncertain runtime 으로 먼저 surface 합니다.
- 같은 ambiguous payload 인데 `updated_at`까지 비어 있으면 browser/controller 는 `DEGRADED(supervisor_missing_snapshot_undated)` uncertain runtime 으로 surface 하고, stale timeout 기준이 복구되기 전까지 clean `RUNNING`으로 올려 보지 않습니다.
- 이 fast-path 는 recent `RUNNING` 착시를 줄이기 위한 reader safety net 이며, primary truth 는 여전히 supervisor final flush 입니다.

## 6.7 controller browser contract
controller browser UI의 active runtime contract는 아래로 제한합니다.

- `GET /api/runtime/status`
- `POST /api/runtime/start`
- `POST /api/runtime/stop`
- `POST /api/runtime/restart`
- `GET /api/runtime/capture-tail?lane=<Claude|Codex|Gemini>&lines=<n>`
- `POST /api/runtime/send-input` with JSON body `{ "lane": "<Claude|Codex|Gemini>", "text": "..." }`

주의:

- browser controller는 arbitrary shell exec를 열지 않습니다.
- 상태 authority는 계속 `status.json`과 `events.jsonl`이며, controller는 이 payload를 읽는 operator UX layer일 뿐입니다.
- `Office View` 같은 시각화 토글은 허용되지만, 이는 같은 runtime status/tail을 다른 형태로 그려주는 read-model일 뿐 별도 상태 판정 경로가 아닙니다.
- 현재 browser Office View는 projectH 전용 `runtime war-room` 장면으로 유지합니다. Claude / Codex / Gemini는 동등한 3석으로 보이고 watcher는 장면 안 `ops core` 오브젝트로만 표현되며, 이 연출은 모두 기존 runtime payload를 읽는 시각화일 뿐입니다.
- launcher가 operator candidate status에서 `classification_source` fallback을 감지하면 runtime authority를 직접 덮어쓰지는 않지만, launcher surface에서는 `BROKEN` gate와 `classification_fallback_detected` recent log로 즉시 드러내는 편이 맞습니다.
- `runtime_state`가 `STOPPED`, `STOPPING`, `BROKEN`이면 controller는 `control`, `round`, lane action을 active처럼 보여주지 않습니다.
- `runtime_state=DEGRADED`이면서 `degraded_reason`이 `supervisor_missing_recent_ambiguous` 또는 `supervisor_missing_snapshot_undated`이면 controller는 runtime summary를 uncertain runtime으로 보여야 합니다. badge는 amber `DEGRADED`, `Control`/`Round`는 `uncertain`, `Watcher`는 `Unknown`이어야 하며, active control/round를 초록 활성 상태처럼 강조하면 안 됩니다.
- `active_round=VERIFY_PENDING|VERIFYING`이어도 Codex pane이 이미 prompt-visible이고 busy tail이 없으면 controller lane badge는 `WORKING`이 아니라 `READY`로 내려와야 합니다. pending work truth는 runtime summary와 lane note(`verify_pending`/`verifying`)로만 남깁니다.
- log modal은 tail 확인 + bounded one-line 입력용입니다. permission/plan prompt 같은 interactive 선택이 뜨면 현재 lane에 `1`, `2`, `3` 같은 짧은 응답을 보낼 수 있습니다. backend route가 없는 lane pause/resume/restart나 attach 버튼은 계속 노출하지 않습니다.
- Codex startup 시 self-update dialog가 뜨면 wrapper가 `Skip until next version`을 자동 선택해야 하며, update dialog 자체를 `READY(prompt_visible)`로 surface하면 안 됩니다. `codex_exit:0`와 함께 pane에 `Please restart Codex`가 남았다면 self-update prompt miss로 봅니다.
- 상태별 GIF를 테스트하려면 operator가 `controller/assets/BOOTING.gif`, `WORKING.gif`, `BROKEN.gif`, `READY.gif`, `DEAD.gif`를 두고 controller를 새로고침하면 됩니다. browser는 이 다섯 파일을 우선 사용합니다.
- background는 `/controller-assets/background.png`를 먼저 시도하고, 필요 시 `/controller-assets/generated/bg-office.png`로 fallback 합니다. sidebar `Scene` 값이 `fallback` 또는 `asset_error`면 자산 경로/로딩 문제를 먼저 의심합니다.
- log modal info strip 은 좁은 viewport 에서도 wrap 되어야 하며, body 는 전체 폭을 유지해야 합니다. 내부 pane 이 좁은 고정폭처럼 보이는 스타일을 다시 넣지 않습니다.
- Office View의 packet/날씨/펫/ambient audio는 runtime payload에서 읽은 read-model 연출입니다. `latest_work`, `latest_verify`, `last_receipt`, `control_seq`, lane state 변화와 맞물려 보여야 하며, pane text scraping이나 hidden route에 의존하면 안 됩니다.
- `working` / `booting` lane은 desk anchor 위에 유지하되, `ready` / `idle` lane은 browser-local roam spot 사이를 이동할 수 있습니다. 이 wandering은 purely decorative이며 runtime state 판정과는 분리해서 봐야 합니다.
- ambient audio는 operator가 mute 버튼 등 explicit browser gesture를 준 뒤에만 시작해야 합니다. 새로고침 직후 자동 재생되면 현재 운영 계약과 어긋난 것입니다.
- toolbar의 `✨` 버튼으로 reduced-motion 모드를 켜면 weather rain, pet roaming, event particle, delivery packet animation이 멈춥니다. agent 렌더링, runtime badge, event log, log modal, needs-operator overlay는 그대로 유지됩니다. 이 설정은 browser-local이며 backend에 영향을 주지 않습니다.
- reduced-motion(`✨`)과 ambient mute(`🔊`) 토글 상태는 `localStorage`에 저장되어 새로고침 후에도 유지됩니다. muted 복원 시 audio가 자동 재생되지는 않습니다.
- `localStorage`가 차단된 환경(private browsing 등)에서는 controller event log에 `환경 설정 저장 불가` 경고가 한 번 표시되고, toolbar 영역에 `⚠ 설정 비저장` 경고 chip이 지속 표시됩니다. 이 경우 toolbar 토글은 현재 페이지에서 정상 동작하지만, 새로고침 시 기본값으로 초기화됩니다. 이 경고는 runtime authority와 무관한 browser-local 안내입니다.
- GIF 세트가 없거나 일부만 준비된 경우에는 `controller/assets/fren-office-sheet.png`를 기준으로 `python3 scripts/build_office_sprites.py`를 실행해 `controller/assets/generated/office-sprite-manifest.json`과 normalized frame PNG를 만들면 됩니다. generated 자산까지 없으면 raw sheet fallback 또는 CSS fallback avatar를 유지합니다.
- 설명용 흰 배경 시트를 그대로 넣었을 때는 controller browser가 frame crop과 가장자리 white trim을 시도해 자연스러운 sprite animation으로 보여줄 수 있습니다. 다만 완전한 transparency 품질이 필요하면 투명 배경 PNG를 우선합니다.
- 프레임별 sprite 크기가 들쭉날쭉해 보이면 Office View는 browser에서 viewport normalization과 ping-pong/crossfade를 적용합니다. 그래도 어색하면 sprite sheet의 frame 간 safe margin과 기준선 자체를 더 맞춘 자산이 필요합니다.

## 6.8 duplicate/no-op implement handoff
다음 조건이 동시에 보이면 duplicate/no-op implement handoff로 판단합니다.

- active control은 여전히 `.pipeline/claude_handoff.md`
- Claude lane은 `READY`
- note가 `waiting_next_control`
- recent events에 `control_duplicate_ignored`가 보임

이 상태의 의미:

- canonical control file은 남아 있지만 runtime은 해당 handoff를 재실행하지 않습니다.
- watcher가 same-handoff SHA의 no-op completion을 감지해 Codex triage로 되돌린 상태입니다.
- operator는 pane 텍스트나 stale `WORKING` 표시만 보고 강제 restart하지 말고, Codex follow-up/control 변경을 먼저 확인합니다.

## 6.9 stale operator stop
다음 조건이 동시에 보이면 stale operator stop으로 판단합니다.

- compat control slot의 active는 여전히 `operator_request.md`
- recent events에 `control_operator_stale_ignored`가 보임
- runtime `status.control`은 `none`

이 상태의 의미:

- canonical stop 문서는 디버그 surface로 남아 있지만, runtime은 그 본문이 가리킨 blocker `/work`들이 이미 `VERIFY_DONE`으로 닫혔다고 판단한 상태입니다.
- operator는 stale stop 파일만 보고 automation을 계속 막지 말고, 최신 `/verify` 또는 다음 control 생성 여부를 먼저 확인해야 합니다.
- stale stop suppression은 operator 문서를 삭제하거나 rewrite하는 동작이 아니라 supervisor read-model 정규화입니다.
- watcher는 이 상태에서 startup/rolling turn을 `CODEX_FOLLOWUP`으로 다시 열고, Codex에게 다음 canonical control outcome을 다시 쓰도록 1회 control-recovery prompt를 보낼 수 있습니다.
- 이때 browser/TUI 표면에서는 `control=none`이더라도 Codex lane이 `WORKING` / `followup`으로 보일 수 있습니다.

## 6.10 gated operator candidate
다음 조건이 동시에 보이면 gated operator candidate로 판단합니다.

- `.pipeline/operator_request.md`는 존재하고 valid `STATUS: needs_operator` + `CONTROL_SEQ`를 가진다.
- runtime `status.control`은 `none`이다.
- runtime `status.autonomy.mode`가 `recovery`, `triage`, `hibernate`, `pending_operator` 중 하나다.
- recent events에 `control_operator_gated` 또는 `autonomy_changed`가 보인다.

이 상태의 의미:

- canonical operator stop 파일은 남아 있지만, supervisor/watcher가 이를 즉시 operator wait current truth로 승격하지 않은 상태입니다.
- `status.autonomy.block_reason`과 `suppress_operator_until`이 24시간 gate의 이유와 deadline입니다.
- `recovery`면 lane/session/receipt/auth 계열 자가복구가 먼저이고, `triage`면 Codex/Gemini 판단이 먼저이며, `hibernate`면 현재는 idle stable이라 operator 호출 없이 unattended로 유지하는 편이 맞습니다.
- `pending_operator`는 immediate safety/approval/truth-sync는 아니지만 아직 exact self-route가 닫히지 않은 후보라는 뜻입니다.
- 이 상태에서 operator는 stop 파일만 보고 즉시 재기동/강제 attach하지 말고, Codex follow-up 또는 gate window 경과 여부를 먼저 확인해야 합니다.

## 6.11 duplicate supervisor
다음 조건이 보이면 duplicate supervisor로 판단합니다.

- 같은 `project_root + session`으로 `pipeline_runtime.cli daemon`이 2개 이상 떠 있음
- `.pipeline/supervisor.pid`가 가리키는 pid와 `current_run.json` writer가 서로 다르게 흔들림
- launcher/controller가 방금 시작한 run이 아니라 더 오래된 run 상태를 다시 surface함

대응:

1. `python3 -m pipeline_runtime.cli stop <project-root> --session <session>` 실행
2. live daemon이 모두 내려갔는지 확인
3. `python3 -m pipeline_runtime.cli start <project-root> --mode experimental --session <session> --no-attach`로 새 run 1개만 다시 시작
4. `supervisor.pid`, `current_run.json`, live process 목록이 같은 run 하나로 맞는지 확인

메모:

- 최신 CLI는 같은 `project_root + session` daemon을 reconcile하도록 되어 있으므로, 정상이라면 restart 후 duplicate writer가 남지 않아야 합니다.
- 이 증상은 launcher readiness 계산 문제가 아니라 single-writer lifecycle 문제가 먼저 깨진 경우입니다.

## 7. 운영자가 보면 안 되는 신호

아래는 “보조 신호”이지 current truth가 아닙니다.

- pane에 프롬프트 기호가 보인다는 사실
- 최신 `verify/*.md` 파일이 갱신된 사실
- watcher.log에 “working” 비슷한 문구가 보이는 사실
- pid 파일이 남아 있다는 사실

이 신호들은 디버깅에는 유용하지만, 상태 판정 기준으로 쓰면 안 됩니다.

## 8. 복구 전략

## 8.1 자동복구 우선
- lane 단위 재시작
- stale lease cleanup
- status refresh
- receipt 재검증

## 8.2 수동개입 조건
아래 경우에만 수동개입을 허용합니다.

- P1 장애
- 같은 lane 3회 연속 auto-recovery 실패
- current_run continuity 상실
- state corruption 확산

## 8.3 롤백 조건
- 새 supervisor build가 false READY를 만들 때
- receipt gating이 오히려 close를 막는 결함이 있을 때
- backend adapter health가 반복 오판할 때

## 9. 보고서 템플릿

### 장애 보고 최소 항목
- 발생 시각
- run_id
- runtime_state
- 영향 범위
- degraded reason 또는 broken lane
- 자동복구 결과
- 수동개입 여부
- 재현 가능성
- 후속 조치

## 10. 운영 종료 후 체크
- 마지막 receipt flush 완료
- orphan process 없음
- current_run 종료 상태 기록
- open incident 없음
- 다음 run에 넘길 known issue 정리

## 11. 결론

운영 문서의 핵심은 “무엇을 보느냐”보다 “무엇을 믿느냐”입니다.  
이 구조에서는 pane 화면이나 최신 파일보다 supervisor status와 receipt를 우선해야 운영이 안정됩니다.
