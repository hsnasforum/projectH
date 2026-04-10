# projectH setup UI / validation / support matrix 제안 (검토용 초안)

**작성일**: 2026-04-08  
**성격**: 검토용 제안서  
**목적**: agent 선택 + 역할 바인딩 setup의 실제 UI/검증 단계에서 필요한 state transition, setup JSON schema, 지원 수준 판정, validation 메시지 카탈로그를 구체화

---

## 1. 이 문서의 위치

이 문서는 아직 canonical 운영 규칙이 아닙니다.

즉:
- 아직 launcher UI나 watcher runtime 판정에 반영하지 않음
- 먼저 `report/`에서 setup 흐름의 세부 계약을 검토하고, 승인 후에만 실제 구현/상위 문서로 승격

---

## 2. 가장 먼저 고정해야 하는 경계

다음 네 가지를 먼저 고정해야 합니다.

1. `agent_profile.json` vs `agent_profile.draft.json`
2. `.pipeline/setup/*.json`의 `setup_id`
3. runtime은 active config만 읽고 setup namespace는 무시
4. UI는 “선택 가능”과 “현재 완전 지원”을 분리해서 보여줌

이 네 가지가 흐리면,
- stale preview와 현재 request가 섞이고
- setup과 runtime이 충돌하고
- 사용자는 가능한 조합과 권장 조합을 구분하지 못하게 됩니다.

---

## 3. active / draft 상태 전이표

### 3.1 파일 역할

- `agent_profile.draft.json`
  - 사용자가 UI에서 고른 아직 미승인 설정
  - preview 기준
- `agent_profile.json`
  - 적용 완료된 현재 유효 설정
  - runtime source of truth

### 3.2 상태 전이

| 단계 | draft | active | 설명 |
|---|---|---|---|
| 초기 상태 | 없음 또는 이전 draft | 현재 active 유지 | setup 미시작 |
| 사용자가 선택 입력 | 새 draft 생성/갱신 | 현재 active 유지 | runtime 영향 없음 |
| preview 생성 | 같은 draft 유지 | 현재 active 유지 | preview만 표시 |
| apply 승인 | 같은 draft 유지 | 현재 active 유지 | 아직 실제 반영 전 |
| apply 성공 | draft를 active로 승격하거나 draft 복사 후 active 갱신 | 새 active 반영 | 이후 runtime refresh/restart 가능 |
| apply 실패 | draft 유지 가능 | 기존 active 유지 | 사용자가 수정 후 재시도 |
| 취소 | draft 삭제 또는 보존 | 기존 active 유지 | runtime 영향 없음 |

### 3.3 강제 규칙

- runtime은 `agent_profile.json`만 읽고, `agent_profile.draft.json`은 절대 읽지 않음
- preview 단계에서는 active를 덮어쓰지 않음
- apply 성공 전에는 restart를 하지 않음

---

## 4. setup JSON slot 스키마 초안

setup slot은 모두 같은 `setup_id`를 공유해야 합니다.

권장 공통 필드:

```json
{
  "setup_id": "setup-20260408-201500-01",
  "schema_version": 1,
  "project_root": "/home/user/code/projectH"
}
```

### 4.1 request.json

경로:

```text
.pipeline/setup/request.json
```

목적:
- launcher가 setup executor에게 전달하는 canonical 요청

예시 스키마:

```json
{
  "status": "setup_requested",
  "setup_id": "setup-20260408-201500-01",
  "schema_version": 1,
  "project_root": "/home/user/code/projectH",
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
  "config_paths": {
    "active": ".pipeline/config/agent_profile.json",
    "draft": ".pipeline/config/agent_profile.draft.json"
  },
  "executor_candidate": "Codex"
}
```

### 4.2 preview.json

경로:

```text
.pipeline/setup/preview.json
```

목적:
- executor가 생성하는 preview 결과

예시 스키마:

```json
{
  "status": "preview_ready",
  "setup_id": "setup-20260408-201500-01",
  "schema_version": 1,
  "executor": "Codex",
  "support_level": "supported_with_warnings",
  "warnings": [
    {
      "code": "SELF_ADVISORY_ENABLED",
      "severity": "warning",
      "message": "Advisory lane is bound to the same agent as verify."
    }
  ],
  "planned_changes": {
    "write": [
      "AGENTS.md",
      "CLAUDE.md",
      "GEMINI.md",
      ".pipeline/README.md"
    ],
    "update_slots": [
      ".pipeline/claude_handoff.md",
      ".pipeline/gemini_request.md",
      ".pipeline/gemini_advice.md"
    ]
  },
  "diff_summary": [
    "Normalize role wording to selected bindings.",
    "Disable advisory lane dispatch when advisory_enabled=false."
  ]
}
```

### 4.3 apply.json

경로:

```text
.pipeline/setup/apply.json
```

목적:
- preview를 보고 사용자가 승인했다는 canonical 신호

예시 스키마:

```json
{
  "status": "apply_requested",
  "setup_id": "setup-20260408-201500-01",
  "schema_version": 1,
  "approved_at": "2026-04-08T20:18:00+09:00",
  "approved_preview_fingerprint": "sha256:abc123",
  "executor": "Codex"
}
```

### 4.4 result.json

경로:

```text
.pipeline/setup/result.json
```

목적:
- executor가 남기는 최종 결과

예시 스키마:

```json
{
  "status": "applied",
  "setup_id": "setup-20260408-201500-01",
  "schema_version": 1,
  "executor": "Codex",
  "applied_at": "2026-04-08T20:19:30+09:00",
  "approved_preview_fingerprint": "sha256:abc123",
  "restart_required": true,
  "changed_files": [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".pipeline/README.md"
  ],
  "warnings": [],
  "errors": []
}
```

실패 시 예:

```json
{
  "status": "apply_failed",
  "setup_id": "setup-20260408-201500-01",
  "schema_version": 1,
  "executor": "Codex",
  "approved_preview_fingerprint": "sha256:abc123",
  "errors": [
    {
      "code": "DOC_SYNC_BLOCKED",
      "severity": "error",
      "message": "Canonical docs could not be updated safely."
    }
  ]
}
```

---

## 5. supported / warning / experimental 판정 매트릭스

### 5.1 판정 기준

- `supported`
  - 현재 projectH 구조에서 추가 역할 왜곡 없이 자연스럽게 운영 가능
- `supported_with_warnings`
  - 운영은 가능하지만 self-verify/self-advisory 등 주의점이 있음
- `experimental`
  - 현재 구조와 긴장이 커서 별도 규칙 또는 manual oversight가 큼

### 5.2 기본 매트릭스

| selected_agents | role binding 예시 | 판정 | 이유 |
|---|---|---|---|
| Claude + Codex + Gemini | implement=Claude, verify=Codex, advisory=Gemini | supported | 현재 full tri-lane canonical |
| Claude + Codex | implement=Claude, verify=Codex, advisory=Codex | supported | 현재 최소 권장 구성 |
| Codex + Gemini | implement=Codex, verify=Codex, advisory=Gemini | supported_with_warnings | self-verify 허용 필요 |
| Claude + Gemini | implement=Claude, verify=Claude, advisory=Gemini | supported_with_warnings | verify lane 부재를 self-verify로 메움 |
| Claude only | implement=Claude, verify=Claude, advisory=Claude | supported_with_warnings | single-agent mode 전제 |
| Codex only | implement=Codex, verify=Codex, advisory=Codex | supported_with_warnings | single-agent self-verify/self-advisory |
| Gemini only | implement=Gemini, verify=Gemini, advisory=Gemini | experimental | 현재 repo 운용 규칙과 가장 거리 멂 |

### 5.3 추가 downgrade 규칙

아래가 있으면 한 단계 낮춰 표시하는 편이 맞습니다.

- `verify` 미지정
- `session_arbitration_enabled=true`인데 advisory disabled
- `self_verify_allowed=false`인데 implement와 verify가 같음
- `self_advisory_allowed=false`인데 advisory가 implement/verify와 겹침

---

## 6. validation 메시지 카탈로그

### 6.1 error

저장/적용 불가. `Apply` 비활성 또는 request 생성 불가.

예:

- `NO_AGENT_SELECTED`
  - `최소 1개의 agent를 선택해야 합니다.`
- `IMPLEMENT_REQUIRED`
  - `Implement lane은 반드시 지정해야 합니다.`
- `ROLE_BINDING_OUTSIDE_SELECTION`
  - `역할에 선택되지 않은 agent가 바인딩되어 있습니다.`
- `SELF_VERIFY_FORBIDDEN`
  - `현재 설정에서는 implement와 verify를 같은 agent에 바인딩할 수 없습니다.`

### 6.2 warning

저장은 가능하지만 apply 전에 재확인 필요.

예:

- `VERIFY_MISSING`
  - `Verify lane이 비어 있습니다. single-agent/self-verify 방식으로 동작할 수 있습니다.`
- `ADVISORY_DISABLED_WITH_SESSION_ARBITRATION`
  - `Session arbitration이 켜져 있지만 advisory lane이 비활성입니다. arbitration은 자동으로 비활성화될 수 있습니다.`
- `EXPERIMENTAL_PROFILE`
  - `현재 조합은 experimental profile입니다. manual oversight가 더 많이 필요할 수 있습니다.`

### 6.3 info

자동 조정 또는 참고사항.

예:

- `EXECUTOR_DEFAULTED_TO_VERIFY`
  - `Setup executor가 verify lane 기준으로 Codex로 자동 선택되었습니다.`
- `ADVISORY_BOUND_TO_VERIFY`
  - `Advisory lane이 verify lane과 같은 agent에 묶였습니다.`
- `RUNTIME_WILL_USE_ACTIVE_ONLY`
  - `적용 전까지 runtime은 현재 active config만 유지합니다.`

---

## 7. launcher UI 필드 초안

### 입력 필드

1. agent 체크박스
   - `Claude`
   - `Codex`
   - `Gemini`

2. 역할 바인딩 드롭다운
   - `Implement lane`
   - `Verify lane`
   - `Advisory lane`

3. 옵션 토글
   - `Enable advisory lane`
   - `Enable operator stop`
   - `Enable session arbitration`
   - `Allow self-verify`
   - `Allow self-advisory`

4. 실행 관련 필드
   - `Setup executor`
   - `Support level`
   - `Preview summary`

### UI 동작

- 체크박스 변경 시 binding 후보 목록 갱신
- validation은 즉시 계산
- `Apply`는 error가 없을 때만 활성
- warning은 preview에 표시하되 apply를 막지는 않음
- info는 자동 보정 결과를 알려주는 수준으로 표시

---

## 8. setup executor 기본 선택 규칙

권장 기본 순서:

1. `verify`에 바인딩된 agent
2. `implement`에 바인딩된 agent
3. 그 외 selected agent 중 현재 projectH에서 지원 수준이 가장 높은 agent

이 규칙은 “항상 하나가 선택되도록” 만들어야 합니다.
다만 UI에서 사용자가 override할 수 있게 두는 편이 맞습니다.

---

## 9. runtime read boundary 재확인

setup 세부 설계에서 가장 중요한 운영 경계는 다시 아래입니다.

1. runtime watcher는 `.pipeline/setup/**`를 무시
2. runtime은 `agent_profile.json`만 읽음
3. setup executor는 runtime slot을 직접 건드리지 않음
4. apply 완료 전에는 runtime refresh/restart 금지

이 네 가지는 UI보다 먼저 고정해야 합니다.

---

## 10. 제안 결론

다음 단계 문서는 단순히 UI 배치도를 넘어서,
**active vs draft / setup_id / setup JSON slot / support level / validation catalog**
까지 한 번에 다뤄야 실제 구현에 들어갈 수 있습니다.

따라서 현재 기준에서 다음 단계에 필요한 최소 문서화 항목은 아래 네 가지입니다.

1. `agent_profile.json` / `agent_profile.draft.json` 상태 전이표
2. `.pipeline/setup/{request,preview,apply,result}.json` 스키마
3. supported / warning / experimental 판정 매트릭스
4. validation 메시지 카탈로그

이 문서는 그 네 가지를 1차로 고정하기 위한 초안입니다.
