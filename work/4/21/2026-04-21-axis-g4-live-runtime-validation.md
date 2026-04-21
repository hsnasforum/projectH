# 2026-04-21 AXIS-G4 live runtime validation

## 변경 파일
- `work/4/21/2026-04-21-axis-g4-live-runtime-validation.md` (새 파일)

## 사용 skill
- `security-gate`: runtime restart, `.pipeline` event/log/status 관측, shell execution이 포함된 검증 전용 작업의 local/audit 경계를 확인했습니다.
- `work-log-closeout`: 실행한 명령과 실측 결과만 기준으로 `/work` closeout 형식을 맞췄습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` CONTROL_SEQ 628의 AXIS-G4 end-to-end 검증 지시에 따라 live runtime에서 `DISPATCH_SEEN` / `TASK_ACCEPTED`, synthetic `job_id` / `dispatch_id`, watcher idle-release 방출 여부를 확인했습니다.
- production 코드는 수정하지 않았고, 검증 결과만 기록했습니다.

## 핵심 변경
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach`를 실행했습니다. 출력은 없었고 rc=0으로 종료됐습니다.
- handoff에 적힌 `python3 -m pipeline_runtime.cli status /home/xpdlqj/code/projectH`는 현재 CLI에 `status` subcommand가 없어 rc=2로 실패했습니다.
- 대체 확인 경로인 `.pipeline/current_run.json` → `.pipeline/runs/20260421T070544Z-p202761/status.json` 기준 status는 `runtime_state=STARTING`, `turn_state.state=IMPLEMENT_ACTIVE`, `active_control_seq=628`, `watcher={"alive": false, "pid": null}`였습니다.
- handoff의 root-level `.pipeline/events.jsonl` 확인 스크립트는 `events.jsonl 없음`을 출력했습니다. 실제 run-local event file은 `.pipeline/runs/20260421T070544Z-p202761/events.jsonl`였습니다.
- run-local `events.jsonl`에는 `event_type=dispatch_selection`이 반복 발행됐습니다. 마지막 확인 시 `dispatch_selection_count=184`였고 payload는 `work_path`/`verify_path`가 아니라 `latest_work`/`latest_verify` 키를 사용했습니다.
- `DISPATCH_SEEN` / `TASK_ACCEPTED`는 supervisor `events.jsonl`에는 없었지만 `.pipeline/runs/20260421T070544Z-p202761/wrapper-events/codex.jsonl`에는 발행됐고, 둘 다 synthetic `job_id="ctrl-628"`, `dispatch_id="seq-628"`를 포함했습니다.
- task hint도 `.pipeline/runs/20260421T070544Z-p202761/task-hints/codex.json`에서 `active=true`, `job_id="ctrl-628"`, `dispatch_id="seq-628"`, `control_seq=628`로 확인됐습니다.
- idle-release는 현재 turn이 `IMPLEMENT_ACTIVE`라 handoff가 말한 idle-eligible 상태(`VERIFY_FOLLOWUP` / `ADVISORY_ACTIVE` 등)가 아니었습니다. root `.pipeline/events.jsonl` 기준 idle-release 검사도 `events.jsonl 없음`이었고, `.pipeline/claude_handoff.md` mtime은 `2026-04-21 16:07:28.319820108 +0900`로 유지됐습니다.

## 검증
- `sha256sum .pipeline/claude_handoff.md`
  - 결과: `b64e8c2abdf22aa019194de7ea5afb15fe88afa1c8ff93d8acb94562fefa13a1`, handoff 입력 SHA와 일치.
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach`
  - 결과: 출력 없음, rc=0.
- `python3 -m pipeline_runtime.cli status /home/xpdlqj/code/projectH`
  - 결과: rc=2, `invalid choice: 'status' (choose from 'start', 'stop', 'restart', 'daemon', 'attach', 'lane-wrapper')`.
- handoff root event 확인 스크립트:
  - 결과: `events.jsonl 없음`.
- `.pipeline/current_run.json` / current run `status.json` 직접 확인:
  - 결과: `run_id=20260421T070544Z-p202761`, `status_path=.pipeline/runs/20260421T070544Z-p202761/status.json`, `events_path=.pipeline/runs/20260421T070544Z-p202761/events.jsonl`, `runtime_state=STARTING`, `turn_state_state=IMPLEMENT_ACTIVE`, `turn_state_seq=628`, `watcher={'alive': False, 'pid': None}`.
- run-local dispatch event 확인:
  - 대표 결과: `{"event_type":"dispatch_selection","payload":{"latest_work":"4/21/2026-04-21-menu-choice-advisory-routing.md","latest_verify":"4/21/2026-04-21-g4-supervisor-signal-mismatch-deferral-verification.md",...}}`
  - 후속 결과: `{"event_type":"dispatch_selection","payload":{"latest_work":"4/21/2026-04-21-operator-retriage-no-control-recovery.md","latest_verify":"—",...}}`
  - 최종 확인: `dispatch_selection_count=184`.
- wrapper event 확인:
  - `DISPATCH_SEEN`: `{"lane":"Codex","event_type":"DISPATCH_SEEN","payload":{"pid":203557,"job_id":"ctrl-628","dispatch_id":"seq-628","control_seq":628,"attempt":1},"derived_from":"task_hint"}`
  - `TASK_ACCEPTED`: `{"lane":"Codex","event_type":"TASK_ACCEPTED","payload":{"pid":203557,"job_id":"ctrl-628","dispatch_id":"seq-628","control_seq":628,"attempt":1},"derived_from":"vendor_output"}`
  - `TASK_DONE`: `{"lane":"Codex","event_type":"TASK_DONE","payload":{"pid":203557,"job_id":"ctrl-628","control_seq":628,"dispatch_id":"seq-628"},"derived_from":"vendor_output"}`
- `stat .pipeline/claude_handoff.md`
  - 결과: Modify `2026-04-21 16:07:28.319820108 +0900`. idle-release handoff rewrite로 보이는 mtime 갱신은 없었습니다.

## 남은 리스크
- `DISPATCH_SEEN` / `TASK_ACCEPTED`는 wrapper-events에는 발행됐지만 supervisor run-local `events.jsonl`에는 집계되지 않았습니다. 따라서 "events.jsonl에 발행"이라는 검증 목표 기준으로는 아직 미충족이며, wrapper emitter 자체가 아니라 supervisor event aggregation 또는 검사 대상 경로/키(`event` vs `event_type`) 불일치가 남은 원인으로 보입니다.
- `dispatch_selection`은 run-local `events.jsonl`에 발행됐지만 payload가 handoff 기대값인 `work_path` / `verify_path`가 아니라 `latest_work` / `latest_verify`입니다.
- `runtime_state=RUNNING` 확인은 못 했습니다. 현재 status 대체 경로에서는 `STARTING`으로 남아 있고 watcher는 `alive=false`입니다.
- idle-release는 현재 `turn_state=IMPLEMENT_ACTIVE`라 조건 불충족으로 동작 여부를 확인하지 못했습니다.
- `.pipeline/operator_request.md`에 기록된 false-positive 이슈는 유지됩니다: seq 625 menu-choice advisory-first routing이 `(B)/(C)/(D)` parenthesized label을 병렬 선택지로 오감지했지만 실제로는 "B 통과 후 C", "C 완료 후 D" 순차 승인 게이트입니다. 해당 note는 `suppress_until: 2026-04-22` gate window 내 실영향 없음으로 기록하고 있으며, 만료 전 또는 B 결정 후 별도 follow-up이 필요합니다.
- 이번 작업은 local runtime restart와 local `.pipeline` 파일 관측만 수행했습니다. 외부 네트워크, approval/save flow, production 코드 변경, commit/push/PR은 수행하지 않았습니다.
