# projectH setup foundation P0 실행안

**작성일**: 2026-04-09<br>
**성격**: 구현 직전 P0 실행안<br>
**목적**: setup 계획서의 `6.0 전역 불변식 / 상태 분류 / active profile resolver 계약`만 별도로 압축해, 바로 구현 슬라이스로 내릴 수 있는 기준선을 고정

---

## 1. 이번 P0가 닫는 범위

이번 P0는 아래 네 모듈 경계만 닫습니다.

- classifier
- resolver
- support-policy
- reconciliation

이번 P0는 아래를 하지 않습니다.

- first-run wizard
- auto-restart
- agent-driven setup executor
- full profile rollout 확대

즉 이번 단계의 목표는 setup UX를 넓히는 것이 아니라,
**setup entry와 runtime 해석과 restart reconciliation이 같은 truth를 보게 만드는 얇은 foundation**을 만드는 것입니다.

---

## 2. 새 모듈 경계

### 2.1 classifier

역할:
- project-local setup 진입 상태 판정

입력:
- `.pipeline/config/agent_profile.json`
- `.pipeline/config/agent_profile.draft.json`
- `.pipeline/setup/request.json`
- `.pipeline/setup/preview.json`
- `.pipeline/setup/apply.json`
- `.pipeline/setup/result.json`
- schema/version metadata

출력 상태:
- `first_run`
- `resume_setup`
- `needs_migration`
- `broken_active_profile`
- `ready_normal`

precedence:
1. `broken_active_profile`
2. `needs_migration`
3. `resume_setup`
4. `first_run`
5. `ready_normal`

### 2.2 resolver

역할:
- active profile을 runtime이 소비하는 단일 plan으로 변환

입력:
- `.pipeline/config/agent_profile.json`

출력 shape:

```json
{
  "resolution_state": "ready",
  "support_level": "supported",
  "effective_runtime_plan": {
    "enabled_lanes": ["Claude", "Codex", "Gemini"],
    "role_owners": {
      "implement": "Claude",
      "verify": "Codex",
      "advisory": "Gemini"
    },
    "prompt_owners": {
      "implement": "Claude",
      "verify": "Codex",
      "advisory": "Gemini"
    },
    "controls": {
      "launch_allowed": true,
      "apply_allowed": true,
      "advisory_enabled": true
    }
  },
  "messages": []
}
```

### 2.3 support-policy

역할:
- support level을 실제 행동으로 매핑

정책:
- `supported`
  preview 허용, apply 허용, launch 허용
- `experimental`
  preview 허용, apply 허용, launch 허용
  단, setup/launcher 경고 배너 필수
- `blocked`
  preview 허용
  apply 차단
  launch 차단
  fail-open 금지

### 2.4 reconciliation

역할:
- apply 이후 restart 전후의 단일 truth 유지

durable marker:

```text
.pipeline/setup/last_applied.json
```

최소 필드:

```json
{
  "setup_id": "setup-20260409-000001-abcd12",
  "approved_preview_fingerprint": "sha256:...",
  "active_profile_fingerprint": "sha256:...",
  "applied_at": "2026-04-09T12:00:00+09:00",
  "restart_required": true,
  "executor": "Codex"
}
```

fingerprint 계산 규칙:

- `approved_preview_fingerprint`와 `active_profile_fingerprint`는 canonical JSON 기준으로 계산
- 인코딩은 UTF-8 사용
- key ordering은 `sort_keys=true`로 고정
- 직렬화 separator는 공백 없는 canonical form으로 고정
- 줄바꿈은 LF로 정규화한 뒤 hash 계산
- 같은 의미의 payload가 환경 차이만으로 다른 fingerprint를 만들지 않게 해야 함

---

## 3. 공개 계약

### 3.1 입력 파일

- classifier는 active/draft/setup slots를 읽을 수 있음
- resolver는 active profile만 읽음
- reconciliation은 `agent_profile.json`과 `last_applied.json`을 우선 truth로 사용

### 3.2 에러 shape

최소 공통 에러 shape는 아래면 충분합니다.

```json
{
  "code": "BROKEN_ACTIVE_PROFILE",
  "severity": "error",
  "message": "Active profile cannot be resolved.",
  "details": {
    "path": ".pipeline/config/agent_profile.json"
  }
}
```

필수 에러 코드는 최소한 아래를 둡니다.

- `BROKEN_ACTIVE_PROFILE`
- `UNSUPPORTED_SCHEMA_VERSION`
- `NEEDS_MIGRATION`
- `BLOCKED_PROFILE`
- `RECONCILIATION_MISMATCH`

### 3.3 precedence

- 진입 상태 판정은 classifier precedence를 따름
- runtime 해석은 resolver 결과만 따름
- launch/apply 허용 여부는 support-policy 결과만 따름
- restart 후 success/fail 판단은 reconciliation 결과만 따름

즉 app, launcher, watcher가 같은 파일을 직접 따로 해석하지 않게 합니다.

---

## 4. 호출 지점

이번 P0에서 이 foundation을 호출해야 하는 지점은 아래입니다.

### 4.1 app 시작

- classifier 호출
- state에 따라 setup auto-entry / recovery CTA / normal home 진입 결정

### 4.2 preview/apply

- preview 생성 전에 support-policy 확인
- apply 직전에 resolver + support-policy 확인
- apply 성공 시 reconciliation marker 기록

### 4.3 launcher 진입

- resolver 호출
- 현재 active profile 요약 및 launch 허용 여부 결정

### 4.4 watcher 진입

- raw profile 직접 해석 금지
- resolver 또는 resolver가 만든 runtime plan만 소비

---

## 5. 테스트 매트릭스

### 5.1 상태 5종

- `first_run`
- `resume_setup`
- `needs_migration`
- `broken_active_profile`
- `ready_normal`

### 5.2 support 3종

- `supported`
- `experimental`
- `blocked`

### 5.3 reconciliation lifecycle

- apply 성공 -> `last_applied.json` 기록
- restart 후 active fingerprint 일치 -> success
- restart 후 active fingerprint 불일치 -> `RECONCILIATION_MISMATCH`
- stale setup artifact 존재 -> protected setup id 보존, 나머지 cleanup

### 5.4 최소 검증 단위

- classifier unit tests
- resolver unit tests
- support-policy behavior tests
- `last_applied.json` lifecycle tests

---

## 6. 비목표

이번 P0는 아래를 의도적으로 하지 않습니다.

- wizard 화면 설계
- 자동 재시작 orchestration
- agent executor prompt/dispatch 구현
- 모든 profile 조합 지원
- setup UI의 대규모 레이아웃 변경

이번 단계가 끝나면 다음으로 가야 할 것은 아래입니다.

1. state-classified onboarding 연결
2. executor contract 강화
3. runtime 반영 P0

---

## 7. 추천 구현 순서

1. classifier 추가
2. resolver 추가
3. support-policy 추가
4. `last_applied.json` reconciliation 추가
5. app/launcher/watcher 호출 지점 연결
6. 테스트 매트릭스 고정

이번 P0의 완료 기준은 한 줄로 정리하면 아래와 같습니다.

**setup 진입, runtime 해석, restart reconciliation이 더 이상 각자 다른 규칙을 쓰지 않는다.**
