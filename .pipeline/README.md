# /.pipeline 정책

`.pipeline`은 projectH의 role-bound tmux 운영에서 쓰는 **rolling automation handoff 슬롯**입니다.

이 폴더는 최신 프롬프트를 자동화 프로그램이 읽기 쉽게 두는 용도이며, 역사 기록이나 canonical truth 저장소가 아닙니다.
따라서 `.pipeline` 파일은 기본적으로 **영어 중심 실행 지시**를 담는 편이 맞고, persistent 기록인 `/work`, `/verify`, `report/`와 역할을 섞지 않습니다.

현재 stage-3 흐름은 `start-pipeline.sh`가 띄우는 `watcher_core.py` experimental 경로에 반영되어 있습니다.
실제 자동 실행 기준은 `start-pipeline.sh` + `watcher_core.py` 경로를 우선합니다.
launcher / setup / supervisor / smoke는 scattered fixed-owner branch 대신 shared physical lane catalog(`Claude`, `Codex`, `Gemini`)와 active profile에서 resolve한 runtime plan을 single source로 읽는 편이 맞습니다.
이 runtime plan의 `lane_configs`는 항상 세 physical lane을 모두 포함하고, 각 lane에 `enabled`, `roles`, `read_first_doc`, `token_source_root` 같은 metadata를 함께 실어 thin client가 fixed owner를 다시 추론하지 않게 하는 편이 맞습니다.

## 파일 역할

Canonical role-based control filenames are `implement_handoff.md`,
`advisory_request.md`, `advisory_advice.md`, and `operator_request.md`.
Historical aliases `claude_handoff.md`, `gemini_request.md`, and
`gemini_advice.md` are read-only compatibility inputs for the same logical
slots. They must not create a second control plane. If both canonical and alias
files exist for the same slot, runtime resolves them as one slot: higher
`CONTROL_SEQ` wins, and the canonical filename wins when `CONTROL_SEQ` ties.

- `implement_handoff.md`
  - 작성자: active verify/handoff owner
  - 역할: active implement owner가 읽는 implement handoff 슬롯
  - 형식: 현재 stage-3에서는 `STATUS: implement` + `CONTROL_SEQ`
  - 실제 owner는 active `role_bindings.implement`를 따름
- `advisory_request.md`
  - 작성자: active verify/handoff owner
  - 역할: active advisory owner에게 넘기는 arbitration 요청 슬롯
  - 형식: 현재 stage-3에서는 `STATUS: request_open` + `CONTROL_SEQ`
- `advisory_advice.md`
  - 작성자: active advisory owner
  - 역할: active verify/handoff owner가 읽는 advisory 슬롯
  - 형식: 현재 stage-3에서는 `STATUS: advice_ready` + `CONTROL_SEQ`
  - advisory 출력은 file edit/write tool 우선, shell heredoc/redirection은 피하는 편이 맞음
  - 읽기 대상은 가능하면 `@path` 형식의 명시적 file mention으로 붙이고, advisory log / advice slot도 prompt에 적힌 정확한 경로로 바로 쓰는 편이 맞음
- `operator_request.md`
  - 작성자: active verify/handoff owner
  - 역할: operator만 읽는 정지 슬롯
  - 형식: 현재 stage-3에서는 `STATUS: needs_operator` + `CONTROL_SEQ` + `REASON_CODE` + `OPERATOR_POLICY` + `DECISION_CLASS` + `DECISION_REQUIRED` + `BASED_ON_WORK` + `BASED_ON_VERIFY`
  - runtime/script가 이 파일을 machine-write해야 할 때는 `pipeline_runtime.control_writers.write_operator_request(...)`를 써서 필수 top header 누락을 막는 편이 맞음
- `session_arbitration_draft.md`
  - 작성자: watcher
  - 역할: active implement-owner session의 live side question을 감지했고 verify/advisory lanes가 idle이며 implement owner가 idle이거나 같은 escalation text에 짧게 안정됐을 때만 남기는 non-canonical draft 슬롯
  - 형식: `STATUS: draft_only`만 포함
  - 자동 실행 슬롯이 아니며 watcher / active implement owner / active advisory owner는 이 파일만으로 dispatch하지 않음
  - resolved 조건이 생기면 watcher가 정리할 수 있으며, 같은 fingerprint는 짧은 cooldown 동안 즉시 다시 열지 않음
- `codex_feedback.md`
  - 작성자: optional
  - 역할: scratch / legacy compatibility text only
  - canonical execution path에서는 읽지 않음
- `gpt_prompt.md`
  - 작성자: active verify/handoff owner 또는 operator
  - 역할: optional/legacy scratch 슬롯
  - canonical role-bound 흐름에서는 필수 아님
- `harness/`
  - 작성자: runtime/operator docs
  - 역할: active role별 짧은 SOP와 막힘 수렴 protocol
  - 파일: `implement.md`, `verify.md`, `advisory.md`, `council.md`
  - control slot이 아니며 dispatch authority도 아님. watcher prompt의 `ROLE_HARNESS` / `COUNCIL_HARNESS` 경로로만 노출되어 각 lane이 role boundary와 출력 형식을 빠르게 맞추게 합니다.
- `archive-stale-control-slots.sh`
  - 작성자: operator / active verify-handoff owner 수동 실행
  - 역할: active `CONTROL_SEQ`/status 기준 control file은 보존한 채 오래된 stale control slot만 `.pipeline/archive/YYYY-MM-DD/`로 옮기는 수동 helper
  - 형식: `--all-stale` 또는 explicit slot basename 인자

## turn_state.json

`.pipeline/state/turn_state.json`은 watcher가 매 턴 전이마다 atomic write하는 단일 상태 파일입니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| `state` | string | `IDLE`, `IMPLEMENT_ACTIVE`, `VERIFY_ACTIVE`, `VERIFY_FOLLOWUP`, `ADVISORY_ACTIVE`, `OPERATOR_WAIT` |
| `legacy_state` | string | (선택) legacy watcher enum mirror (`CLAUDE_ACTIVE`, `CODEX_VERIFY`, `CODEX_FOLLOWUP`, `GEMINI_ADVISORY`) |
| `entered_at` | float | 전이 시각 (epoch) |
| `reason` | string | 전이 사유 |
| `active_control_file` | string | 현재 active control slot 파일명 |
| `active_control_seq` | int | 현재 active CONTROL_SEQ (-1이면 없음) |
| `active_role` | string | 현재 turn의 semantic role (`implement`, `verify`, `advisory`, `operator`) |
| `active_lane` | string | 현재 turn을 맡은 실제 owner lane 이름 (`Claude`, `Codex`, `Gemini`) |
| `verify_job_id` | string | (선택) 현재 verify 대상 job ID |

- 이 파일은 watcher 내부 canonical state의 **UI 투영**입니다. job state를 대체하지 않습니다.
- `state`는 role-first current turn authority이고, `legacy_state`는 한 릴리즈 윈도우 동안만 남기는 compat/debug mirror입니다. thin client는 `state`와 `active_role`/`active_lane`을 우선 읽는 편이 맞습니다.
- `pipeline_gui/backend.py`는 이 파일이 있으면 이것만 읽어 표시합니다. control slot 재해석과 혼합하지 않습니다.
- 이 파일이 없으면 기존 control slot + job state 해석으로 fallback합니다.

## 운영 원칙

- 이 두 파일은 최신 슬롯 파일이므로 라운드마다 덮어써도 됩니다.
- persistent truth는 항상 아래에 남깁니다.
  - 구현 truth: `/work`
  - 검증 truth: `/verify`
- `.pipeline/current_run.json`과 `.pipeline/runs/<run_id>/...`는 runtime authority/generated state 산출물이라 local start/stop 중 다시 생기는 것이 정상입니다. 경로 자체는 canonical로 유지하되, source diff와 섞이지 않도록 Git-generated artifact로 취급하는 편이 맞습니다.
- `/work`, `/verify`, `report/` 같은 persistent 기록은 기본적으로 한국어로 남깁니다.
- `.pipeline` execution/control 슬롯은 기본적으로 concise English-led instructions를 유지합니다.
- `.pipeline/harness/*.md`도 execution-facing English-led protocol입니다. 다만 이 파일들은 control slot이 아니라 role protocol입니다. 최신 `/work`, `/verify`, active control, supervisor status/events와 충돌하면 current truth가 우선합니다.
- 파일 경로, 테스트 이름, selector, field name 같은 literal identifier는 기록 언어와 무관하게 원문 그대로 둡니다.
- `.pipeline` 내용과 `/work` 또는 `/verify`가 충돌하면 `/work`와 `/verify`를 우선합니다.
- watcher는 active `IMPLEMENT_ACTIVE` 구현 라운드가 이미 진행 중이면 기본적으로 새 `implement_handoff.md`를 즉시 hot-swap하지 않고, 현재 라운드가 `/work`, `implement_blocked`, 또는 idle timeout으로 닫힌 뒤 다음 판정에서 반영하는 편이 맞습니다. 다만 더 높은 `CONTROL_SEQ`의 implement handoff가 active control이 되었고 이전 implement pane이 이미 prompt-ready idle이면, stale turn-state 고착을 피하기 위해 `implement_handoff_idle_release`로 새 handoff를 재전달할 수 있습니다.
- watcher는 control slot 변경만으로 verify/handoff-owner round를 닫지 않습니다. 현재 라운드 시작 이후의 `/verify` receipt가 실제로 갱신된 것이 확인될 때만 feedback-only completion을 인정합니다.
- watcher prompt에는 active root memory file과 live control/work/verify path 외에 `ROLE_HARNESS` / `COUNCIL_HARNESS` path가 표시될 수 있습니다. 이 경로는 CLI-Anything식 self-contained skill/SOP 패턴을 흡수한 role protocol이며, `READ_FIRST`의 owner root doc 규칙이나 current truth authority를 대체하지 않습니다.
- verify/handoff-owner round가 idle timeout에 걸렸는데 current-round `/verify` receipt나 next control output이 아직 incomplete하면, watcher는 그 라운드를 terminal done으로 닫지 않고 `VERIFY_PENDING`으로 되돌려 backoff 후 자동 재시도를 거치게 하는 편이 맞습니다.
- verify/handoff-owner pane이 busy indicator 없이 idle prompt로 빨리 돌아왔는데 current-round `/verify` receipt나 next control output이 아직 incomplete하면, watcher는 5분 full timeout까지 붙들지 말고 short idle window 뒤 `VERIFY_PENDING`으로 되돌려 재시도하는 편이 맞습니다.
- 새 verify dispatch에는 `dispatch_id`와 `accept_deadline`이 같이 붙고, wrapper는 active task hint를 실제로 읽은 순간 `DISPATCH_SEEN`, 실제 작업 수락 신호가 보일 때 `TASK_ACCEPTED`를 emit하는 편이 맞습니다.
- verify owner lane에서는 일반 busy marker가 늦게 보여도 첫 `• ...` 작업 시작선을 `TASK_ACCEPTED` 증거로 같이 인정하는 편이 맞습니다. verify dispatch helper도 input prompt가 실제로 소비된 뒤에는 immediate busy/activity 확인이 비어 있어도 이를 dispatch 성공으로 보고, 이후 acceptance 판단은 wrapper `DISPATCH_SEEN` / `TASK_ACCEPTED` deadline이 맡는 편이 맞습니다. prompt consumed를 곧바로 dispatch 실패로 되돌리면 같은 verify prompt가 한 번 더 paste될 수 있습니다.
- wrapper의 task-level event(`DISPATCH_SEEN`, `TASK_ACCEPTED`, `TASK_DONE`, `BRIDGE_DIAGNOSTIC`)는 lane별 `wrapper-events/*.jsonl`에 원본으로 남고, supervisor가 같은 current run의 `events.jsonl`에도 `source: "wrapper"`로 de-dupe mirror합니다. 반복 heartbeat는 canonical event stream으로 mirror하지 않습니다.
- verify round는 `status.control=none`이어도 `active_round.dispatch_control_seq`, `job_id`, `dispatch_id`를 가진 round-scoped task hint로 verify dispatch를 계속 이어가는 편이 맞습니다. supervisor는 active control slot이 없다는 이유만으로 verify hint를 inactive로 내리면 안 됩니다.
- 반대로 `VERIFY_FOLLOWUP` / `ADVISORY_ACTIVE` turn에서는 stale verify `job_id`/`dispatch_id`/`dispatch_control_seq`를 current task hint나 `active_round` surface에 다시 싣지 않는 편이 맞습니다. follow-up/advisory는 current control seq를 쓰고, 이전 verify round truth는 current surface에서 비워야 합니다.
- watcher는 current run의 wrapper `DISPATCH_SEEN`, `TASK_ACCEPTED`, `TASK_DONE`를 그 dispatch와 직접 연결해 보며, prompt가 잠깐 idle처럼 보인다는 이유만으로 pre-accept stall이나 post-accept completion을 바로 확정하지 않는 편이 맞습니다.
- `TASK_DONE`은 최소 `job_id`, `control_seq`, `dispatch_id`를 함께 내보내는 선행 완료 신호입니다. stale old `TASK_DONE`가 새 verify dispatch를 닫지 않도록 watcher는 current `dispatch_id`와 일치하는 경우에만 이를 유효하게 봅니다.
- wrapper read model이 최신 state를 평탄화하는 과정에서 same-dispatch `TASK_ACCEPTED`가 이미 `TASK_DONE` 뒤에 접혀 보이지 않을 수 있습니다. 이 경우 verify FSM은 current dispatch의 matching `TASK_DONE`를 accept의 더 강한 증거로 보고 `task_accept_missing` 재큐잉으로 되감지 않는 편이 맞습니다.
- wrapper는 verify hint가 아직 active여도 같은 dispatch가 prompt-visible + no-busy 상태로 짧게 settle되면 `TASK_DONE`를 직접 emit할 수 있어야 합니다. `TASK_DONE`를 task-hint clear 이후로만 미루면 verify close chain이 순환에 빠집니다.
- wrapper는 verify hint가 active인데 `control_seq` metadata가 비정상이면 event를 조용히 생략하지 않고 `BRIDGE_DIAGNOSTIC(code=active_task_hint_metadata_invalid)`를 남기는 편이 맞습니다. silent no-event가 다시 false `dispatch_stall`로 숨으면 안 됩니다.
- verify/handoff-owner round close는 원칙적으로 `TASK_ACCEPTED -> TASK_DONE -> current-round /verify receipt + next control -> receipt close` 순서로만 허용합니다. 다만 `TASK_ACCEPTED` 뒤 done deadline까지 matching `TASK_DONE`가 없고, lane이 idle이며, current-round `/verify` receipt와 next control이 모두 닫혔을 때는 wrapper 신호 누락으로 보아 FSM이 `TASK_DONE`를 산출물 기반으로 보조 추론할 수 있습니다. 이 보조 추론은 작업 중 pane이나 incomplete output에는 적용하지 않습니다.
- current run에 `VERIFY_RUNNING` job이 남아 있으면 watcher는 그 job을 terminal close 또는 재큐잉까지 계속 step하는 편이 맞습니다. 이때 오래된 다른 unverified `/work`를 새 verify candidate로 먼저 끼워 넣어 current round lease release나 pending implement handoff를 가리지 않는 편이 맞고, 열린 `.pipeline/advisory_request.md` / `.pipeline/advisory_advice.md`가 있어도 current-run `VERIFY_RUNNING` close chain은 먼저 굴려 얼리지 않는 편이 맞습니다.
- 다만 fresh automatic verify scan은 historical backlog 전체를 다시 훑지 않고 최신 canonical `/work` 한 장만 기준으로 여는 편이 맞습니다. 오래된 unmatched `/work`는 새 스캔으로 다시 끌어오지 말고, 이미 열린 current-run `VERIFY_PENDING` / `VERIFY_RUNNING` job replay나 operator가 명시한 reverify 경로에서만 이어지는 편이 맞습니다.
- 반대로 merely `VERIFY_PENDING`인 current-run job replay나 새 `/work` verify candidate 스캔은 `VERIFY_FOLLOWUP` / `ADVISORY_ACTIVE` / gated operator retriage 같은 current control-resolution turn이 살아 있는 동안 끼어들지 않는 편이 맞습니다. 이 경계가 풀리기 전 stale verify가 같은 pane에 다시 paste되면 follow-up/advisory control truth가 오염됩니다.
- `slot_verify` lease owner인 supervisor pid가 **유효한 pid로 읽히고도 `signal 0`에 응답하지 않을 때만** watcher는 그 lease를 TTL까지 active로 붙들지 않고 stale lock으로 즉시 정리하는 편이 맞습니다. supervisor 비정상 종료 뒤에도 새 handoff나 recovery turn이 lease TTL에 묶여 지연되면 안 됩니다.
- `PaneLease`의 `owner_pid_path`는 watcher init 시점의 `supervisor.pid` 존재 여부와 무관하게 항상 `<base>/supervisor.pid`를 가리키는 편이 맞습니다. init 시점에만 존재 여부를 체크해 None으로 고정해 두면 watcher가 supervisor보다 먼저 뜨는 start-up race에서 owner-death 감지가 영구적으로 꺼집니다. 반대로 "pid 파일 없음" 자체는 standalone 운영(예: 테스트/수동 디버깅)을 의미하므로 dead로 해석하지 않고, 유효 pid가 `signal 0`에 응답하지 않을 때만 dead로 판정해 stale lock을 정리합니다.
- supervisor의 `finally` unlink는 `SIGTERM`/`SIGINT` 같은 정상 종료 경로에서만 기대하는 편이 맞습니다. `SIGKILL`처럼 `finally`가 실행되지 않는 종료에서는 stale `supervisor.pid` 파일이 남을 수 있으며, 이 경우 cleanup 책임은 죽는 supervisor가 아니라 살아남은 watcher의 owner-death 판정이 맡습니다.
- `slot_verify.lock`에는 lease를 잡을 때의 `owner_pid`를 함께 남기는 편이 맞습니다. 그렇지 않으면 supervisor가 재시작돼 새 `supervisor.pid`가 살아 있는 상태에서도 예전 lease를 current owner가 잡은 것처럼 착각해 `lease_busy`가 TTL까지 남을 수 있습니다. legacy lock처럼 `owner_pid`가 없는 경우에도 current `supervisor.pid` mtime이 lock 시작 시각보다 더 새로우면 restart 이후 stale lease로 보고 정리하는 편이 맞습니다.
- `DISPATCH_SEEN`조차 deadline 안에 오지 않으면 lane note를 `waiting_dispatch_seen_after_dispatch`로 두고, `DISPATCH_SEEN`은 왔지만 `TASK_ACCEPTED`가 deadline 안에 오지 않았을 때만 `waiting_task_accept_after_dispatch`로 보는 편이 맞습니다.
- 다만 pre-accept stall을 한 번 재큐잉한 뒤 pane tail에 `[Pasted Content ...]` 같은 직전 paste 잔상이 그대로 남아 있으면, prompt cursor가 다시 보여도 watcher는 그 snapshot을 실패 증거로 보존하고 same-snapshot backoff 동안 재dispatch하지 않는 편이 맞습니다. bare idle prompt만 snapshot 없이 short retry 대상입니다.
- `TASK_ACCEPTED`는 왔지만 `TASK_DONE`이 verify done deadline 안에 오지 않으면 lane note를 `waiting_task_done_after_accept`로 두고, `TASK_DONE` 뒤에도 receipt/control close가 안 오면 `waiting_receipt_close_after_task_done`로 남기는 편이 맞습니다.
- 다만 pane tail이 `Waiting for background terminal`처럼 active background wait를 계속 보여주는 동안에는 `TASK_DONE` missing deadline을 그대로 stall로 승격하지 않고, post-accept active wait로 유지하며 done deadline을 밀어주는 편이 맞습니다.
- 같은 fingerprint에서 위 상황이 한 번 더 반복되면 watcher는 이를 `dispatch_stall` incident로 승격하고, 해당 machine note를 유지한 채 추가 자동 재큐잉 없이 degraded surface로 넘기는 편이 맞습니다.
- 같은 fingerprint에서 post-accept completion wait가 한 번 더 반복되면 watcher는 이를 `post_accept_completion_stall` incident로 승격하고, supervisor events에는 `completion_stall_detected`, degraded reason에는 `post_accept_completion_stall`을 남기는 편이 맞습니다.
- launcher recent log에는 `dispatch_stall_detected`와 `completion_stall_detected`가 그대로 보여야 하며, controller/index.html은 새 전용 액션 없이 기존 degraded reason / lane note / recent event만 읽는 편이 맞습니다.
- no-silent-stall contract상 자동화가 멈추거나 주의 상태로 내려가면 supervisor status/events에는 최소 `automation_reason_code`, `automation_incident_family`, `automation_next_action` 중 하나가 남아야 합니다. canonical incident family는 `signal_mismatch`, `dispatch_stall`, `completion_stall`, `operator_retriage_no_next_control`, `stale_control_advisory`, `idle_release_pending`, `lane_recovery_exhausted`, `session_recovery_exhausted`입니다.
- supervisor는 launcher용 derived field `automation_health = ok|recovering|attention|needs_operator`, `automation_reason_code`, `automation_incident_family`, `automation_next_action = continue|retrying|advisory_followup|verify_followup|operator_required|pr_boundary`, `control_age_cycles`, `stale_control_seq`, `stale_control_cycle_threshold`를 `status.json`에 함께 씁니다. `stale_control_seq=true`는 같은 active `CONTROL_SEQ`가 오래 이어졌다는 surface입니다. advisory grace까지 지나면 `automation_health=attention`, `automation_reason_code=stale_control_advisory`, `automation_next_action=advisory_followup`으로 승격해 launcher가 이를 정상 진행으로 숨기지 않습니다. 같은 health/reason/action 조합이 새로 승격되면 `events.jsonl`에는 `automation_incident` event를 남깁니다.
- `operator_approval_completed`는 dirty worktree commit/push 승인 stop이 이미 read-only git 증거로 충족된 recovery reason입니다. watcher는 branch/upstream/HEAD와 rolling `.pipeline` artifact 외 clean worktree를 확인한 뒤 `VERIFY_FOLLOWUP`으로 라우팅하고, launcher/GUI는 이를 `승인 작업 완료, 다음 제어 정리 중`으로 표시합니다. raw reason은 상세 console 또는 `events.jsonl` debug context에만 남깁니다.
- `commit_push_bundle_authorization`은 operator가 이미 큰 검증 묶음을 publish 대상으로 승인한 뒤의 자동화 follow-up reason입니다. `OPERATOR_POLICY: internal_only`와 함께 오면 unattended hibernate가 아니라 verify/handoff-owner triage(`routed_to=verify_followup`)로 보내며, 작은 local slice의 dirty state를 자동 publish하라는 뜻은 아닙니다.
- `pr_creation_gate`는 승인된 큰 묶음의 draft PR 생성 follow-up reason입니다. `OPERATOR_POLICY: gate_24h`, `DECISION_CLASS: release_gate`와 함께 오면 operator wait가 아니라 verify/handoff-owner triage(`routed_to=verify_followup`)로 보내고 `automation_next_action=verify_followup`으로 보여야 합니다.
- `external_publication_boundary` / `publication_boundary` / `pr_boundary` / `pr_merge_gate`는 draft PR 생성 follow-up이 아니라 merge, release, destructive publication 같은 실제 외부 공개 경계입니다. 이 reason은 `gate_24h`, `internal_only`, idle stable 상태여도 `hibernate + ok`나 verify follow-up으로 숨기지 않고 `automation_health=needs_operator`, `automation_next_action=pr_boundary`로 보여야 합니다. 예외적으로 `pr_merge_gate`가 참조한 PR 번호가 이미 merged임을 `gh pr view`로 확인할 수 있으면 supervisor/watcher는 `pr_merge_completed` recovery로 canonical `control`을 `none`으로 내리고 stale operator wait를 재표시하지 않습니다. control 본문의 `HEAD`가 merged PR의 `headRefOid`와 다르면 닫힌 PR 번호를 재사용한 잘못된 gate이므로 `pr_merge_head_mismatch` recovery로 내리고 verify/handoff가 새 PR 또는 control을 바로잡게 합니다.
- 이 publish follow-up은 implement handoff로 넘기지 않습니다. implement prompt는 commit/push/branch publish/PR을 계속 금지하므로, verify/handoff owner가 범위를 확인해 직접 실행하거나 직접 실행할 수 없으면 advisory escalation으로 닫아야 합니다.
- 선택지 메뉴, ABCD/숫자/inline label 선택, next-slice ambiguity, session rollover, context exhaustion은 real-risk metadata가 없으면 operator stop이 아니라 `automation_next_action=advisory_followup` 또는 `verify_followup`으로 라우팅합니다. 삭제/덮어쓰기, auth/credential, approval/truth-sync, safety stop, merge/destructive publication boundary만 operator boundary로 남깁니다.
- launcher/controller/GUI는 thin client이므로 current truth를 runtime `status.json` / `events.jsonl` canonical block에서만 읽는 편이 맞습니다. `turn_state`는 current turn authority, `active_round`는 current verify round일 때만 surface하고, `compat.control_slots` / pane/log/file scan은 drift detection 보조로만 씁니다. `automation_health != needs_operator`인 recovery/verify 상태에서는 compat `operator_request.md`를 active operator wait로 색칠하지 않습니다.
- supervisor는 `turn_state`, `active_round`, 최신 work/verify mtime, control/autonomy block만으로 `status.progress.phase`와 active lane의 `progress_phase`를 함께 계산합니다. 이 값은 사람이 pane을 보고 하던 "검증 실행 중", "`/verify` 작성 완료 후 다음 control 정리", "operator gate 후속 처리" 같은 진행 힌트이며, pane transcript 자체를 current truth로 승격하지 않습니다.
- launcher/GUI는 incident를 `정상 / 복구 중 / 주의 / 개입 필요` health label로 표시하고, raw `automation_reason_code`나 lane machine note는 상세 console/recent event에만 남깁니다.
- launcher GUI agent card는 raw machine note(`signal_mismatch`, `waiting_next_control`, `prompt_visible` 등)나 progress phase를 그대로 노출하지 않고 한국어 operator-facing label로 표시합니다. 상세 console에는 raw note와 raw `progress_phase`를 남겨 drift/debug 정보를 유지합니다.
- pane prompt/activity marker는 `pipeline_runtime/lane_surface.py`의 shared helper/profile을 single source로 두는 편이 맞습니다. watcher, supervisor, cli wrapper가 서로 다른 busy/ready marker 집합을 오래 따로 들고 있으면 다음 READY/WORKING drift 씨앗이 됩니다.
- runtime이 `STOPPED`로 내려가거나 `active_round.artifact_path`가 더 새 round로 바뀌면 old `dispatch_stall`, old operator/autonomy gate, 이전 `/work` 기반 degraded reason은 current truth에서 같이 지워지는 편이 맞습니다. sidebar/runtime surface가 예전 stale gate를 현재 round와 섞어 보이면 안 됩니다.
- 다만 current receipt manifest mismatch나 active lane의 auth/post-accept breakage 같은 current boundary 파손은 runtime이 아직 살아 있는 동안(`STARTING`/`RUNNING`/session-loss recovery)에는 `runtime_state = DEGRADED`와 matching `degraded_reasons` entry로 계속 surface하는 편이 맞습니다. 반대로 supervisor가 final stop flush까지 완료해 canonical `STOPPED` snapshot을 쓰는 순간에는 그 live degraded/control/active-round surface를 비워 `STOPPED + inactive truth`를 우선하는 편이 맞습니다. stale current-round breakage가 stop 이후에도 계속 live처럼 보이면 안 됩니다.
- `STOPPED + inactive truth`도 silent OK가 아닙니다. 명시적인 active incident/control은 비우되 launcher용 derived health는 `automation_health=attention`, `automation_reason_code=runtime_stopped`, `automation_next_action=operator_required`로 남겨 사용자가 런타임이 꺼진 상태를 정상 진행으로 오해하지 않게 합니다.
- `scripts/pipeline_runtime_gate.py fault-check`는 이 degrade 우선순위 boundary를 synthetic `receipt_manifest:<job>` mismatch와 active Claude `claude_auth_login_required` 경로로 직접 재현하는 fault probe를 live session-loss / lane recovery 검증보다 먼저 수행해, supervisor가 두 경로 중 하나라도 `STARTING`/`STOPPED`로 숨기면 gate가 바로 실패하도록 합니다. 뒤이은 live `lane recovery` 단계는 wrapper가 남긴 `exit:<code>` / `pane_dead` / `heartbeat_timeout` 같은 pre-accept breakage note를 terminal로 보지 않고 retry budget 안에서 supervisor가 `recovery_started`/`recovery_completed`를 실제로 emit하는지까지 확인합니다. terminal recovery block은 `auth_login_required` 같은 명시된 failure reason으로만 좁혀 유지합니다.
- tmux session 자체가 사라진 `session loss degraded` 시나리오에서는 `session_missing`이 root cause이므로 supervisor는 representative `degraded_reason`을 `session_missing`으로 유지하고, 먼저 bounded `session_recovery_started`/`session_recovery_completed` 한 번으로 scaffold를 다시 세우는 편이 맞습니다. 이때 pane가 없는 lane별 `restart_lane()`를 바로 반복 호출해 recovery log를 스팸처럼 쌓지 않는 편이 맞고, session recovery budget은 transient `session_alive`만으로 즉시 리셋하지 않습니다. 복구 후 같은 session이 최소 300초 동안 안정적으로 살아 있을 때만 budget을 다시 채우며, 그 전에 session이 다시 사라지면 두 번째 scaffold 재생성 대신 `session_recovery_exhausted` event와 `degraded_reasons=["session_missing", "session_recovery_exhausted", ...]`를 남깁니다. per-lane `*_recovery_failed`는 session이 살아 있지만 lane만 깨진 경우의 secondary evidence로 남깁니다. fault-check의 `session loss degraded` 단계도 representative reason이 lane recovery 실패로 밀리지 않는 순서를 계속 assert합니다.
- 같은 `session loss degraded` 체크 엔트리는 사람이 읽는 `detail` 문자열 외에 `data.runtime_state` / `data.representative_reason` / `data.degraded_reasons` / `data.secondary_recovery_failures` / `data.session_recovery`를 구조화된 payload로 함께 싣습니다. `secondary_recovery_failures`는 lane 실패가 없을 때도 빈 list(`[]`)로 항상 존재하므로 CI/launcher 자동화는 detail 문자열을 scraping하지 않고 이 필드를 바로 읽습니다. `data.session_recovery`는 supervisor의 bounded recovery 계약(`session_missing` + 최소 1개 BROKEN lane)이 충족됐는지 `recovery_expected` / `broken_lane_names`로 표현하고, 기대된 경우에는 terminal `session_recovery_completed` 또는 `session_recovery_failed` 이벤트에서 읽은 `event_observed` / `event_type` / `attempt` / `result` / `error`와 원본 `event`를 싣습니다. recovery가 기대된 상황에서 terminal event가 관측되지 않으면 `session loss degraded` 자체가 실패하므로, supervisor가 scaffold 재생성을 시도 자체를 잃어버린 회귀가 representative `session_missing`만으로 가려지지 않습니다. recovery가 기대되지 않은 경로에서도 같은 스키마 키가 기본값(`recovery_expected=false`, `broken_lane_names=[]`, `event_observed=false`, 빈 문자열/빈 dict)으로 유지되어 자동화가 match 실패를 scraping 없이 읽을 수 있습니다.
- live 복구 검증 체크인 `recoverable lane pid observed`와 `lane recovery`도 같은 규약으로 구조화 `data`를 싣습니다. 전자는 `data.lane` / `data.pid` / `data.pid_available`을, 후자는 `data.event_observed` / `data.event_type` / `data.lane` / `data.attempt` / `data.result`와 원본 `data.event`를 포함하며, lane pid가 없어 복구 증거를 얻지 못한 경우에도 빈 event와 함께 `data.reason = "lane_pid_unavailable_before_fault_injection"` 같은 명시적 사유 문자열을 남깁니다.
- `fault-check` 최상단의 두 synthetic degraded-precedence 프로브(`receipt manifest mismatch degraded precedence`, `active lane auth failure degraded precedence`)도 같은 방식으로 `data.runtime_state` / `data.degraded_reasons` / `data.matched_reason`과 각각 `data.expected_reason_prefix` 또는 `data.expected_reason`을 함께 싣습니다. supervisor가 degrade를 숨겨 match가 실패한 회귀 경로에서는 `matched_reason`이 빈 문자열로 유지되므로 자동화가 detail scraping 없이 증거 부재를 읽을 수 있습니다.
- `runtime start` / `runtime stop after session loss` / `runtime restart`는 `data = {"action", "succeeded", "result"}`로 lifecycle action 결과를 구조화하고, `status surface ready`는 `data.wait_sec` / `data.ready` / `data.runtime_state` / `data.watcher_alive` / `data.active_control_status` / `data.ready_lane_names` / `data.ready_lane_count` / `data.snapshot`을 함께 실어 readiness 증거를 자동화가 snapshot helper 경로 그대로 읽을 수 있게 합니다.
- `fault-check` CLI는 markdown report와 같은 basename을 쓰는 JSON sidecar를 함께 기록합니다. `--report /tmp/projecth-runtime-fault-check.md` 호출이면 `/tmp/projecth-runtime-fault-check.json`이 함께 남고, 안에는 `{"title", "ok", "summary": {...}, "checks": [...]}` 형태로 `run_fault_check()`가 메모리에 만들던 각 entry의 `data` payload가 그대로 보존되므로 Python을 import하지 않는 consumer도 markdown scraping 없이 같은 증거를 읽을 수 있습니다.
- `synthetic-soak`와 plain `soak` CLI도 같은 basename 규칙으로 JSON sidecar를 함께 기록합니다. `run_soak()`의 summary dict는 `summary` 아래에 평탄화되어 실리고(`duration_sec`, `ready_ok`, `ready_wait_sec`, `state_counts`, `degraded_counts`, `receipt_count`, `control_change_count`, `duplicate_dispatch_count`, `classification_gate_failures`, `classification_gate_details`, `orphan_session`, `broken_seen`, `degraded_seen`, `readiness_snapshot` 등), `checks` 리스트에는 `runtime start` / `runtime ready barrier` / `classification_fallback_detected` / `stop left no orphan session` 같은 대표 체크가 그대로 포함됩니다. synthetic 경로에는 추가로 `workspace_retained`/`workspace_cleanup`이 summary에 남습니다. 실패/주의 context를 scraping하지 않도록 `runtime_context`에는 최신 status snapshot, current run id, open control, active round, recent events, `automation_health`/reason/family/action을 함께 싣습니다.
- startup/rolling dispatch 직전에는 prompt 입력줄에 남아 있는 미전송 텍스트를 먼저 비운 뒤 새 prompt를 paste하는 편이 맞습니다. 그래야 stray draft input이 다음 control prompt를 오염시키지 않습니다.
- watcher는 busy transcript, background wait, prompt-not-ready lane에 follow-up/advisory/operator/blocked-triage prompt를 곧바로 paste하지 않고 pending defer로 남기는 편이 맞습니다. 이때 runtime events에는 `lane_input_deferred`를 남겨 queued paste contamination과 normal dispatch를 구분해야 합니다.
- readiness 판정은 최근 tail 안에서 마지막 busy marker 이후 입력 prompt가 다시 보이면 prompt-ready를 우선하되, `background terminal`, `thinking with ...`, `esc to interrupt/cancel` 같은 active busy marker가 같은 tail에 남아 있으면 busy가 유지됩니다. 단순 `Working (...)` stale tail 뒤에 `❯` / `›` / `>` prompt만 보이는 경우에는 pending defer를 계속 붙잡지 않는 편이 맞습니다.
- live experimental watcher의 source(`watcher_core.py`, `watcher_dispatch.py`, `watcher_prompt_assembly.py`, `verify_fsm.py`, watcher가 직접 import하는 `pipeline_runtime/*` helper)가 `.pipeline/experimental.pid`보다 새로워지면 supervisor가 `watcher_self_restart_started` / `watcher_self_restart_completed` / `watcher_self_restart_failed` event를 남기고 watcher만 재시작합니다. 이 경로는 operator decision이 아니라 runtime-local self-reload이며, lane session/PR/publication boundary를 건드리지 않습니다.
- `pipeline_runtime.cli start`는 live supervisor가 있더라도 runtime source가 `.pipeline/supervisor.pid`보다 새로우면 no-op으로 빠지지 않고 supervisor를 graceful stop 후 새 daemon으로 교체합니다. 즉 이미 떠 있던 old supervisor가 self-restart 코드를 아직 import하지 못한 경우에도 다음 launcher/start 경계에서 operator 선택 없이 새 코드로 갈아탑니다.
- 이 queue/defer/flush/drop 경계는 `watcher_core.py` 안의 ad-hoc send branch로 흩어두기보다 `watcher_dispatch.py`에서 전담하는 편이 맞습니다. watcher core는 prompt 조립과 dispatch intent 생성까지만 맡고, 실제 paste/defer/drop/flush는 shared dispatch queue가 처리해야 drift replay가 고정됩니다.
- 같은 이유로 verify 상태기계도 `watcher_core.py`에 계속 눌러담기보다 `verify_fsm.py`가 `TASK_ACCEPTED -> TASK_DONE -> receipt close` 전이와 deadline/incident 승격을 전담하고, watcher core는 artifact/control/pane 사실 수집과 orchestrator shell 역할에 집중하는 편이 맞습니다.
- turn/control arbitration도 `turn_arbitration.py`가 watcher의 next-turn 결정과 supervisor의 active-lane/active-round suppression 우선순위를 공용으로 들고, `watcher_core.py`와 supervisor는 marker 계산 결과만 넘겨 current truth를 다시 각자 해석하지 않는 편이 맞습니다.
- prompt/context 조립은 `watcher_prompt_assembly.py` 공용 경계에 두는 편이 맞습니다. `watcher_core.py`가 긴 multi-line prompt 본문과 formatting 규칙을 계속 들고 있으면 dispatch/FSM/arbitration 분리 이후에도 giant orchestrator file이 남게 됩니다.
- pending defer는 같은 control family/current control이 아직 살아 있을 때만 유지하는 편이 맞습니다. 더 높은 `CONTROL_SEQ` handoff가 열리거나 active control이 다른 family로 넘어가면 예전 verify/advisory/implement pending prompt는 flush하지 말고 폐기해야 합니다.
- `signal_mismatch` 기반 pending drop은 implement handoff dispatch처럼 wrapper receipt가 직접 confirm해야 하는 prompt에만 적용합니다. `advisory_request`, `advisory_advice_followup`, `verify_operator_retriage`, `verify_control_recovery`, `verify_blocked_triage` 같은 control-resolution prompt는 lane이 바빠서 아직 paste되지 않았을 수 있으므로, active control drift가 없으면 큐에 남겨 lane이 prompt-ready가 될 때 flush하는 편이 맞습니다.
- `watcher_dispatch.flush_pending()`는 pending 항목마다 active control을 다시 읽어야 합니다. stale snapshot을 루프 전체에 재사용하면 seq만 바뀐 최신 handoff를 예전 control로 오판해 drop/paste 순서가 뒤집힐 수 있으므로, drop 시에는 `reason_code`, `expected_control_seq`, `active_control_seq`, `expected_prompt_path`, `active_prompt_path`, `notify_kind`를 함께 남겨 seq drift와 file drift를 분리 관측하는 편이 맞습니다.
- lane readiness의 busy 판정은 pane 전체 scrollback이 아니라 최근 visible tail 기준으로 보는 편이 맞습니다. 예전 `Working (...)` 줄이 위에 남아 있다는 이유만으로 현재 prompt-visible owner pane을 계속 busy로 취급하면 안 됩니다.
- stale control slot을 수동 정리해야 할 때는 `.pipeline/archive-stale-control-slots.sh`를 쓰고, active `CONTROL_SEQ`/status 기준 control file은 archive하지 않는 편이 맞습니다.
- shared `.pipeline/state/`에는 `turn_state.json`, `autonomy_state.json`, 그리고 blocker resolution에 아직 필요한 `VERIFY_DONE` 기록만 오래 남길 수 있습니다. 이전 run의 `VERIFY_PENDING` / `VERIFY_RUNNING` 같은 non-terminal job state는 watcher startup에서 `.pipeline/runs/<old_run_id>/state-archive/` 또는 `.pipeline/state-archive/legacy/`로 옮겨 현재 run surface와 섞이지 않게 하는 편이 맞습니다.
- JobState JSON의 **primary 경로는 `.pipeline/state/jobs/<job_id>.json`**이고, 공용 상태 파일(`turn_state.json`, `autonomy_state.json`)은 `.pipeline/state/` 루트에 남습니다. owner boundary는 name filter가 아니라 디렉터리 path 자체로 강제되며, 새 JobState 쓰기는 항상 `jobs/` 하위로 들어갑니다. migration 기간 동안 `.pipeline/state/<job_id>.json` 루트 fallback은 **읽기 전용**으로만 허용되며, 같은 `job_id`가 양쪽에 있으면 primary가 항상 우선입니다. 자동 이동(auto-move)은 이번 라운드 범위 밖이며, 추후 마이그레이션 라운드에서 replay/복구 테스트와 함께 별도로 다룹니다.
- state-dir scan 소유권은 `pipeline_runtime/schema.py`의 `jobs_state_dir(...)` / `iter_job_state_paths(...)` / `load_job_states(...)` helper가 가집니다. watcher_core의 `_archive_stale_job_states`, `_verified_work_paths`, `_get_current_run_jobs`와 supervisor의 job state loading은 모두 이 helper를 통해서만 접근하며, 각 파일 안의 직접 `state_dir.glob("*.json")` 조립은 제거됐습니다. `STATE_DIR_SHARED_FILES` name filter는 이제 primary 경로가 아니라 루트 fallback 해석에만 좁게 남아 있습니다.
- watcher startup이 current run의 `VERIFY_PENDING` job을 state에서 복원했다면, 최신 `/work` candidate 스캔 결과와 무관하게 그 pending round를 먼저 다시 step해 verify/handoff owner lane으로 재개하는 편이 맞습니다. 다만 이 replay는 current control-resolution turn(`VERIFY_FOLLOWUP`, `ADVISORY_ACTIVE`, gated operator retriage)이나 열린 advisory arbitration이 없을 때만 허용합니다. 그렇지 않으면 older pending round가 현재 follow-up/advisory pane truth를 덮는 false restart가 됩니다.
- 단, current-run `VERIFY_PENDING` job의 artifact가 이미 matching `/verify` note로 닫힌 상태라면 replay하지 않고 같은 run의 `state-archive/`로 옮깁니다. 이렇게 해야 예전 pending job이 최신 unverified `/work` scan을 계속 가로막지 않고, manifest 없는 가짜 `VERIFY_DONE` surface도 만들지 않습니다.
- supervisor-managed runtime에서는 watcher job state도 supervisor가 만든 current `run_id`를 그대로 써야 합니다. watcher가 자기 PID 기반 별도 `run_id`를 만들면 verify/implement owner job state가 current run status surface에서 빠져 stale `READY`/`prompt_visible`처럼 보일 수 있습니다.
- 반대로 supervisor가 재시작될 때 watcher가 살아 있다면, supervisor는 `.pipeline/current_run.json`의 기존 `run_id`를 그대로 이어받는 편이 맞습니다. 그래야 canonical `runs/<run_id>/status.json`이 watcher가 이미 startup-replay한 current-run `VERIFY_PENDING` / `VERIFYING` job state와 같은 라인을 계속 비추고, 새 supervisor가 별도 run dir로 옮겨가 이전 status.json이 stale `STOPPED`로 굳는 일이 생기지 않습니다.
- 다만 inheritance는 stale pointer가 다른 live watcher와 섞이지 않도록 좁게 게이트해야 맞습니다. `current_run.json`은 supervisor가 매번 갱신할 때 현재 살아 있는 `experimental.pid`를 `watcher_pid` 필드로 같이 기록하고, supervisor restart의 `_inherited_run_id_from_live_watcher()`는 그 pointer `watcher_pid`가 현재 live `experimental.pid`와 정확히 같을 때만 기존 `run_id`를 이어받습니다. owner 필드가 없거나 mismatched이거나 pid가 죽었으면 fresh `_make_run_id()`가 그대로 이깁니다.
- 추가로 pid가 매우 짧은 시간 안에 재사용되는 극단 케이스까지 막기 위해, `current_run.json`은 같은 갱신에서 watcher process 의 `/proc/<pid>/stat` starttime을 `watcher_fingerprint` 필드로 같이 기록하고, inheritance는 pointer `watcher_fingerprint`가 현재 live watcher 의 fingerprint와 정확히 같을 때만 허용합니다. fingerprint 필드가 없거나 mismatched이거나 `/proc`에서 읽을 수 없으면 여전히 fresh `_make_run_id()`가 이깁니다.
- 이 owner contract는 supervisor와 watcher exporter가 같은 pointer boundary를 공유해야 성립합니다. watcher exporter(`watcher_core._write_current_run_pointer`)도 `current_run.json`을 갱신할 때 자신의 `os.getpid()`를 `watcher_pid`로, 같은 process의 `/proc/<pid>/stat` starttime을 `watcher_fingerprint`로 함께 기록해 supervisor restart inheritance 조건을 깨뜨리지 않습니다. fingerprint 계산은 `pipeline_runtime/schema.process_starttime_fingerprint` 한 helper로 모아서 두 writer가 owner-match 정의를 공유합니다.
- `process_starttime_fingerprint`는 `/proc/<pid>/stat`을 읽지 못하는 환경에서는 POSIX `ps -p <pid> -o lstart=` 출력을 보조 fingerprint로 씁니다. 그 두 source도 모두 비어 있으면 `os.stat(f"/proc/{pid}")`의 `st_ctime_ns`를 좁은 third fallback으로 직렬화해 씁니다. 이 third fallback은 `/proc/<pid>/stat` 파싱/읽기가 실패하고 `ps -p <pid> -o lstart=`가 사용 가능한 fingerprint를 내지 못하지만 `/proc/<pid>` 자체는 여전히 stat 가능한 경우에만 도움이 되며, `/proc` 자체가 마운트되지 않은 호스트의 portability를 넓혀 주지는 않습니다. 세 source가 모두 비어 있을 때에만 빈 문자열을 돌려서 inheritance가 fresh `_make_run_id()`로 fall through 하므로, fallback은 inheritance 능력을 넓히되 잘못된 inherit를 절대 만들지 않습니다.
- lane `READY/WORKING` 표시는 wrapper event를 primary truth로 쓰되, attachable lane의 pane tail 하단 prompt/activity marker는 stale surface 보정에만 좁게 쓰는 편이 맞습니다. 특히 current `accepted_task`가 살아 있는 lane은 matching `TASK_DONE`/BROKEN/inactive 전이 전까지 `READY`로 내려가면 안 되고, tail prompt는 state override가 아니라 note/drift evidence만 보정해야 합니다.
- `RECEIPT_PENDING` round가 남아 있어도 current turn이 더 이상 `VERIFY_ACTIVE`/`VERIFY_FOLLOWUP`가 아니면 launcher/runtime이 이를 곧바로 fixed verify lane current truth로 끌어올리지는 않는 편이 맞습니다. receipt close 대기는 `active_round.completion_stage`와 lane note로 보이게 하고, active lane 우선순위는 current turn/control에 먼저 맞춥니다.
- launcher snapshot은 thin client 그대로 `active_round.state`, `dispatch_id`, `completion_stage`, `Receipt: pending close`를 같이 보여서, verify lane이 task는 끝냈지만 receipt close를 기다리는 상태를 “멈춤”이 아니라 current runtime truth로 읽을 수 있어야 합니다.
- runtime이 아직 살아 있는 `STOPPING`/`BROKEN` 전이 중에는 `RECEIPT_PENDING` round를 lane note/active_round로 잠깐 surface할 수 있지만, supervisor가 final `STOPPED` snapshot을 flush할 때는 `control=none`, `active_round=null`, idle turn snapshot으로 정리하는 편이 맞습니다. stopped 상태에서 이전 implement/verify/receipt task가 여전히 진행 중인 것처럼 보이면 안 됩니다.
- metadata-only `/work` closeout(`## 변경 파일 - 없음` 또는 work/verify/.pipeline 경로만 기록)도 latest canonical round note라면 watcher의 implement-owner round-completion 감지에는 포함하는 편이 맞습니다. watcher는 이런 closeout으로 `IMPLEMENT_ACTIVE`를 풀고 verify artifact 후보로 넘길 수 있어야 하며, 단지 dispatch prompt content를 좁히기 위해서만 metadata-only filtering을 유지합니다.
- latest `/work` verify 필요 판정과 receipt close용 verify artifact 선택은 generic latest same-day `/verify` mtime 하나만으로 닫지 않는 편이 맞습니다. supervisor는 current run `VERIFY_DONE` job의 verify manifest `feedback_path`가 있으면 그 current-round verify artifact를 먼저 쓰고, 그 증거가 없을 때만 verify note 안의 `work/...md` 참조로 fallback하는 편이 맞습니다. `verify/<month>/<day>/` day-folder 바로 아래 note도 canonical same-day verify로 인정해야 하며, same-day fallback은 유지하되 verify root 다른 날짜 폴더에 있더라도 note 본문이 해당 `work/...md`를 직접 참조하면 matching verify로 인정해야 합니다. unrelated newer `/verify`가 있어도 latest `/work` 자체가 아직 매칭 verify 없이 남아 있으면 verify/handoff-owner verification을 계속 우선해야 하고, receipt/`artifacts.latest_verify`도 그런 unrelated note를 current truth처럼 가리키면 안 됩니다. `REASON_CODE: newer_unverified_work_present` + `OPERATOR_POLICY: stop_until_truth_sync`도 이런 recovery family로 보고 즉시 operator stop이 아니라 verify/handoff-owner verification 우선 경계로 다루는 편이 맞습니다.

## handoff 작성 원칙

- `.pipeline/implement_handoff.md`는 단순히 "다음으로 비어 있는 내부 regression"을 채우는 문서가 아닙니다.
- `.pipeline/implement_handoff.md`는 최신 implement-owner round를 검수한 결과를 다음 implement-owner 라운드에 넘기는 **실행 슬롯**입니다.
- `.pipeline/advisory_request.md`는 active verify/handoff owner가 실제로 exact slice를 못 좁혔을 때만 쓰는 **arbitration 요청 슬롯**입니다.
- `.pipeline/advisory_advice.md`는 active advisory owner가 active verify/handoff owner에게 recommendation을 남기는 **advisory 슬롯**입니다.
- `.pipeline/operator_request.md`는 active verify/handoff owner가 실제로 operator 판단이 필요할 때만 쓰는 **정지 슬롯**입니다.
- `.pipeline/session_arbitration_draft.md`는 watcher가 active session의 context exhaustion / session rollover / continue-vs-switch를 감지했고 verify/advisory lanes가 idle이며 implement owner가 idle이거나 같은 escalation text에 짧게 안정됐을 때만 남기는 **draft 슬롯**이며, canonical stop/go 신호가 아닙니다.
- 이 draft는 implement-owner activity resume, canonical advisory/operator slot open, signal cleared 같은 resolved 조건이 생기면 watcher가 다시 정리할 수 있고, 같은 fingerprint는 짧은 cooldown 동안 곧바로 재생성하지 않는 편이 맞습니다.
- 실행 슬롯, advisory arbitration 슬롯, 정지 슬롯을 implement owner가 같이 읽지 않도록 분리하는 것이 stage-3 구조의 핵심입니다.
- `.pipeline/implement_handoff.md`는 현재 MVP 우선순위에 맞는 다음 implement-owner 라운드 한 슬라이스만 남겨야 합니다.
- `.pipeline/implement_handoff.md`의 `READ_FIRST`는 implement owner 기준 root memory file 1개만 적는 편이 맞습니다. 즉 Claude면 `CLAUDE.md`, Codex면 `AGENTS.md`, Gemini면 `GEMINI.md`가 들어가야 하고, verify/advisory owner 쪽 다른 root doc는 같이 적지 않는 편이 맞습니다. 그 뒤에 이 슬라이스에 실제로 필요한 source path만 최소로 붙입니다.
- verify owner와 advisory owner도 같은 규칙을 따르는 편이 맞습니다. `/verify`, `.pipeline/advisory_request.md`, `.pipeline/advisory_advice.md`, verify-owned recovery/follow-up prompt의 `READ_FIRST` 역시 active owner 기준 root memory file 1개만 적고, 다른 role의 root doc는 섞지 않는 편이 맞습니다.
- context 최적화 관점에서는 `READ_FIRST`에 `work/README.md`, `verify/README.md`, `.pipeline/README.md` 같은 static guide를 매 라운드 기본값으로 반복해서 넣지 않는 편이 맞습니다. 기본값은 active owner root doc 1개 + 현재 control/work/verify처럼 이번 round에 실제로 필요한 live path만 두고, generic guide는 root doc나 named source path가 부족할 때만 추가하는 편이 맞습니다.
- 특히 advisory arbitration이 exact shipped docs path나 current runtime-doc family를 이미 지목한 경우에는 그 named path들을 먼저 읽고 범위를 유지하는 편이 맞습니다. `docs/superpowers/**`, `plandoc/**`, 기타 historical planning docs는 request/latest `/work`/latest `/verify`가 현재 근거로 명시할 때만 advisory scope에 포함하는 편이 맞습니다.
- active implement-owner session 중 context exhaustion, session rollover, continue-vs-switch 같은 live side question이 생기면, active verify/handoff owner는 `.pipeline/advisory_request.md` / `.pipeline/advisory_advice.md`를 coordination에만 쓰고 답은 implement owner에게 짧은 lane reply로 relay합니다. 이 경우 `.pipeline/implement_handoff.md`는 session boundary 전까지 그대로 둡니다.
- `.pipeline/implement_handoff.md`는 `STATUS: implement`와 `CONTROL_SEQ`를 함께 사용합니다.
- `.pipeline/advisory_request.md`는 `STATUS: request_open`와 `CONTROL_SEQ`를 함께 사용합니다.
- `.pipeline/advisory_advice.md`는 `STATUS: advice_ready`와 `CONTROL_SEQ`를 함께 사용합니다.
- `.pipeline/operator_request.md`는 `STATUS: needs_operator`와 `CONTROL_SEQ`를 함께 사용합니다.
- 더 높은 `CONTROL_SEQ`의 real operator boundary가 active current truth가 되면 watcher는 더 낮은 `CONTROL_SEQ`의 `.pipeline/advisory_request.md` / `.pipeline/advisory_advice.md`를 삭제하거나 archive하지 않고 `STATUS: superseded`로 중립화합니다. 이때 `SUPERSEDED_BY`, `SUPERSEDED_BY_SEQ`, `SUPERSEDED_REASON` header와 `advisory_slot_superseded` runtime event를 남겨 이전 advisory가 왜 더 이상 pending dispatch가 아닌지 audit할 수 있게 합니다.
- `.pipeline/session_arbitration_draft.md`는 `STATUS: draft_only`만 사용합니다.
- `STATUS: implement_blocked`는 rolling control file status가 아니라, active implement-owner pane에서만 watcher가 읽는 machine-readable blocked sentinel입니다.
- `STATUS: implement`이면 active verify/handoff owner가 다음 단일 슬라이스를 이미 확정한 상태입니다. active implement owner는 그 한 슬라이스만 구현합니다.
- active implement owner가 그 슬라이스를 실행할 수 없으면 operator 선택지를 직접 열지 않고 `STATUS: implement_blocked` + `BLOCK_REASON` + `BLOCK_REASON_CODE` + `REQUEST: verify_triage` + `ESCALATION_CLASS: verify_triage` + `HANDOFF` + `HANDOFF_SHA` + `BLOCK_ID`를 pane에 남기고 멈추는 편이 맞습니다.
- `codex_triage`, `codex_triage_only`, `codex_followup`는 과거 Codex-bound verify lane 호환 alias로만 읽습니다. 새 prompt, route, status, event payload는 role-bound canonical 값인 `verify_triage`, `verify_triage_only`, `verify_followup`을 씁니다.
- runtime/script smoke가 `implement_blocked` sentinel을 만들 때도 자유문장 출력 대신 `pipeline_runtime.control_writers.render_implement_blocked(...)`로 구조화 필드를 같이 렌더링하는 편이 맞습니다.
- `STATUS: request_open`이면 active verify/handoff owner가 advisory arbitration을 먼저 요청한 상태입니다. watcher는 advisory owner를 먼저 부릅니다.
- `STATUS: advice_ready`이면 active advisory owner가 recommendation을 남긴 상태입니다. watcher는 verify/handoff-owner follow-up을 먼저 부릅니다.
- `STATUS: request_open`이 오래 닫히지 않고 같은 `CONTROL_SEQ`의 current `advisory_advice.md`가 없으면 watcher는 operator stop을 열지 않고 `advisory_recovery` event를 남긴 뒤 verify/handoff owner에게 recovery prompt를 보낼 수 있습니다. 이 prompt는 `.pipeline/advisory_advice.md`를 대필하지 않고, 기존 request/work/verify를 읽어 더 높은 `CONTROL_SEQ`의 `.pipeline/implement_handoff.md`, 더 좁은 `.pipeline/advisory_request.md`, 또는 실제 operator boundary인 `.pipeline/operator_request.md` 중 하나만 쓰게 합니다.
- `STATUS: needs_operator` file이 생겼다고 해서 곧바로 current truth operator stop이 되는 것은 아닙니다. supervisor/watcher는 `safety_stop`, `approval_required`, `truth_sync_required`, publication boundary(`external_publication_boundary` / `publication_boundary` / `pr_boundary` / `pr_merge_gate`)만 즉시 publish하고, 나머지는 최대 24시간 동안 gated candidate로 다룹니다.
- `approval_required`로 적힌 stop이라도 본문이 문자/숫자/한글 라벨 선택지 메뉴(괄호형 inline 라벨 포함)이고 최신 `docs/`, milestone, `/work`, `/verify` 근거로 에이전트가 먼저 좁힐 수 있는 문제라면, runtime은 안전/파괴/auth/truth-sync blocker가 없는 한 `slice_ambiguity` 성격의 verify/handoff follow-up으로 낮춰 advisory-first 흐름을 태우는 편이 맞습니다. 실제 blocker 판정은 `DECISION_REQUIRED` 같은 결정 헤더를 우선하고, 본문 설명에 등장한 blocker marker만으로 stop을 확정하지 않는 편이 맞습니다.
- watcher가 `routed_to=verify_followup` gated operator retriage를 verify/handoff owner에게 이미 보냈고, verify lane이 다시 prompt-ready idle이 됐는데도 더 높은 `CONTROL_SEQ`의 `implement_handoff.md`, `advisory_request.md`, `operator_request.md`가 생기지 않았다면, 같은 stop에 재고정하지 않고 `operator_retriage_no_next_control` incident를 남긴 뒤 `.pipeline/advisory_request.md`를 다음 `CONTROL_SEQ`로 machine-write해 advisory-first arbitration으로 승격할 수 있습니다. `approval_required` / `safety_stop` / `truth_sync_required` / 아직 merged로 확인되지 않은 `pr_merge_gate`처럼 실제 승인·안전·publication 경계가 남은 stop은 이 승격 대상이 아니라 즉시 operator wait current truth로 남습니다.
- 같은 의미의 `.pipeline/operator_request.md`를 규칙 준수를 위해 더 높은 `CONTROL_SEQ`로 다시 쓴 경우에는 `STATUS`, `CONTROL_SEQ`, `SOURCE`, `SUPERSEDES`, timestamp류 header를 semantic fingerprint에서 제외합니다. 이 seq-only/mtime-only bump는 24시간 suppress window나 `operator_retriage_no_next_control` age를 새로 시작하지 않고, 기존 retriage window를 이어갑니다.
- supervisor/watcher는 operator stop publish/gate를 `OPERATOR_POLICY` 우선, `REASON_CODE` 다음, 설명 prose 마지막 참고 순서로 판정합니다. 구조화 metadata가 없거나 알 수 없으면 fail-safe로 즉시 publish하는 편이 맞습니다.
- runtime은 오래 남은 control slot compatibility를 위해 `OPERATOR_POLICY: stop_until_exact_slice_selected`를 `gate_24h`로, `REASON_CODE: gemini_axis_switch_without_exact_slice`를 `slice_ambiguity`로 정규화해 false immediate publish를 막습니다. 새 slot은 canonical 값(`gate_24h`, `slice_ambiguity`)을 그대로 쓰는 편이 맞습니다.
- `BASED_ON_WORK`가 이미 `VERIFY_DONE`라고 해서 모든 `needs_operator`를 stale stop으로 되돌리면 안 됩니다. `verified_blockers_resolved` self-heal은 명시적인 `truth_sync_required`처럼 "해당 work note verification이 blocker를 직접 닫는" family에만 적용하고, `slice_ambiguity`나 다른 next-slice/operator-selection stop은 같은 `BASED_ON_WORK`를 갖더라도 gate/publish 계약을 그대로 유지하는 편이 맞습니다.
- launcher와 runtime soak/smoke gate도 operator candidate status에서 `classification_source`가 `operator_policy` 또는 `reason_code`가 아니면 `classification_fallback_detected`로 즉시 실패시키는 편이 맞습니다. 즉 fallback metadata는 화면 경고가 아니라 운영 게이트 실패로 다룹니다.
- gate 중인 후보는 runtime `status.control=none`으로 내려가고, 대신 `status.autonomy.mode = recovery|triage|hibernate`와 `block_reason`, `suppress_operator_until`, `operator_eligible`로 surface됩니다. 오래된 상태 파일에서는 `pending_operator`가 보일 수 있지만, 현재 계약에서 `approval_required` / `safety_stop` / `truth_sync_required` / publication boundary(`external_publication_boundary` / `publication_boundary` / `pr_boundary` / `pr_merge_gate`) 같은 real-risk stop은 gate 뒤에 숨기지 않고 `needs_operator` current truth로 publish합니다. 이미 merged로 확인된 `pr_merge_gate`는 `pr_merge_completed` recovery로 내려가며, 확인에 실패하면 fail-closed로 기존 operator wait를 유지합니다.
- 예외적으로 `approval_required` commit/push stop은 operator-approved commit/push가 이미 끝났음을 watcher가 read-only git evidence로 증명할 수 있으면 `operator_approval_completed` recovery로 내려갑니다. upstream이 없거나 HEAD가 upstream에 포함되지 않거나 rolling `.pipeline` artifact 외 dirty source가 있으면 fail-closed로 기존 `needs_operator` current truth를 유지합니다.
- 다만 `OPERATOR_POLICY: internal_only` + `DECISION_CLASS: next_slice_selection` + `REASON_CODE: waiting_next_control` 조합, 또는 이미 승인된 큰 publish 묶음을 나타내는 `REASON_CODE: commit_push_bundle_authorization` 조합은 unattended idle로 눕히기보다 verify/handoff-owner follow-up으로 다시 보내는 편이 맞습니다. 이 경우 runtime `autonomy.mode`는 `triage`, gate route는 `verify_followup`으로 남기고, genuine `idle_hibernate` (`DECISION_CLASS: internal_only`)만 `hibernate`를 유지합니다.
- gate window는 next-slice ambiguity, session/context follow-up, recovery 후보처럼 에이전트가 먼저 좁힐 수 있는 non-real-risk stop에만 적용됩니다. active implement owner는 current truth가 아닌 gated stop 슬롯을 직접 따르지 않습니다.
- runtime long soak는 baseline evidence로 유지하되, 기본 검증 메뉴는 아닙니다. 1차 자동화 milestone은 `scripts/pipeline_runtime_gate.py synthetic-soak --duration-sec 21600 --sample-interval-sec 10 --min-receipts 10`로 만든 6h synthetic soak report(`report/pipeline_runtime/verification/<date>-6h-synthetic-soak.md` + JSON sidecar) 통과이고, 이후 adoption gate에서 24h soak로 올리는 편이 맞습니다. 현재 기본 검증은 launcher live stability gate, incident replay, 실제 작업 세션이며, 6h/24h long soak는 supervisor/watcher/tmux adapter/wrapper event 계약 대변경, control/receipt/state writer 계약 변경, adoption 직전 최종 gate 같은 예외 상황에서만 다시 실행하는 편이 맞습니다.
- 현재 launcher live stability gate는 `handoff_dispatch -> TASK_ACCEPTED -> TASK_DONE -> receipt_close` chain continuity, READY/WORKING 오표시 0회, 불필요한 `needs_operator` 0회, `classification_fallback_detected` 0회, stop/restart 후 stale `RUNNING/STOPPING` 0회, orphan watcher/session 0회, dispatch/completion/receipt close incident의 named event surface, 반복 incident의 replay 고정 여부를 기준으로 봅니다.
- 자동화 완성 목표는 ordinary next-step, ambiguity, stall, rollover, recovery 문제로 사용자를 호출하지 않는 것입니다. 에이전트들은 `/work`, `/verify`, current docs, runtime evidence를 기준으로 먼저 회의/중재하고 하나의 다음 control로 좁혀야 합니다.
- 재귀학습과 진화적 탐색은 현재 단계에서 repo-local operational learning입니다. 같은 문제는 named incident, replay test, owning boundary, shared helper, runtime surface로 남기고, 후보 탐색은 current evidence와 milestone에 묶인 bounded comparison으로 닫습니다.
- runtime logic은 current branch, commit SHA, `CONTROL_SEQ`, pane id, Korean label, exact operator prose, one-off control body를 하드코딩하지 않습니다. shared parser/schema/status-label/helper와 fixture가 source of truth입니다.
- watcher/supervisor/launcher/controller가 같은 truth를 near-copy로 재해석하지 않습니다. 같은 판정이 두 계층에 필요하면 owning boundary나 `pipeline_runtime/*` helper로 올리고 thin client는 surface만 읽습니다.
- watcher_core나 supervisor 같은 큰 파일에 새 예외 branch를 계속 쌓아 유지보수성을 낮추지 않습니다. parsing, labeling, control writing, lane surface, event contract 책임은 커지면 명확한 helper/owner로 추출합니다.
- `STATUS: needs_operator`는 bare stop line만 남기는 용도가 아닙니다. 이 상태를 쓸 때는 최소한 아래를 같이 적는 편이 canonical입니다.
  - stop reason
  - 근거가 된 latest `/work`와 latest `/verify`
  - operator가 다음에 무엇을 정해야 하는지
- 오래된 stale `operator_request.md`나 obsolete draft를 치우고 싶다면, 본문만 덮어쓰거나 삭제하기보다 `.pipeline/archive-stale-control-slots.sh`로 archive하는 편이 안전합니다.
- stop/go 판단은 최신 valid control 파일의 `STATUS`와 `CONTROL_SEQ`가 담당합니다. watcher/launcher는 `CONTROL_SEQ` 우선, `mtime` 보조로 active control을 고르고 stale older control file은 dispatch 판단에서 제외합니다. 멈추고 싶다면 본문 설명만 고치는 대신 stop 슬롯을 더 높은 `CONTROL_SEQ`로 갱신해야 합니다.
- latest `/work`와 `/verify`가 한 family를 truthfully 닫았고 그 family 안에 더 작은 후속 risk가 남아 있다면, active verify/handoff owner는 보통 `needs_operator`보다 그 same-family current-risk reduction을 먼저 자동 확정하는 편이 맞습니다.
- 기본 자동 tie-break 순서는 아래와 같습니다.
  - same-family current-risk reduction
  - same-family user-visible improvement
  - new quality axis
  - internal cleanup
- 위 순서로도 truthful한 단일 슬라이스를 못 고를 때만 `STATUS: needs_operator`를 씁니다.
- 다음 슬라이스는 아래 중 하나를 직접 개선해야 합니다.
  - user-visible document workflow
  - current reviewed-memory user-visible clarity
  - approval, evidence, summary, search quality
  - current shipped flow risk reduction
- route-by-route handler completeness, contract-family completeness, internal helper completeness는 기본 handoff 우선순위가 아닙니다.
- stale handoff를 줄이기 위해 현재 `/work`와 `/verify`의 최신 truth를 먼저 확인하고, 그 범위 안에서만 handoff를 작성합니다.
- Playwright-only smoke tightening, selector drift, single-scenario fixture update handoff는 기본적으로 isolated browser rerun을 요구하는 편이 맞습니다. shared browser helper 변경, 여러 browser scenario 변경, release/ready 판단, isolated rerun의 broader drift 신호가 없는데도 `make e2e-test`를 기본처럼 요구하는 stale handoff는 피합니다.
- latest `/work`의 `## 변경 파일`이 markdown-only docs sync로 보이면, watcher의 verify/handoff-owner prompt는 docs-only fast path를 붙입니다. 이 경우 active verify/handoff owner는 우선 `git diff --check`와 직접 docs/code truth-sync를 먼저 확인하고, `/work`가 실제로 code/test/runtime 변경을 주장하지 않는 한 broader unit/Playwright rerun으로 자동 확장하지 않는 편이 맞습니다.
- 다만 같은 날 same-family docs-only truth-sync가 이미 3회 이상 반복됐다면, active verify/handoff owner는 또 하나의 더 작은 docs-only micro-slice를 `.pipeline/implement_handoff.md`에 쓰지 않는 편이 맞습니다. 이 경우 남은 docs drift를 한 번에 닫는 bounded bundle로 묶거나, truthful한 단일 bundle을 못 고르면 `.pipeline/advisory_request.md` 또는 `.pipeline/operator_request.md`로 전환합니다.
- whole-project trajectory review나 milestone audit은 `.pipeline` handoff가 아니라 `report/`에서 별도로 다룹니다.

## 권장 흐름

1. active implement owner가 구현 후 최신 `/work` closeout을 남깁니다.
2. active verify/handoff owner가 최신 `/work`와 그 work에 매칭되는 `/verify`(same-day fallback 또는 explicit work reference가 있는 cross-day note)를 읽고 실제 검증을 재실행합니다.
3. active verify/handoff owner가 `/verify` note를 남기거나 갱신합니다.
4. active verify/handoff owner가 구현 가능한 경우 `.pipeline/implement_handoff.md`에 `STATUS: implement`를 씁니다.
5. active verify/handoff owner가 exact slice를 못 좁히면 `.pipeline/advisory_request.md`에 `STATUS: request_open`을 씁니다.
6. advisory owner가 `report/gemini/...md`와 `.pipeline/advisory_advice.md`에 `STATUS: advice_ready`를 남깁니다.
7. active verify/handoff owner가 advisory recommendation을 읽고 최종 `.pipeline/implement_handoff.md` 또는 `.pipeline/operator_request.md`를 씁니다.
7-0. 예외적으로 active implement-owner lane이 막히면, implement owner는 pane-local `implement_blocked` sentinel만 남기고 watcher가 verify/handoff-owner blocked triage를 자동 dispatch합니다.
7-1. 예외적으로 active implement-owner session의 side-question arbitration이면, active verify/handoff owner는 advisory advice를 implement owner에게 짧은 lane reply로만 relay하고 `.pipeline/implement_handoff.md`는 덮어쓰지 않습니다. handoff 갱신은 session boundary 또는 다음 라운드 시작 시점으로 미룹니다.
7-2. watcher는 이런 active-session side-question을 감지해도 `.pipeline/advisory_request.md`를 자동으로 열지 않습니다. 필요하면 verify/advisory lanes가 idle이고 implement owner가 idle이거나 짧게 settle된 상태일 때 `.pipeline/session_arbitration_draft.md`만 생성하고, active verify/handoff owner가 직접 canonical 슬롯 승격 여부를 정합니다.
7-3. watcher가 생성한 `.pipeline/session_arbitration_draft.md`는 perpetual slot이 아닙니다. implement owner가 다시 작업을 시작하거나 canonical advisory/operator 슬롯이 열리면 watcher가 정리하고, 같은 fingerprint는 짧은 cooldown 동안 반복 생성하지 않는 편이 맞습니다.
8. `.pipeline/codex_feedback.md`는 필요하면 scratch로 남길 수 있지만, watcher는 그것을 stop/go 실행 신호로 읽지 않습니다.
9. watcher 또는 자동화는 최신 valid control 기준으로 `.pipeline/implement_handoff.md`의 `STATUS: implement`일 때만 implement owner에 전달하고, `.pipeline/advisory_request.md`가 최신이면 advisory owner를, `.pipeline/advisory_advice.md`가 최신이면 verify/handoff-owner follow-up을 실행합니다. `.pipeline/operator_request.md`는 latest slot이어도 gate 대상이면 바로 operator로 서지 않고, immediate publish 사유, publication boundary(`pr_merge_gate` 포함), 또는 24시간 gate가 지난 뒤에만 operator wait current truth가 됩니다.
10. watcher의 책임은 파일 변경 감지와 올바른 pane 전달까지입니다. 전송 후 implement/verify/advisory owner pane이 바쁘거나 interrupted 상태여서 처리가 안 되는 경우는 watcher contract 문제가 아니라 세션 상태 문제입니다.
11. active verify/handoff owner가 다음 슬라이스를 고를 때는, 같은 family 안의 작은 current-risk reduction을 먼저 닫고 그다음 새 quality axis로 넘어가는 편이 기본값입니다.
12. startup dispatch는 pane이 실제로 입력을 받을 준비가 됐는지 먼저 확인한 뒤 보내는 편이 맞습니다. 그 뒤에는 짧은 readiness 확인과 watcher retry에 맡기는 쪽이 기본값입니다.
13. startup 또는 rolling dispatch에서 최신 canonical `/work`가 아직 matching `/verify` 없이 남아 있으면, unrelated same-day `/verify`가 더 늦게 찍혀 있어도 fresher `implement_handoff.md`보다 verify/handoff-owner verification이 우선입니다.
14. launcher가 `tmux attach`에서 빠져나와도 자동 진행이 이어져야 하므로, watcher는 launcher shell background보다 tmux session 내부의 별도 hidden watcher window에서 유지하는 편이 더 안전합니다.
15. active implement-owner round가 이미 진행 중이면, newer `implement_handoff.md`가 생겨도 watcher는 busy pane으로 mid-round re-dispatch하지 않고 현재 라운드 exit 뒤에 반영합니다. 예외적으로 더 높은 `CONTROL_SEQ`가 active이고 implement pane이 prompt-ready idle이면, watcher는 `implement_handoff_idle_release`로 stale seq를 풀고 최신 handoff를 다시 보낼 수 있습니다.

## 추가 실행 규칙

- implement-owner round는 bounded file edits와 canonical `/work` closeout에서 끝납니다. implement lane에서 commit, push, branch publish, PR 생성까지 같이 진행하지 않는 편이 맞습니다.
- commit/push/PR creation automation은 큰 검증 묶음 경계에서만 다룹니다. operator가 명시 승인한 release, soak, PR stabilization, direct publish bundle이 아니면 small/local slice는 `/work` closeout과 local dirty state로 남기고 commit/push/PR operator stop을 새로 열지 않습니다.
- verify/handoff-owner round는 pane-only reasoning이나 next control slot rewrite만으로 닫히지 않습니다. dispatch 이후 current-round `/verify` receipt가 실제로 갱신된 것이 확인된 뒤에만 `.pipeline/implement_handoff.md`, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`를 쓰는 편이 맞습니다.
- Gemini advisory round도 pane-only answer로 닫지 않습니다. `report/gemini/...md` advisory log와 `.pipeline/advisory_advice.md` recommendation slot이 둘 다 있어야 round가 완료된 것으로 봅니다.

## stale control slot archive helper

- helper: `.pipeline/archive-stale-control-slots.sh`
- 기본 원칙:
  - `pipeline_runtime.schema.parse_control_slots(...)` 기준 active control file은 archive하지 않음
  - valid active control을 해석할 수 없을 때만 newest existing file을 보수적 fallback으로 보존
  - known control-slot basename만 받음
  - 결과는 `.pipeline/archive/YYYY-MM-DD/` 아래로 이동
  - 실제 archive 시 repo-relative source/target, file hash, archived slot header, pre/post active control을 `.pipeline/archive/YYYY-MM-DD/archive-manifest.jsonl`에 append
  - `PIPELINE_ARCHIVE_DRY_RUN=1`이면 미리보기만 수행
- 예시:
  - `bash .pipeline/archive-stale-control-slots.sh --all-stale`
  - `bash .pipeline/archive-stale-control-slots.sh operator_request.md session_arbitration_draft.md`

## 최소 `needs_operator` 예시

```md
STATUS: needs_operator
CONTROL_SEQ: 184
REASON_CODE: approval_required
OPERATOR_POLICY: immediate_publish
DECISION_CLASS: operator_only
DECISION_REQUIRED: approve runtime auth refresh
BASED_ON_WORK: work/<month>/<day>/<latest-work>.md
BASED_ON_VERIFY: verify/<month>/<day>/<latest-verify>.md

이유:
- latest `/work`와 `/verify` 기준으로 다음 단일 슬라이스를 아직 truthful하게 확정하지 못했습니다.

operator 확인 필요:
- 다음 단일 user-visible slice 또는 current-risk reduction slice 1개 확정
- 확정 후 `STATUS: implement`로 갱신
```

## tmux 레인 예시

- pane 1: Codex CLI - implement owner lane
- pane 2: Claude Code - verify/handoff owner lane
- pane 3: Gemini CLI - advisory owner lane

## 3-agent smoke helper

- repo-local live arbitration smoke는 `.pipeline/smoke-three-agent-arbitration.sh`로 반복 확인할 수 있습니다.
- repo-local deterministic blocked auto-triage smoke는 `.pipeline/smoke-implement-blocked-auto-triage.sh`로 반복 확인할 수 있습니다.
- blocked auto-triage smoke는 fixed "Claude blocks / Codex triages" harness가 아니라, active `.pipeline/config/agent_profile.json`을 `resolve_project_runtime_adapter(...)`로 읽어 active `implement` / `verify` owner를 먼저 해석한 뒤 각 shim을 physical Claude/Codex pane에 role-bound로 배치합니다.
- 이 smoke는 physical lane 이름(`Claude`, `Codex`)은 유지하지만, 어느 pane이 implement shim을 받고 어느 pane이 verify-triage shim을 받는지는 active role binding을 따릅니다.
- deterministic blocked sentinel이 visible tmux tail에서 잘리지 않도록, idle Gemini pane은 implement pane이 아니라 verify pane 쪽을 줄이는 배치로 띄워 implement shim이 더 큰 viewport를 유지합니다.
- active profile이 깨져 있거나, implement/verify owner가 비어 있거나, 동일 owner이거나, 둘 중 하나가 `Claude`/`Codex` 밖이면 tmux session을 띄우기 전에 fail-closed로 종료합니다.
- 이 helper는 workspace 안에 `.pipeline/live-arb-smoke-XXXXXX/` 임시 base dir를 만들고:
  - base dir 아래에 smoke-local `.pipeline/config/agent_profile.json`을 써서 watcher/runtime owner resolve를 production active profile과 분리하고
  - `advisory_request.md`를 seed한 뒤
  - smoke-local `work/4/3/...`와 `verify/4/3/...` synthetic note를 같이 만들고
  - physical Claude/Codex/Gemini lane에 실제 각 CLI를 띄우고
  - `watcher_core.py`를 custom `--base-dir` + smoke-local `--repo-root`로 실행합니다.
- topology는 기본값 `PIPELINE_SMOKE_TOPOLOGY=swapped`(`implement=Codex`, `verify=Claude`, `advisory=Gemini`)이며, `legacy` 또는 `active`로 바꿔 같은 helper를 matrix smoke에 재사용할 수 있습니다.
- 필요하면 `PIPELINE_SMOKE_ROLE_BINDINGS_JSON='{\"implement\":\"Claude\",\"verify\":\"Codex\",\"advisory\":\"Gemini\"}'` 같이 explicit override를 줄 수 있습니다.
- 성공 기준:
  - `advisory_advice.md`가 `STATUS: advice_ready`
  - `report/gemini/*.md` advisory log 생성
  - 이후 `implement_handoff.md` 또는 `operator_request.md` 생성
  - 마지막 runtime status가 operator candidate일 경우 `classification_source`가 structured source(`operator_policy|reason_code`)로 검증됨
- 성공 시 기본값으로 smoke tmux session은 정리하고, smoke 산출물 디렉터리는 남겨 둡니다.
- 성공 시 기본값으로 최근 `3`개 smoke 디렉터리만 남기고 더 오래된 `live-arb-smoke-*` 디렉터리는 정리합니다.
- `PIPELINE_SMOKE_KEEP_RECENT=0`이면 자동 정리를 끌 수 있습니다.
- 실패 시 기본값으로 tmux session과 산출물을 남겨 inspection에 씁니다.
- 오래된 smoke 디렉터리만 수동으로 정리하려면 `.pipeline/cleanup-old-smoke-dirs.sh`를 쓸 수 있습니다.
- 기본값은 최근 `3`개 유지이며, `PIPELINE_SMOKE_CLEANUP_DRY_RUN=1`로 삭제 없이 대상만 확인할 수 있습니다.
- 수동 cleanup도 자동 prune과 동일하게 `PIPELINE_SMOKE_KEEP_RECENT=0`이면 fail-safe no-op으로 동작하여 매칭되는 smoke 디렉터리를 전부 지우지 않고 종료합니다.
- 이 경우 `.pipeline/cleanup-old-smoke-dirs.sh`는 `Cleanup disabled: PIPELINE_SMOKE_KEEP_RECENT=0, preserving all matching <pattern> directories.`라는 explicit receipt 한 줄을 stdout에 남겨, helper가 조용히 return한 경우와 disabled 경우를 operator가 바로 구분할 수 있게 합니다.

## smoke 디렉터리 정리 규약

`.pipeline/` 바로 아래의 smoke workspace는 두 종류로 구분합니다.

- **generated-and-prunable**: smoke helper가 `mktemp -d` 로 만든 임시 workspace입니다. `live-arb-smoke-*` 전체와, `smoke-implement-blocked-auto-triage.sh` 가 방금 만든 untracked `live-blocked-smoke-*` 디렉터리가 여기에 해당합니다. auto-prune은 이 범위에만 적용합니다.
- **checked-in-and-protected**: repro용으로 git에 커밋된 `live-blocked-smoke-*` fixture 디렉터리입니다. 이 파일들은 blocked auto-triage 회귀를 재현하기 위한 자산이므로, cleanup 경로는 이를 절대 삭제·archive 하지 않습니다.

이 두 종류를 한 경계에서 다루기 위해 모든 smoke 디렉터리 가지치기는 `.pipeline/smoke-cleanup-lib.sh`의 `prune_smoke_dirs <smoke_root> <pattern> <keep_recent> [protect_tracked] [dry_run]` 하나만 공유해서 씁니다.

`protect_tracked=1`로 호출했는데 `smoke_root`가 git work tree 바깥이라 `git rev-parse --show-toplevel`이 빈 값을 돌려주면, `prune_smoke_dirs`는 enumeration/삭제를 하지 않고 stderr에 `prune_smoke_dirs: protect_tracked=1 requires a git-backed smoke root, got <path>` 진단을 찍은 뒤 non-zero로 return합니다. 이 fail-closed 경계가 있기 때문에 repo 외부에서 실수로 돌린 호출이 조용히 "tracked 파일 조회 불가 → 아무 것도 보호하지 않음"으로 degrade하지 않습니다. 현재 사용 중인 caller는 모두 `.pipeline/` 내부에서만 돌리므로 실제로는 이 fail-closed 경계에 걸리지 않습니다.

각 호출 지점은 아래와 같습니다.

- `.pipeline/smoke-three-agent-arbitration.sh`: `pattern=live-arb-smoke-*`, `protect_tracked=0`. live arbitration smoke는 tracked fixture가 없으므로 기존 동작대로 newest `KEEP_RECENT`만 남기고 나머지는 삭제합니다.
- `.pipeline/smoke-implement-blocked-auto-triage.sh`: `pattern=live-blocked-smoke-*`, `protect_tracked=1`. 삭제 후보마다 `git ls-files --error-unmatch -- <dir>` 로 tracked 파일이 있는지 확인하고, 있으면 `PROTECT` 로 건너뜁니다. 그 결과 checked-in fixture 디렉터리는 자동 정리되지 않고, 이번 smoke run이 방금 만든 untracked workspace만 오래된 순으로 정리됩니다.
- `.pipeline/cleanup-old-smoke-dirs.sh`: 같은 helper를 경유합니다. 기본 pattern은 `live-arb-smoke-*` 이며, 필요하면 `PIPELINE_SMOKE_PATTERN=...` 으로 다른 generated pattern을 지정할 수 있습니다. 이 수동 cleanup 스크립트는 pattern 값과 무관하게 항상 `protect_tracked=1`로 `prune_smoke_dirs`를 호출하므로, `PIPELINE_SMOKE_PATTERN='live-blocked-smoke-*'` 같은 override를 걸어도 tracked fixture 디렉터리는 `PROTECT`로 건너뛰고 generated workspace만 실제로 삭제합니다.

즉 auto-prune 경계는 "generated smoke workspaces only"이고, tracked `.pipeline/live-blocked-smoke-*` fixture는 helper/scripts 쪽에서 관리 대상이 아니라 git 추적 자산으로 유지합니다.
