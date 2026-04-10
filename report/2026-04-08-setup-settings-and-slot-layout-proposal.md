# projectH setup settings 저장 위치 / setup slot layout 제안 (검토용 초안)

**작성일**: 2026-04-08  
**성격**: 검토용 제안서  
**목적**: 최초 실행 setup에서 agent 선택/역할 바인딩을 저장할 위치와, 이를 agent에게 위임하기 위한 setup 전용 slot 구조를 normal runtime control slot과 분리해서 정리

---

## 1. 이 문서의 위치

이 문서는 아직 canonical 운영 규칙이 아닙니다.

즉:
- 아직 `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`에 고정하지 않음
- 아직 launcher / watcher / setup flow 구현을 바꾸지 않음
- 먼저 `report/`에서 저장 위치와 slot layout을 검토하고, 승인 후에만 실제 구현/문서로 승격

---

## 2. 왜 별도 설계가 필요한가

이전 초안에서 정리한 것처럼, setup은 앞으로 아래를 다뤄야 합니다.

- 선택된 agent 집합
- implement / verify / advisory 역할 바인딩
- advisory/session arbitration/operator stop enable 여부
- guide 문서와 `.pipeline` 기본 슬롯 세팅

문제는 현재 `.pipeline`이 이미 **normal runtime control slot**으로 쓰이고 있다는 점입니다.

현재 canonical runtime slot:
- `claude_handoff.md`
- `gemini_request.md`
- `gemini_advice.md`
- `operator_request.md`
- `session_arbitration_draft.md`

따라서 setup까지 같은 이름 공간에 섞어 넣으면 아래 문제가 생깁니다.

1. watcher가 setup 파일을 normal dispatch signal로 오해할 수 있음
2. stale setup 요청이 active runtime control처럼 보일 수 있음
3. 설정 저장 파일과 실행 handoff 파일의 수명이 섞임

따라서 **setup 저장 위치와 setup slot은 normal runtime slot과 분리**하는 편이 맞습니다.

---

## 3. 제안 원칙

### 3.1 설정 저장은 project-local persistent

agent 선택 / 역할 바인딩은 프로젝트마다 달라질 수 있으므로, 전역 홈 디렉터리보다
**프로젝트 로컬 `.pipeline/` 아래에 persistent config로 저장**하는 편이 맞습니다.

### 3.2 setup slot은 runtime slot과 다른 namespace

setup request / preview / apply / result는 `.pipeline/` 안에 두더라도
**별도 하위 디렉터리**로 분리하는 편이 안전합니다.

### 3.3 승인 전/후 상태를 나눔

설정값은
- 사용자가 고른 draft
- 승인된 active config

를 분리해서 저장해야 합니다.

### 3.4 launcher는 orchestration만

launcher는
- 설정 입력
- preview 표시
- 승인
- restart orchestration

만 담당하고, 실제 문서/slot 세팅은 agent가 수행하도록 유지합니다.

---

## 4. 권장 디렉터리 구조

권장 구조는 아래와 같습니다.

```text
.pipeline/
  config/
    agent_profile.json
    agent_profile.draft.json
  setup/
    request.json
    preview.json
    apply.json
    result.json
  logs/
  state/
  locks/
  manifests/
```

### 해석

- `.pipeline/config/`
  - project-local persistent setup config
- `.pipeline/setup/`
  - setup phase에서만 쓰는 rolling slot
- `.pipeline/logs`, `.pipeline/state`, `.pipeline/locks`
  - 기존 runtime 용도 유지

즉 setup은 `.pipeline` 안에 두되,
**`config/`와 `setup/`으로 분리**하는 편이 가장 덜 충돌합니다.

---

## 5. settings 저장 위치 제안

### 5.1 active config

권장 경로:

```text
.pipeline/config/agent_profile.json
```

역할:
- 현재 프로젝트에서 승인된 agent 선택/역할 바인딩의 source of truth
- launcher 재실행 후에도 유지
- watcher / launcher / setup agent가 공통으로 읽을 수 있음
- **runtime은 이 파일만 읽고, draft config는 절대 읽지 않음**

### 5.2 draft config

권장 경로:

```text
.pipeline/config/agent_profile.draft.json
```

역할:
- 사용자가 UI에서 고른 미승인 설정
- preview를 위해 사용
- 승인되기 전까지 runtime source of truth로 보지 않음
- launcher setup mode와 setup executor만 읽음

### 5.3 왜 `state/`가 아니라 `config/`인가

`state/`는 현재 runtime 흔적에 가깝고, setup 선택값은 session 간에도 보존할 가치가 있습니다.
따라서 agent 구성과 역할 바인딩은
**runtime state가 아니라 project config**로 보는 편이 맞습니다.

---

## 6. settings 스키마 저장 예시

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
    "saved_at": "2026-04-08T20:15:00+09:00",
    "saved_by": "launcher"
  }
}
```

### 추가 메모

- `saved_at`, `saved_by` 정도의 metadata는 있는 편이 좋음
- 나중에 agent executor가 적용 결과를 적을 때 `applied_by`, `applied_at`을 별도 result에 두는 편이 더 낫고, active config 자체에 과도한 실행 이력을 넣을 필요는 없음

---

## 7. setup slot layout 제안

권장 경로:

```text
.pipeline/setup/request.json
.pipeline/setup/preview.json
.pipeline/setup/apply.json
.pipeline/setup/result.json
```

이 네 파일은 normal runtime slot과 별도로, **setup mode에서만 읽는 rolling slot**입니다.
canonical payload는 JSON으로 두고, 필요하면 launcher가 사람이 보기 쉬운 preview 텍스트를 별도 UI에서 렌더링하는 편이 맞습니다.

### 7.0 setup_id 원칙

각 setup 시도는 반드시 하나의 `setup_id`를 가져야 합니다.

즉:
- `request.json`
- `preview.json`
- `apply.json`
- `result.json`

이 네 파일은 모두 같은 `setup_id`를 공유해야 합니다.

이유:
- 이전 setup 시도의 stale preview/result가 현재 요청과 섞이지 않게 하기 위해
- 승인 버튼이 지금 보고 있는 preview와 같은 요청을 가리킨다는 것을 보장하기 위해
- restart 직전/직후에 어떤 setup 시도가 실제로 적용됐는지 다시 추적하기 위해

### 7.1 request slot

경로:

```text
.pipeline/setup/request.json
```

작성자:
- launcher

역할:
- selected agent와 role binding에 맞는 setup 작업 요청

권장 상태:

```text
STATUS: setup_requested
```

포함 내용:
- `setup_id`
- 대상 프로젝트 경로
- selected agents
- role bindings
- enabled options
- active/draft config 경로
- 어떤 문서/slot을 세팅해야 하는지
- setup executor 후보

### 7.2 preview slot

경로:

```text
.pipeline/setup/preview.json
```

작성자:
- selected setup executor agent

역할:
- 실제로 적용될 변경 preview와 경고를 사용자에게 보여줌

권장 상태:

```text
STATUS: preview_ready
```

포함 내용:
- `setup_id`
- 생성/수정 예정 파일
- 예상 diff 요약
- 경고/제약
- 현재 조합이 supported / supported with warnings / experimental 중 어디인지

### 7.3 apply slot

경로:

```text
.pipeline/setup/apply.json
```

작성자:
- launcher 또는 operator confirmation flow

역할:
- preview를 보고 사용자가 승인했다는 신호

권장 상태:

```text
STATUS: apply_requested
```

포함 내용:
- `setup_id`
- 승인 시각
- 승인한 config fingerprint
- setup executor가 실제로 적용해야 할 범위

### 7.4 result slot

경로:

```text
.pipeline/setup/result.json
```

작성자:
- setup executor agent

역할:
- 적용 완료 / 실패 결과와 restart 필요 여부를 남김

권장 상태:

```text
STATUS: applied
```

또는

```text
STATUS: apply_failed
```

포함 내용:
- `setup_id`
- 실제 변경 파일
- 적용 성공/실패
- restart required 여부
- 남은 경고

---

## 8. setup flow 제안

### 권장 순서

1. launcher가 UI에서 agent 선택 + 역할 바인딩을 받음
2. launcher가 `agent_profile.draft.json` 저장
3. launcher가 `.pipeline/setup/request.json` 작성
4. selected setup executor agent가 request를 읽고 preview 생성
5. launcher가 preview를 사용자에게 보여줌
6. 사용자가 승인하면 launcher가 `.pipeline/setup/apply.json` 작성
7. setup executor agent가 실제 문서/slot 세팅 적용
8. setup executor agent가 `.pipeline/setup/result.json` 작성
9. launcher가 `agent_profile.draft.json`을 `agent_profile.json`으로 승격
10. watcher / launcher refresh 또는 restart

즉 setup은 단일 파일 overwrite보다,
**request -> preview -> apply -> result** 순으로 가는 편이 approval-based 구조와 맞습니다.

---

## 9. setup slot과 runtime slot의 경계

중요한 점은 setup slot이 normal runtime slot과 섞이면 안 된다는 것입니다.

따라서 아래가 필요합니다.

1. watcher는 기본 runtime mode에서 `.pipeline/setup/**`를 dispatch signal로 읽지 않음
2. launcher는 setup mode일 때만 `.pipeline/setup/*.json`을 관찰
3. runtime은 `agent_profile.json`만 읽고 `agent_profile.draft.json`은 읽지 않음
4. setup executor는 normal runtime control slot(`claude_handoff.md`, `gemini_request.md`, `gemini_advice.md`, `operator_request.md`)을 직접 건드리지 않음
5. apply 완료 전에는 runtime refresh/restart를 하지 않음
6. `.pipeline/setup/request.json`은 `claude_handoff.md` 같은 implement handoff로 해석하지 않음
7. `.pipeline/setup/result.json`은 `/work`, `/verify` 대체물이 아님

즉 setup slot은 **초기화/구성 phase 전용**, runtime slot은 **작업 phase 전용**으로 분리하는 편이 맞습니다.

---

## 10. 누구를 setup executor로 둘 것인가

선택된 agent가 여러 명일 때, setup executor는 별도 결정이 필요합니다.

권장 기본값:

1. `verify`로 바인딩된 agent
2. `implement`로 바인딩된 agent
3. 그 외 selected agent 중 현재 projectH 기준 지원 수준이 가장 높은 agent

이유:
- setup은 “코드 작성”보다 “규칙 반영 + diff 생성 + 검증” 성격이 강해서 verify쪽 기본값이 더 자연스럽기 때문
- 다만 이건 권장 기본값일 뿐이고, UI에서 override 가능하게 두는 편이 맞음

다만 장기적으로는 executor도 사용자 override 가능하게 두는 편이 맞습니다.

---

## 11. 1차 구현 시 가장 먼저 필요한 것

1. `.pipeline/config/`와 `.pipeline/setup/` namespace 추가
2. `agent_profile.draft.json` / `agent_profile.json` 스키마 저장
3. setup request / preview / apply / result JSON slot 형식 고정
4. launcher UI에서 preview까지 연결

이 단계에서는 아직 watcher 자동 setup dispatch까지 하지 않아도 됩니다.
처음엔 launcher가 setup executor에게 명시적으로 넘기는 편이 더 안전합니다.

---

## 12. 제안 결론

agent 선택과 역할 바인딩을 실제로 운영 가능한 구조로 만들려면,
가장 먼저 필요한 것은 **설정 저장 위치와 setup 전용 slot namespace를 normal runtime slot과 분리하는 것**입니다.

따라서 1차 권장안은 아래입니다.

- active config:
  - `.pipeline/config/agent_profile.json`
- draft config:
  - `.pipeline/config/agent_profile.draft.json`
- setup slots:
  - `.pipeline/setup/request.json`
  - `.pipeline/setup/preview.json`
  - `.pipeline/setup/apply.json`
  - `.pipeline/setup/result.json`

즉 setup은
**project-local config + setup-only slot namespace + agent-executed apply flow**
로 가는 것이 가장 자연스럽습니다.

이 초안이 승인되면 다음 단계에서
- launcher UI fields
- validation messages
- setup preview rendering
- setup executor selection rule

을 실제 구현 설계로 더 좁히는 것이 적절합니다.
