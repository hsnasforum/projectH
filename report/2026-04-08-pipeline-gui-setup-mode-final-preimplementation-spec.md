# projectH pipeline_gui setup mode 최종 사전구현 사양

**작성일**: 2026-04-08  
**성격**: 구현 직전 최종 사양  
**목적**: `pipeline_gui` setup mode를 구현하기 전에, 화면 위젯, 파생 상태, 이벤트, 버튼 규칙, 파일 I/O, active promotion guard를 하나의 문서로 고정

---

## 1. 이 문서가 닫는 범위

이 문서는 아래를 **최종 사전구현 계약**으로 고정합니다.

1. setup 화면의 정확한 위젯 inventory
2. setup 화면이 사용하는 파생 UI 상태
3. 체크박스 / 드롭다운 / 토글 / preview / apply / result / restart confirmation 이벤트
4. `Save draft`, `Generate preview`, `Apply` 버튼 활성 규칙
5. `.pipeline/config/` 와 `.pipeline/setup/` 파일 I/O 경계
6. active config promotion guard

이 문서는 아직 runtime 구현 그 자체는 아니지만, 구현자는 이 문서를 기준으로 `pipeline_gui/view.py`, `pipeline_gui/app.py`, setup helper layer를 바로 설계할 수 있어야 합니다.

---

## 2. 고정 전제

### 2.1 화면 위치

setup mode는 **launcher 메인 창 내부의 dedicated mode/screen**으로 구현합니다.

- 별도 OS window는 만들지 않음
- 기존 header와 상단 상태 영역은 유지 가능
- main content 영역만 setup 화면으로 전환
- restart confirmation만 예외적으로 confirmation dialog 사용 가능

### 2.2 layout

setup 화면은 승인된 구조대로 **좌/우 2-pane layout**을 사용합니다.

- 좌측 pane
  - agent selection
  - role bindings
  - options
  - executor override
  - action buttons
- 우측 pane
  - support level
  - validation summary
  - preview summary
  - apply readiness
  - restart notice

### 2.3 runtime / setup 경계

다음 경계는 hard rule입니다.

- runtime watcher는 `.pipeline/setup/**`를 무시
- runtime은 `.pipeline/config/agent_profile.json`만 읽음
- runtime은 `.pipeline/config/agent_profile.draft.json`을 절대 읽지 않음
- setup executor는 runtime control slot을 직접 수정하지 않음
- preview 단계에서는 active config를 절대 덮어쓰지 않음
- apply 완료 전에는 runtime refresh/restart를 시작하지 않음

### 2.4 setup attempt 식별

각 preview/apply/result round는 하나의 `setup_id`를 공유합니다.

- `request.json`
- `preview.json`
- `apply.json`
- `result.json`

이 네 파일은 모두 같은 `setup_id`를 가져야 합니다.

`Save draft` 자체는 `setup_id`를 만들지 않고, **`Generate preview` 시점에 새 `setup_id`를 발급**합니다.

---

## 3. 위젯 inventory

### 3.1 공통 규칙

- field id는 launcher 내부 상태/validation key로도 그대로 사용합니다.
- mutable field는 모두 inline error slot을 가집니다.
  - 예: `selected_agents.Claude.error`
  - 예: `role_bindings.implement.error`
- default는 **active config가 있으면 active 기준**, 없으면 아래 `first-run default`를 사용합니다.

### 3.2 first-run default

active config가 없을 때 기본값은 아래로 고정합니다.

- selected agents: `Claude`, `Codex`, `Gemini` 모두 선택
- `implement = Claude`
- `verify = Codex`
- `advisory = Gemini`
- `advisory_enabled = true`
- `operator_stop_enabled = true`
- `session_arbitration_enabled = true`
- `self_verify_allowed = false`
- `self_advisory_allowed = false`
- `setup_executor = auto`

### 3.3 위젯 표

| widget_id | model_key | pane | label | value type | first-run default | enable/disable rule |
|---|---|---|---|---|---|---|
| `setup_state_badge` | derived | right | `Setup State` | enum label | `DraftOnly` | 항상 표시, read-only |
| `selected_agents.Claude` | `selected_agents["Claude"]` | left | `Claude` | `bool` | `true` | 항상 enabled |
| `selected_agents.Codex` | `selected_agents["Codex"]` | left | `Codex` | `bool` | `true` | 항상 enabled |
| `selected_agents.Gemini` | `selected_agents["Gemini"]` | left | `Gemini` | `bool` | `true` | 항상 enabled |
| `role_bindings.implement` | `role_bindings.implement` | left | `Implement lane` | `AgentName \| null` | `Claude` | 선택 agent가 1개 이상일 때 enabled |
| `role_bindings.verify` | `role_bindings.verify` | left | `Verify lane` | `AgentName \| null` | `Codex` | 선택 agent가 1개 이상일 때 enabled |
| `role_bindings.advisory` | `role_bindings.advisory` | left | `Advisory lane` | `AgentName \| null` | `Gemini` | `advisory_enabled=true` 이고 선택 agent가 1개 이상일 때 enabled |
| `role_options.advisory_enabled` | `role_options.advisory_enabled` | left | `Enable advisory lane` | `bool` | `true` | 항상 enabled |
| `role_options.operator_stop_enabled` | `role_options.operator_stop_enabled` | left | `Enable operator stop` | `bool` | `true` | 항상 enabled |
| `role_options.session_arbitration_enabled` | `role_options.session_arbitration_enabled` | left | `Enable session arbitration` | `bool` | `true` | `advisory_enabled=true`일 때만 enabled. advisory off 전환 시 자동 `false` |
| `mode_flags.self_verify_allowed` | `mode_flags.self_verify_allowed` | left | `Allow self-verify` | `bool` | `false` | 항상 enabled |
| `mode_flags.self_advisory_allowed` | `mode_flags.self_advisory_allowed` | left | `Allow self-advisory` | `bool` | `false` | `advisory_enabled=true`일 때만 enabled. advisory off면 자동 `false` |
| `setup_executor` | `executor.override` | left | `Setup executor` | `auto \| AgentName` | `auto` | 선택 agent가 1개 이상일 때 enabled. option 목록은 `auto + selected_agents` |
| `support_level_badge` | derived | right | `Support level` | `supported \| supported_with_warnings \| experimental` | derived | valid config일 때 표시, invalid면 `INVALID CONFIG` 우선 |
| `validation_summary` | derived | right | `Validation summary` | list panel | empty | 항상 표시, read-only |
| `preview_summary` | derived | right | `Preview summary` | summary panel | `No preview generated` | 항상 표시, read-only |
| `preview_meta.setup_id` | derived | right | `Current setup_id` | text | `—` | `Generate preview` 후 표시 |
| `preview_meta.preview_fingerprint` | derived | right | `Preview fingerprint` | text | `—` | current preview 존재 시 표시 |
| `apply_readiness` | derived | right | `Apply readiness` | text | `Apply disabled: generate preview first` | 항상 표시, read-only |
| `restart_notice` | derived | right | `Restart notice` | text | hidden | `Applied`이고 `restart_required=true`일 때 표시 |
| `action.save_draft` | action | left footer | `Save draft` | button | n/a | truth table 따름 |
| `action.generate_preview` | action | left footer | `Generate preview` | button | n/a | truth table 따름 |
| `action.apply` | action | left footer | `Apply` | button | n/a | truth table 따름 |

### 3.4 inline error slot 규칙

좌측 pane의 mutable field는 모두 자기 아래 inline error slot을 가집니다.

- error만 inline
- warning/info는 우측 `validation_summary`에만 누적
- `Apply` 비활성 사유는 `apply_readiness`에 고정 표시

---

## 4. 파생 상태 모델

### 4.1 내부 파생 플래그

구현은 최소한 아래 파생 플래그를 유지해야 합니다.

- `has_error`
- `has_warning`
- `draft_dirty`
- `draft_saved`
- `current_setup_id`
- `current_draft_fingerprint`
- `current_preview_fingerprint`
- `current_preview_matches_draft`
- `apply_requested_for_current_setup`
- `approved_preview_fingerprint`
- `result_status`
- `result_matches_current_setup`
- `restart_required`

### 4.2 상태 우선순위

setup 화면의 derived state는 아래 우선순위로 계산합니다.

1. `InvalidConfig`
2. `ApplyPending`
3. `ApplyFailed`
4. `Applied`
5. `PreviewReady`
6. `PreviewWaiting`
7. `DraftOnly`

### 4.3 상태 정의

| state | entry condition | visible meaning | exit condition |
|---|---|---|---|
| `InvalidConfig` | `has_error=true` | 현재 form이 저장/preview/apply 불가 | error가 모두 해소됨 |
| `DraftOnly` | valid config이고 current preview가 없거나 stale | draft는 존재할 수 있으나 current preview/apply는 없음 | current draft 기준 preview가 도착하면 `PreviewReady` |
| `PreviewWaiting` | valid config이고 `request.json.setup_id == current_setup_id` 이며 `request.json.draft_fingerprint == current_draft_fingerprint` 이고 current preview가 아직 없음 | 현재 draft 기준 preview를 executor가 생성 중 | matching preview 도착 시 `PreviewReady`, draft 변경 시 `DraftOnly` |
| `PreviewReady` | valid config이고 `preview.json.setup_id == current_setup_id` 이며 `preview.draft_fingerprint == current_draft_fingerprint` | 현재 draft와 정확히 맞는 preview가 준비됨 | apply 요청 시 `ApplyPending`; draft 변경 시 `DraftOnly` |
| `ApplyPending` | `apply.json.setup_id == current_setup_id` 이고 `approved_preview_fingerprint == current_preview_fingerprint` 이며 matching result가 아직 없음 | apply가 승인되어 executor 결과 대기 중 | result success면 `Applied`, result fail이면 `ApplyFailed` |
| `Applied` | `result.status == "applied"` 이고 `result.setup_id == current_setup_id` 이고 `result.approved_preview_fingerprint == approved_preview_fingerprint == current_preview_fingerprint` 이며 active promotion 완료 | 현재 setup이 active로 승격됨 | form 변경 시 `DraftOnly` 또는 error 발생 시 `InvalidConfig` |
| `ApplyFailed` | `result.status == "apply_failed"` 이고 `result.setup_id == current_setup_id` 이고 `result.approved_preview_fingerprint == approved_preview_fingerprint` | apply가 실패했고 active는 기존 값 유지 | form 수정 또는 새 preview generation 시 `DraftOnly` 또는 `PreviewReady` |

### 4.4 상태별 화면 동작

- `InvalidConfig`
  - support level 대신 `INVALID CONFIG`
  - apply readiness는 첫 error reason을 고정 표기
- `DraftOnly`
  - preview summary는 마지막 preview가 stale이면 `stale preview ignored` 표기
- `PreviewReady`
  - preview summary, preview fingerprint, setup_id 모두 current 값 표시
- `ApplyPending`
  - 좌측 입력 fields와 3개 action button 모두 lock
  - `Apply in progress` badge 표시
- `Applied`
  - `restart_required=true`이면 restart notice와 confirmation CTA 표시
- `ApplyFailed`
  - validation summary 상단에 executor error 표시

---

## 5. 이벤트 및 상태 전이 표

| event_id | trigger | guard | actions | resulting state |
|---|---|---|---|---|
| `EVT_AGENT_CHECK_CHANGED` | Claude/Codex/Gemini checkbox 변경 | none | in-memory draft model 갱신, invalid binding 제거 또는 null 처리, support level/validation 재계산, `draft_dirty=true` | error 있으면 `InvalidConfig`, 아니면 대개 `DraftOnly` |
| `EVT_ROLE_BINDING_CHANGED` | implement/verify/advisory dropdown 변경 | field enabled | draft model 갱신, validation 재계산, `draft_dirty=true` | error 있으면 `InvalidConfig`, 아니면 `DraftOnly` |
| `EVT_OPTION_TOGGLED` | advisory/operator/session/self flags 변경 | field enabled | draft model 갱신, dependent field auto-normalize (`advisory_enabled=false`면 advisory binding/session_arbitration/self_advisory=false), validation 재계산, `draft_dirty=true` | error 있으면 `InvalidConfig`, 아니면 `DraftOnly` |
| `EVT_EXECUTOR_CHANGED` | executor override dropdown 변경 | field enabled | `executor.override` 갱신, info/warning 재계산, `draft_dirty=true` | error 있으면 `InvalidConfig`, 아니면 `DraftOnly` |
| `EVT_SAVE_DRAFT` | `Save draft` 클릭 | valid config, not apply pending | normalized draft model 계산, `agent_profile.draft.json` atomically write, `current_draft_fingerprint` 갱신, `draft_dirty=false` | matching preview 없으면 `DraftOnly`, matching preview 있으면 `PreviewReady` |
| `EVT_GENERATE_PREVIEW` | `Generate preview` 클릭 | valid config, not apply pending | draft dirty면 먼저 `EVT_SAVE_DRAFT` 실행, 새 `setup_id` 발급, `request.json` write, local/default executor adapter가 비동기 preview materialization 시작 | `PreviewWaiting` |
| `EVT_PREVIEW_ARRIVED` | `preview.json` polling 감지 | `preview.setup_id == current_setup_id` | `preview_fingerprint`, support level, warnings, planned changes 갱신; `preview.draft_fingerprint == current_draft_fingerprint`면 current preview로 채택, 아니면 stale preview로 무시 | match면 `PreviewReady`, mismatch면 기존 state 유지 |
| `EVT_APPLY` | `Apply` 클릭 | current state=`PreviewReady` | `apply.json` write with `setup_id`, `approved_preview_fingerprint`, chosen executor; input lock | `ApplyPending` |
| `EVT_RESULT_ARRIVED` | `result.json` polling 감지 | `result.setup_id == current_setup_id` | success/failure 판정, success면 active promotion guard 평가, failure면 errors 표시 | success면 `Applied`, fail면 `ApplyFailed` |
| `EVT_RESTART_CONFIRM_ACCEPTED` | restart confirmation에서 Yes | current state=`Applied` and `restart_required=true` | existing launcher restart flow 호출, restart notice clear pending, poll refresh | state 유지 (`Applied`) |
| `EVT_RESTART_CONFIRM_DECLINED` | restart confirmation에서 No | current state=`Applied` and `restart_required=true` | restart notice 유지, runtime restart 미실행 | `Applied` 유지 |

### 5.1 중요한 이벤트 규칙

#### Generate preview

- 새 `setup_id`는 매번 새로 발급
- old preview/apply/result 파일은 삭제하지 않아도 되지만, **UI는 current `setup_id`가 아닌 slot payload를 모두 stale로 무시**

#### Preview arrival

- `preview.json`은 반드시 `preview_fingerprint`를 포함
- UI는 `preview.setup_id == current_setup_id` 와 `preview.draft_fingerprint == current_draft_fingerprint` 둘 다 만족할 때만 current preview로 채택

#### Apply

- `Apply`는 preview를 다시 생성하지 않음
- 현재 보여주는 preview를 그대로 승인
- 따라서 `apply.json.approved_preview_fingerprint`는 **현재 우측 pane에 보이는 preview fingerprint**와 정확히 같아야 함

#### Result arrival

- `apply_failed`는 active config를 절대 건드리지 않음
- `applied`라도 fingerprint mismatch면 active promotion 금지

---

## 6. 버튼 truth table

### 6.1 버튼 규칙의 기준 플래그

- `valid = not has_error`
- `dirty = draft_dirty`
- `preview_current = current preview exists and matches current draft + current setup_id`
- `apply_pending = current state == ApplyPending`
- `applied_current = current state == Applied and dirty=false`

### 6.2 truth table

| 조건 | SaveDraft | GeneratePreview | Apply | 비고 |
|---|---|---|---|---|
| `has_error=true` | disabled | disabled | disabled | `InvalidConfig` |
| `valid=true`, `dirty=true`, current preview 없음 | enabled | enabled | disabled | GeneratePreview는 내부적으로 save 후 request write |
| `valid=true`, `dirty=false`, draft saved, current preview 없음 | disabled | enabled | disabled | preview 생성 가능 |
| `valid=true`, `dirty=false`, `preview_current=true` | disabled | enabled | enabled | current preview 재생성은 허용 |
| `valid=true`, `dirty=true`, old preview only | enabled | enabled | disabled | old preview는 stale |
| `apply_pending=true` | disabled | disabled | disabled | apply 중에는 전체 action lock |
| `applied_current=true` | disabled | disabled | disabled | 새 변경 없으면 작업 종료 상태 |
| `state=Applied`, `dirty=true` | enabled | enabled | disabled | 새 draft cycle 시작 |
| `state=ApplyFailed`, `dirty=false` | disabled | enabled | disabled | preview를 다시 생성해 재시도 |

### 6.3 Apply 비활성 고정 메시지 규칙

`apply_readiness`는 아래 우선순위로 메시지를 고정 표시합니다.

1. `Apply disabled: invalid configuration`
2. `Apply disabled: save or regenerate preview for current draft`
3. `Apply disabled: waiting for preview`
4. `Apply disabled: apply already in progress`
5. `Apply enabled: preview matches current draft`

---

## 7. 파일 I/O 매핑

## 7.1 active config

경로:

```text
.pipeline/config/agent_profile.json
```

역할:

- runtime source of truth
- setup success 전까지 변경 금지
- launcher가 promotion 시에만 write

권장 필드:

```json
{
  "schema_version": 1,
  "selected_agents": ["Claude", "Codex", "Gemini"],
  "role_bindings": {
    "implement": "Claude",
    "verify": "Codex",
    "advisory": "Gemini"
  },
  "role_options": {
    "advisory_enabled": true,
    "operator_stop_enabled": true,
    "session_arbitration_enabled": true
  },
  "mode_flags": {
    "single_agent_mode": false,
    "self_verify_allowed": false,
    "self_advisory_allowed": false
  },
  "metadata": {
    "saved_at": "2026-04-08T21:30:00+09:00",
    "saved_by": "launcher",
    "source_setup_id": "setup-20260408-213000-01"
  }
}
```

## 7.2 draft config

경로:

```text
.pipeline/config/agent_profile.draft.json
```

역할:

- 현재 form의 persistent draft
- preview의 기준
- runtime은 무시

권장 필드:

- active config와 동일 본문
- metadata에 `draft_saved_at` 포함 가능

## 7.3 request.json

경로:

```text
.pipeline/setup/request.json
```

작성:

- launcher

포함 최소 필드:

- `status = "setup_requested"`
- `setup_id`
- `selected_agents`
- `role_bindings`
- `role_options`
- `mode_flags`
- `config_paths.active`
- `config_paths.draft`
- `draft_fingerprint`
- `executor_candidate`

## 7.4 preview.json

경로:

```text
.pipeline/setup/preview.json
```

작성:

- setup executor

포함 최소 필드:

- `status = "preview_ready"`
- `setup_id`
- `executor`
- `draft_fingerprint`
- `preview_fingerprint`
- `support_level`
- `warnings`
- `planned_changes`
- `diff_summary`

## 7.5 apply.json

경로:

```text
.pipeline/setup/apply.json
```

작성:

- launcher

포함 최소 필드:

- `status = "apply_requested"`
- `setup_id`
- `executor`
- `approved_at`
- `approved_preview_fingerprint`

## 7.6 result.json

경로:

```text
.pipeline/setup/result.json
```

작성:

- setup executor

포함 최소 필드:

- `status = "applied" | "apply_failed"`
- `setup_id`
- `executor`
- `approved_preview_fingerprint`
- `restart_required`
- `changed_files`
- `warnings`
- `errors`

### 7.7 action별 I/O 표

| action | read | write | note |
|---|---|---|---|
| screen load | `agent_profile.json`, optional `agent_profile.draft.json`, optional `preview.json`, optional `apply.json`, optional `result.json` | 없음 | draft가 있으면 draft를 form에 로드, 없으면 active 또는 first-run default |
| field change | in-memory only | 없음 | dirty만 세움 |
| save draft | current form model | `agent_profile.draft.json` | atomic write |
| generate preview | `agent_profile.draft.json` or current form | `agent_profile.draft.json`(필요 시), `request.json` | 새 `setup_id` 발급 |
| preview arrival | `preview.json` | 없음 | current setup_id와 fingerprint match일 때만 채택 |
| apply | current preview | `apply.json` | preview current match가 guard |
| result arrival | `result.json`, `agent_profile.draft.json` | `agent_profile.json`(promotion 성공 시에만) | explicit promotion guard 적용 |

---

## 8. active promotion guard

### 8.1 hard guard

active promotion은 아래 조건을 **모두 만족할 때만** 일어납니다.

1. `result.status == "applied"`
2. `result.setup_id == current_setup_id`
3. `apply.json.setup_id == current_setup_id`
4. `preview.json.setup_id == current_setup_id`
5. `result.approved_preview_fingerprint == apply.json.approved_preview_fingerprint`
6. `apply.json.approved_preview_fingerprint == preview.json.preview_fingerprint`
7. `.pipeline/config/agent_profile.draft.json` 이 존재함
8. `fingerprint(agent_profile.draft.json) == current_draft_fingerprint`

즉 수식으로는 아래와 같습니다.

```text
result.status == "applied"
AND result.setup_id == current_setup_id
AND result.approved_preview_fingerprint
    == approved_preview_fingerprint
    == current_preview_fingerprint
AND draft.json exists
AND fingerprint(draft.json) == current_draft_fingerprint
```

### 8.2 promotion actor

active promotion은 **launcher가 수행**합니다.

- setup executor는 문서/slot materialization과 `result.json` 기록까지만 담당
- `agent_profile.json` 승격은 launcher가 guard를 검증한 뒤 수행

이렇게 하면:

- executor가 preview/apply/result와 active config를 동시에 만지지 않게 되고
- setup orchestration과 materialization 책임이 분리됩니다.

### 8.3 promotion 실패 처리

아래 중 하나라도 만족하지 않으면 promotion은 **실패가 아니라 보류/거부**로 처리합니다.

- `result.status != "applied"`
- `setup_id` mismatch
- fingerprint mismatch
- draft file missing
- draft fingerprint drift after preview/apply
- `agent_profile.draft.json`을 찾을 수 없음

이 경우:

- `agent_profile.json`은 기존 active 유지
- UI는 `ApplyFailed` 또는 `DraftOnly`로 돌아가고 mismatch reason을 표시
- runtime restart는 시작하지 않음

---

## 9. restart confirmation

restart confirmation은 `Applied` 이후에만 등장합니다.

### 규칙

- `result.restart_required = true`일 때만 confirmation 표시
- `result.restart_required = false`면 confirmation 없이 `Applied` 종료

### confirmation 문구

권장 문구:

```text
Setup applied successfully. Restart watcher/launcher now to load the active profile?
```

### confirmation 동작

- Yes
  - existing launcher restart flow 호출
  - restart notice를 pending -> handled로 전환
- No
  - restart notice 유지
  - active config는 이미 승격된 상태이므로 다음 수동 restart까지 보존

---

## 10. 구현 범위 밖

이번 사양은 아래를 다루지 않습니다.

- setup executor가 실제로 어떤 prompt로 guide 문서를 세팅할지
- role-neutral runtime slot rename migration
- setup screen의 세부 색상/타이포그래피
- watcher의 setup polling 구현 세부

즉 이 문서는 **screen contract + state machine + file boundary**까지만 닫습니다.

---

## 11. 구현자용 요약

구현자는 아래만 기억하면 됩니다.

1. 좌측은 입력, 우측은 해석/preview
2. runtime은 active만 읽고 draft/setup namespace는 무시
3. `Generate preview`가 `setup_id`를 만든다
4. `Apply`는 current preview fingerprint를 그대로 승인한다
5. `result.status == "applied"`와 matching fingerprint/setup_id가 모두 맞을 때만 launcher가 active를 승격한다
