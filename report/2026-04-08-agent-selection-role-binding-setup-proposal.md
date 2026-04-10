# projectH agent 선택 / 역할 바인딩 / setup delegation 제안 (검토용 초안)

**작성일**: 2026-04-08  
**성격**: 검토용 제안서  
**목적**: 최초 실행 setup에서 agent 선택을 자유롭게 허용하면서도, 현재 `projectH`의 multi-lane 구조를 다른 프로젝트에도 재사용 가능한 형태로 일반화할 수 있는지 검토

---

## 1. 이 문서의 위치

이 문서는 아직 canonical 운영 규칙이 아닙니다.

즉:
- 아직 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에 고정하지 않음
- 아직 launcher UI나 `.pipeline` control flow 구현을 바꾸지 않음
- 먼저 `report/`에서 구조를 검토하고, 승인 후에만 상위 규칙/구현으로 승격

---

## 2. 현재 문제의식

현재 `projectH`의 기본 전제는 사실상 아래처럼 고정돼 있습니다.

- `Claude = implement`
- `Codex = verify / next handoff`
- `Gemini = advisory / tie-break`

이 구조는 지금 저장소에는 잘 맞지만, 아래 두 조건을 만족시키기 어렵습니다.

1. **사용자마다 어떤 agent를 쓸지 다를 수 있음**
   - `Claude + Codex`
   - `Claude + Codex + Gemini`
   - `Codex only`
   - 그 외 조합

2. **사용자마다 역할 배정도 다를 수 있음**
   - 어떤 사용자는 `Codex = implement`, `Claude = verify`를 원할 수 있음
   - advisory lane을 아예 끄거나, verify lane과 advisory lane을 같은 agent에 맡길 수도 있음

따라서 앞으로는
**“어떤 agent를 쓰는가”**와 **“누가 implement / verify / advisory를 맡는가”**를 분리해서 설계하는 편이 맞습니다.

---

## 3. 핵심 제안

### 3.1 agent 선택과 역할 배정을 분리

최초 실행 setup은 아래 2단으로 이해하는 것이 적절합니다.

1. **Agent selection**
   - `Claude`
   - `Codex`
   - `Gemini`
   - 이 3개 중 아무 조합이나 선택 가능해야 함

2. **Role binding**
   - `implement`
   - `verify`
   - `advisory`
   - 위 역할을 선택된 agent 중 누구에게 맡길지 별도로 바인딩

즉 앞으로의 설정 단위는:
- `선택된 agent 집합`
- `역할 바인딩`

두 가지가 되어야 합니다.

### 3.2 setup은 launcher가 직접 완료하지 않음

최초 setup에서 필요한 문서/slot 세팅은 launcher가 직접 문서를 완성하는 구조보다,
**launcher가 setup 요청만 만들고, 선택된 agent가 guide 기준으로 실제 설정 작업을 수행하는 구조**가 더 맞습니다.

즉 역할은 이렇게 나뉩니다.

- launcher
  - 사용자의 선택을 받음
  - 설정 요청을 구성함
  - preview / 승인 / 적용 재시작 흐름을 관리함

- selected agent(s)
  - guide 기준으로 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.pipeline/*`를 실제 세팅함
  - 프로젝트별 기본 템플릿을 맞춤 반영함

- user
  - preview를 보고 승인함

즉 launcher는 **setup orchestrator**, agent는 **setup executor**로 보는 편이 맞습니다.

---

## 4. 경우의 수 전제

### 4.1 agent 선택 조합

`Claude / Codex / Gemini` 기준으로 선택 조합은 7개입니다.

1. `Claude`
2. `Codex`
3. `Gemini`
4. `Claude + Codex`
5. `Claude + Gemini`
6. `Codex + Gemini`
7. `Claude + Codex + Gemini`

`아무것도 선택 안 함`은 invalid로 간주합니다.

### 4.2 역할 바인딩 경우의 수

역할은 최소 3개입니다.

- `implement`
- `verify`
- `advisory`

선택된 agent 수를 `n`이라고 하면, 역할 바인딩 조합 수는 기본적으로 `n^3`입니다.

예:
- 1 agent 선택 시: 1가지
- 2 agents 선택 시: 8가지
- 3 agents 선택 시: 27가지

즉 이 문제는 고정 profile 몇 개로만 다루기보다,
**설정 스키마 + validation 규칙**으로 다루는 편이 맞습니다.

---

## 5. 설정 스키마 초안

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
  }
}
```

### 필드 해석

- `selected_agents`
  - 실제로 이번 프로젝트에서 활성화한 agent 목록

- `role_bindings`
  - `implement`, `verify`, `advisory`를 각각 누가 맡는지 명시

- `role_options`
  - 특정 흐름 자체를 enable/disable
  - 예: advisory lane 비활성, session arbitration 비활성

- `mode_flags`
  - self-verify, self-advisory, single-agent 허용 여부를 명시

---

## 6. validation 규칙 초안

### 필수 규칙

1. `implement`는 반드시 지정
2. `role_bindings`의 값은 모두 `selected_agents` 안에 있어야 함
3. `selected_agents`는 최소 1개

### 권장 규칙

4. `verify`는 가능하면 지정, 없으면 warning
5. `advisory_enabled = false`면 advisory binding 비활성
6. `session_arbitration_enabled = true`인데 advisory lane이 없으면 warning 또는 자동 비활성

### 충돌 규칙

7. `self_verify_allowed = false`면 `implement != verify`
8. `self_advisory_allowed = false`면 advisory를 implement/verify와 분리
9. `single_agent_mode = true`가 아닌데 선택된 agent가 1개면 warning

즉 설정은 자유롭게 받되,
**현재 지원 수준 / 권장 수준 / 경고 수준**을 명확히 보여주는 편이 맞습니다.

---

## 7. UI 초안

### Step 1. Agent selection

- 체크박스:
  - `Claude`
  - `Codex`
  - `Gemini`

### Step 2. Role binding

- 드롭다운:
  - `Implement lane`
  - `Verify lane`
  - `Advisory lane`
- 각 드롭다운 후보는 Step 1에서 선택한 agent만 표시

### Step 3. Options

- `Enable advisory lane`
- `Enable operator stop`
- `Enable session arbitration`
- `Allow self-verify`
- `Allow self-advisory`

### Step 4. Preview

- 활성 agent
- 역할 바인딩
- 활성 `.pipeline` slot
- 생성/갱신 예정 문서
- 경고/제한 사항

즉 UI는 단순 “3가지 preset 중 하나 고르기”보다,
**선택 + 바인딩 + preview** 구조가 더 맞습니다.

---

## 8. `.pipeline`와의 관계

현재 `.pipeline` 파일명은 agent 이름에 묶여 있습니다.

- `claude_handoff.md`
- `gemini_request.md`
- `gemini_advice.md`
- `operator_request.md`

하지만 장기적으로는 실제 의미가 agent명보다 role에 가까워집니다.

즉 내부적으로는 최소한 이렇게 봐야 합니다.

- `implement handoff`
- `verify follow-up`
- `advisory request`
- `operator stop`

따라서 권장 방향은:

1. **당장은 파일명 유지**
   - 현재 watcher / launcher / docs와의 호환성 때문

2. **내부 해석은 role 중심으로 전환**
   - 예: `claude_handoff.md`는 당장은 legacy 이름이지만, 의미는 `implement handoff`

3. **나중에 필요하면 role-neutral 파일명으로 migration**
   - 이건 2차 과제

즉 지금 단계에서는
**설정은 role 기준, 파일명은 legacy 유지**
가 가장 안전합니다.

---

## 9. 조합별 해석 가이드

### 현재 바로 자연스러운 조합

- `Claude + Codex`
- `Claude + Codex + Gemini`

### 추가 규칙이 필요한 조합

- `Codex only`
- `Codex + Gemini`
- `Claude only`
- `Claude + Gemini`
- `Gemini only`

즉 선택은 자유롭게 열어두되,
UI preview에서 아래를 같이 표시하는 편이 맞습니다.

- `supported`
- `supported with warnings`
- `experimental`

즉 “선택 가능”과 “현재 완전 지원”을 같은 뜻으로 두지 않는 편이 안전합니다.

---

## 10. setup 실행 방식 제안

### 현재 권장 흐름

1. 사용자가 agent와 역할을 선택
2. launcher가 setup request 초안을 생성
3. 선택된 setup executor agent가 guide 기준으로 문서/slot 세팅
4. preview diff를 보여줌
5. 사용자 승인
6. watcher / launcher refresh 또는 restart
7. 실제 작업 시작

즉 setup은
**launcher가 직접 다 쓰는 구조**보다
**agent에게 세팅 작업을 위임하는 approval-based 구조**
가 더 projectH 철학과 맞습니다.

---

## 11. 1차 구현 우선순위 제안

### 1차

- agent selection UI
- role binding UI
- settings schema 저장
- preview / validation

### 2차

- 선택 결과를 setup request로 변환
- agent가 guide 기준으로 문서/slot 세팅하도록 위임

### 3차

- 적용 후 watcher / launcher refresh
- 필요 시 restart까지 묶은 관리 액션

### 4차

- role-neutral internal mapping 정리
- legacy slot 이름과의 의미 분리 강화

즉 최초 slice는
**UI에서 자유 선택과 역할 바인딩을 받는 것**
부터 닫는 편이 가장 안전합니다.

---

## 12. 제안 결론

앞으로의 setup 설계는
**“세 agent 중 누굴 쓸까?”**가 아니라
**“어떤 agent를 활성화하고, 누가 implement / verify / advisory를 맡을까?”**
를 중심으로 가는 것이 맞습니다.

그리고 실제 문서/slot 세팅은 launcher가 직접 완료하기보다,
**launcher가 요청을 만들고 agent가 guide 기준으로 세팅 작업을 수행하는 구조**가 더 적절합니다.

즉 이 제안의 핵심은 세 가지입니다.

1. agent 선택은 모든 조합을 전제로 자유롭게 받는다
2. 역할 바인딩을 별도 설정으로 둔다
3. setup은 launcher orchestrator + agent executor 구조로 설계한다

이 초안이 승인되면, 다음 단계에서
- UI 입력 항목
- settings schema 저장 위치
- setup request slot 형식
- 조합별 warning/supported/experimental 표시

를 실제 구현 설계로 더 좁히는 것이 자연스럽습니다.
