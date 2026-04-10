# projectH launcher setup 화면 계약 제안 (검토용 초안)

**작성일**: 2026-04-08  
**성격**: 검토용 제안서  
**목적**: 최초 setup 화면을 실제 구현 가능한 수준으로 좁히기 위해, 한 화면 레이아웃과 메시지 표현 규칙, 액션 흐름을 정리

---

## 1. 이 문서의 위치

이 문서는 아직 canonical UI 규칙이 아닙니다.

즉:
- 아직 `pipeline_gui/` 구현에 반영하지 않음
- 먼저 `report/`에서 화면 계약을 검토하고, 승인 후 launcher UI 구현 slice로 승격

---

## 2. 기본 전제

이 화면은 아래 전제를 따릅니다.

1. agent 선택과 역할 바인딩은 분리
2. active config와 draft config는 분리
3. setup은 launcher가 orchestrate하고 agent가 execute
4. runtime은 active config만 읽고 `.pipeline/setup/**`는 무시

즉 setup 화면은 단순 설정 패널이 아니라,
**draft 생성 -> preview 생성 -> apply 승인**을 관리하는 한 화면 계약입니다.

---

## 3. 한 화면 레이아웃 제안

권장 구조는 **좌/우 2열**입니다.

### 좌측 패널: 입력 영역

순서:

1. **Agent selection**
   - `Claude`
   - `Codex`
   - `Gemini`
   - 체크박스 3개

2. **Role binding**
   - `Implement lane`
   - `Verify lane`
   - `Advisory lane`
   - 드롭다운 3개

3. **Options**
   - `Enable advisory lane`
   - `Enable operator stop`
   - `Enable session arbitration`
   - `Allow self-verify`
   - `Allow self-advisory`

4. **Executor**
   - `Setup executor`
   - 기본값은 자동 추천
   - 필요하면 override 가능

### 우측 패널: 해석/결과 영역

순서:

1. **Support level**
   - `supported`
   - `supported with warnings`
   - `experimental`

2. **Validation summary**
   - error / warning / info 누적 표시

3. **Preview summary**
   - selected agents
   - role bindings
   - enabled options
   - 생성/수정 예정 문서
   - setup executor

4. **Apply readiness**
   - `Apply 가능 / 불가`
   - 현재 비활성 사유

즉 입력은 왼쪽, 판단과 결과는 오른쪽으로 분리하는 편이 가장 읽기 쉽습니다.

---

## 4. 메시지 표현 규칙

### 4.1 error

의미:
- 저장/적용 불가
- 사용자가 먼저 수정해야 함

표현 위치:
- **해당 필드 바로 아래 inline**

예:
- agent를 아무것도 선택하지 않았으면 agent selection 영역 바로 아래
- implement가 비었으면 implement dropdown 바로 아래

표현 스타일:
- 빨간색
- 한 줄 요약 우선
- 필요하면 짧은 보조 설명 한 줄

### 4.2 warning

의미:
- 저장은 가능
- apply 전에 재확인 권장

표현 위치:
- **우측 패널 Validation summary에 누적**

이유:
- warning은 필드 자체가 깨진 것이 아니라 조합 해석 문제인 경우가 많기 때문

표현 스타일:
- 주황/노랑 계열
- code + 짧은 설명

### 4.3 info

의미:
- 자동 조정 결과
- 참고사항

표현 위치:
- **우측 패널 Validation summary 하단**

예:
- setup executor가 verify lane 기준으로 자동 선택됨
- advisory lane이 verify lane과 공유됨

표현 스타일:
- 파랑/회색 계열
- dismiss 없이 누적 가능

### 4.4 Apply 비활성 사유

의미:
- 사용자가 왜 지금 적용할 수 없는지 즉시 이해해야 함

표현 위치:
- **Apply 버튼 옆 고정 표기**

예:
- `Apply disabled: implement lane required`
- `Apply disabled: no agent selected`

즉 error는 inline, warning/info는 오른쪽 누적, Apply 막힘 이유는 버튼 옆 고정이 가장 맞습니다.

---

## 5. 액션 흐름

권장 액션은 세 단계입니다.

### 5.1 Save draft

역할:
- 현재 선택값을 `agent_profile.draft.json`으로 저장

버튼명 예시:
- `Save draft`

동작:
- error가 있으면 비활성
- warning이 있어도 가능
- 저장 후 draft timestamp 갱신

### 5.2 Generate preview

역할:
- `.pipeline/setup/request.json` 생성
- setup executor가 `.pipeline/setup/preview.json`을 생성하도록 요청

버튼명 예시:
- `Generate preview`

동작:
- error가 있으면 비활성
- draft가 저장되지 않았으면 내부적으로 저장 후 진행 가능
- preview 생성 중에는 pending 상태 표시

### 5.3 Apply

역할:
- 사용자가 preview를 승인
- `.pipeline/setup/apply.json` 생성
- executor가 실제 세팅 후 `.pipeline/setup/result.json` 기록

버튼명 예시:
- `Apply`

동작:
- preview가 현재 draft와 같은 `setup_id`일 때만 활성
- `preview_ready` + no error 상태에서만 활성
- 완료 후 restart required 여부를 별도 표시

즉 `Save draft -> Generate preview -> Apply` 순서를 화면에서 명확히 보여주는 편이 맞습니다.

---

## 6. 상태 표시 규칙

화면 상단 또는 우측 상단에 setup 상태 badge를 두는 것이 좋습니다.

권장 상태:

- `Draft only`
- `Preview ready`
- `Apply pending`
- `Applied`
- `Apply failed`

이 상태는 `.pipeline/setup/*.json`의 `status`와 연결하되,
runtime status와 섞지 않는 편이 맞습니다.

즉 이 화면은 `Pipeline RUNNING / STOPPED`가 아니라
**setup phase state**를 보여주는 별도 상태 모델이어야 합니다.

---

## 7. 필드별 즉시 validation 예시

### Agent selection

- 0개 선택:
  - inline error
  - `최소 1개의 agent를 선택해야 합니다.`

### Implement lane

- 비어 있음:
  - inline error
  - `Implement lane은 반드시 지정해야 합니다.`

### Verify lane

- 비어 있음:
  - 우측 warning
  - `Verify lane이 비어 있습니다. single-agent/self-verify 방식으로 동작할 수 있습니다.`

### Advisory lane

- advisory disabled인데 값이 남아 있음:
  - info
  - `Advisory lane is disabled. binding will be ignored.`

### Self-verify 금지 위반

- implement == verify, self_verify_allowed = false:
  - inline error under verify

즉 hard-invalid는 inline, 해석 경고는 우측 누적이 기본입니다.

---

## 8. Support level 표시 규칙

Support level은 우측 패널 상단에서 항상 보이는 것이 좋습니다.

표현 예:

- `SUPPORTED`
- `SUPPORTED WITH WARNINGS`
- `EXPERIMENTAL`

표시 기준:
- error가 있으면 support level보다 먼저 `INVALID CONFIG`로 보여줘도 됨
- valid config에 대해서만 support level 계산

Support level 아래에는 짧은 이유 1~2줄을 붙이는 편이 좋습니다.

예:
- `Current projectH flow supports this mapping without extra manual steps.`
- `This profile relies on self-verify and may need more operator oversight.`

---

## 9. 구현 전에 한 번 더 고정할 것

이 화면 계약으로 들어가기 전에 아래 3개만 더 합의하면 바로 구현 slice로 들어갈 수 있습니다.

1. setup 화면을 현재 launcher 메인 화면 안에 넣을지, first-run modal/wizard로 뺄지
2. preview를 JSON 그대로 보여줄지, 사람이 읽는 summary 카드로 렌더링할지
3. Apply 후 restart를 자동으로 할지, 사용자 confirm을 한 번 더 받을지

현재 판단으로는:
- first-run modal 또는 setup 전용 mode가 더 자연스럽고
- preview는 JSON raw가 아니라 summary 카드 렌더링이 낫고
- restart는 result가 `restart_required=true`일 때 명시 confirm을 한 번 더 받는 편이 안전합니다.

---

## 10. 제안 결론

다음 구현 단계의 launcher setup 화면은
**좌측 입력 / 우측 해석 / 3단계 액션 / 메시지 위치 규칙**
이 먼저 고정돼야 합니다.

따라서 현재 추천 화면 계약은 아래입니다.

- 좌측:
  - agent 선택
  - 역할 바인딩
  - 옵션
  - executor
- 우측:
  - support level
  - validation summary
  - preview summary
  - apply readiness
- 액션:
  - `Save draft`
  - `Generate preview`
  - `Apply`

이 문서가 승인되면, 다음 단계는 이제 report 초안이 아니라
실제 launcher UI slice로 들어가도 무리가 없는 상태에 가깝습니다.
