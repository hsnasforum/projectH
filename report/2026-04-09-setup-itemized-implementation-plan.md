# projectH setup 항목별 실행 계획서

**작성일**: 2026-04-09<br>
**성격**: 검토용 실행 계획서<br>
**목적**: 현재 launcher setup 구현 상태를 기준으로, 화면에 보이는 8개 항목을 각각 어떤 범위로 마무리할지와 어떤 순서로 진행할지를 한 문서에서 정리

---

## 1. 이 문서의 위치

이 문서는 아직 canonical 운영 규칙이 아닙니다.

즉:
- 아직 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에 고정하지 않음
- 아직 `start-pipeline.sh`, `watcher_core.py`, `pipeline-launcher.py`의 runtime 계약을 바꾸지 않음
- 먼저 현재 구현 기준선을 정확히 적고, 그 위에서 각 항목을 어떤 슬라이스로 구현할지 결정하기 위한 계획 문서로 사용

---

## 2. 현재 기준선

현재 코드 기준으로 보면 setup 계열은 아래까지는 이미 들어와 있습니다.

- `pipeline_gui/view.py`
  setup 전용 좌/우 2-pane 화면, agent 선택, role binding, option, executor, preview/apply/restart UI가 존재
- `pipeline_gui/app.py`
  `agent_profile.draft.json` / `agent_profile.json` / `.pipeline/setup/{request,preview,apply,result}.json` round-trip과 promotion guard, restart notice, confirm형 restart가 존재
- `pipeline_gui/setup_executor.py`
  `SetupExecutorAdapter` protocol, `LocalSetupExecutorAdapter`, stale staged file 정리, fault injection 테스트용 adapter가 존재

반대로 runtime 쪽은 아직 고정형입니다.

- `start-pipeline.sh`
  Claude / Codex / Gemini 3-lane을 고정으로 기동
- `watcher_core.py`
  verify pane, Claude handoff, Gemini arbitration 흐름이 고정 역할 전제를 사용
- `pipeline-launcher.py`
  3-agent 고정 표시와 pane 전제가 남아 있음

즉 현재 상태를 한 줄로 요약하면:

**setup UI와 setup state machine은 부분 구현됐지만, runtime은 아직 fixed three-lane contract에 가깝습니다.**

---

## 3. 전역 선행 계약

이 문서를 실행 문서로 쓰려면, 개별 항목보다 먼저 아래 네 가지를 닫아야 합니다.

1. setup 진입 상태 분류
2. active profile resolver 계약
3. support level의 행동 매핑
4. setup apply / restart reconciliation 단일 truth

### 3.1 setup 진입 상태 분류

`active profile 없음 = first-run`으로 단순화하면 안 됩니다.

최소한 아래 상태는 구분해야 합니다.

- `first_run`
  현재 schema 기준 active profile도 없고, resume 가능한 draft/in-flight setup도 없으며, migration 대상 legacy profile도 없음
- `resume_setup`
  current schema의 draft가 있거나, 같은 schema의 in-flight setup 흔적이 있어 setup을 이어서 진행할 수 있음
- `needs_migration`
  legacy profile 또는 이전 schema profile은 있으나, 명시된 migration path로 current schema로 올릴 수 있음
- `broken_active_profile`
  active profile이 있으나 손상, 불완전, unreadable, resolver 불일치 등으로 바로 해석할 수 없음
- `ready_normal`
  valid active profile이 있고 현재 runtime에 바로 적용 가능

권장 우선순위는 아래입니다.

1. `broken_active_profile`
2. `needs_migration`
3. `resume_setup`
4. `first_run`
5. `ready_normal`

즉 auto-entry는 `first_run` 하나만 보지 않고, 먼저 손상/마이그레이션/재진입 상태를 가려낸 뒤에만 사용해야 합니다.

### 3.2 active profile resolver 계약

runtime truth는 하나여야 합니다.

따라서 `start-pipeline.sh`, `watcher_core.py`, `pipeline-launcher.py`가 각자 profile을 해석하면 안 되고,
모두 하나의 **active profile resolver**만 보게 해야 합니다.

resolver의 최소 출력은 아래 정도로 고정하는 편이 좋습니다.

- `resolution_state`
  `ready` / `needs_migration` / `broken`
- `support_level`
  `supported` / `experimental` / `blocked`
- `effective_runtime_plan`
  enabled lanes, role owners, prompt owners, arbitration availability, disabled controls
- `messages`
  사용자용 설명과 launch/apply 차단 사유

입력 source of truth는 기본적으로 아래입니다.

- `.pipeline/config/agent_profile.json`
- 필요 시 schema/version metadata
- setup 재진입과는 분리된 resolver-level validation rules

### 3.3 support level의 행동 매핑

support level은 문구가 아니라 **행동**으로 닫아야 합니다.

권장 매핑은 아래입니다.

- `supported`
  preview 허용, apply 허용, launch 허용
- `experimental`
  preview 허용, apply 허용, launch 허용
  단, setup 화면과 launcher에 경고 배너를 고정 표시
- `blocked`
  preview 허용
  apply 차단, launch 차단을 명시적으로 수행
  runtime은 fail-open 하지 않고 명시적으로 중단

즉 `warning 또는 launch block`처럼 열어두지 말고,
적어도 `blocked`는 fail-loud behavior로 고정해야 합니다.

### 3.4 restart reconciliation 단일 truth

재시작 후 reconciliation을 하려면 durable marker가 먼저 있어야 합니다.

권장 단일 truth는 아래입니다.

```text
.pipeline/setup/last_applied.json
```

이 파일의 최소 필드는 아래가 적절합니다.

- `setup_id`
- `approved_preview_fingerprint`
- `active_profile_fingerprint`
- `applied_at`
- `restart_required`
- `executor`

cleanup 규칙도 같이 고정해야 합니다.

- in-flight `setup_id`와 `last_applied.setup_id`는 보호
- 그 외 canonical/staged setup artifacts는 retention 규칙으로 정리
- restart 후 reconciliation은 `agent_profile.json`과 `last_applied.json`만 우선 대조

---

## 4. 항목별 상태 요약

| 항목 | 현재 상태 | 현재 코드 기준 해석 |
|---|---|---|
| 전역 불변식 / 상태 분류 / active profile resolver 계약 | 미적용 | setup 진입 상태와 runtime truth를 하나로 묶는 계약이 아직 없음 |
| 최초 실행 onboarding 연결 | 부분 적용 | setup mode는 있으나 state-classified auto-entry는 아직 없음 |
| executor abstraction | 부분 적용 | adapter 경계는 있으나 timeout/cancel/single-flight/progress/write allowlist/idempotency 계약이 없음 |
| runtime 반영 P0 | 부분 적용 | 저장/표시/validation은 있으나 runtime은 아직 fixed three-lane 전제 |
| setup 후 재시작 | 부분 적용 | `restart_required`와 confirm형 restart는 있으나 durable marker 기반 reconciliation은 없음 |
| agent-driven setup executor | 미적용 | 선택된 agent가 실제 setup request를 실행하는 구조는 아직 없음 |
| 완전 자동 재시작 + 재진입 | 미적용 | 현재는 apply 후 수동 확인 기반 재시작 |
| first-run wizard | 미적용 | 별도 wizard나 modal 진입 UX 없음 |
| 지원 profile rollout 확대 | 미적용 | P0 runtime plan 이후 rollout 전략만 제안 상태 |

---

## 5. 권장 구현 순서

권장 순서는 아래입니다.

0. 전역 불변식 / 상태 분류 / active profile resolver 계약
1. 최초 실행 onboarding 연결
2. executor abstraction 마감
3. runtime 반영 P0
4. setup 후 재시작 마감
5. agent-driven setup executor
6. 완전 자동 재시작 + 재진입
7. first-run wizard
8. 지원 profile rollout 확대

이 순서를 권장하는 이유는 다음과 같습니다.

- onboarding보다 먼저 entry state 분류와 resolver가 있어야 기존 사용자 흐름을 깨지 않음
- runtime P0와 rollout 확대는 같은 에픽의 P0와 확장 단계로 보는 편이 truth가 하나로 유지됨
- executor abstraction이 강화돼야 local executor와 future agent executor가 같은 규칙을 따를 수 있음
- auto-restart, wizard는 앞선 truth contract가 닫힌 뒤에야 UX만 얇게 얹을 수 있음

---

## 6. 항목별 계획

### 6.0 전역 불변식 / 상태 분류 / active profile resolver 계약

#### 현재 상태

- setup mode는 자체 validation과 support level을 계산
- runtime은 여전히 `start-pipeline.sh`, `watcher_core.py`, `pipeline-launcher.py`가 고정 구조를 가정
- first-run, resume, migration, broken profile을 구분하는 classifier가 없음

#### 목표

setup entry와 runtime 해석이 모두 기대는 **얇은 공통 계약층**을 먼저 고정합니다.

#### 범위

- setup entry state classifier
- active profile resolver
- support level 행동 매핑
- `last_applied.json` durable marker

#### 구현 단계

1. project-local classifier를 추가해 `first_run`, `resume_setup`, `needs_migration`, `broken_active_profile`, `ready_normal`을 판정
2. active profile resolver를 추가해 `agent_profile.json -> effective_runtime_plan` 변환을 단일화
3. support level을 `supported`, `experimental`, `blocked`로 고정하고 행동을 명시
4. `.pipeline/setup/last_applied.json`을 reconciliation 단일 truth로 도입
5. launcher와 runtime 진입부는 개별 해석 대신 classifier/resolver만 참조

#### 검증

- classifier unit test
- resolver unit test
- support level별 behavior test
- `last_applied.json` lifecycle test

#### 완료 기준

- first-run 판정과 runtime 해석이 서로 다른 규칙을 사용하지 않음
- 이후 항목이 모두 같은 classifier/resolver를 재사용 가능

#### 남은 리스크

- 이 층을 과하게 넓히면 또 다른 mini-framework가 될 수 있음
- 따라서 setup entry + runtime plan + reconciliation까지만 딱 닫는 것이 적절함

---

### 6.1 최초 실행 onboarding 연결

#### 현재 상태

- 앱 시작 시 `_run_setup_check_silent()`로 hard blocker / soft warning 점검은 자동 수행
- setup 화면은 버튼으로 열 수 있음
- setup 진입은 classifier 없이 수동 버튼 중심

#### 목표

최초 실행 사용자가 setup 기능을 찾아 헤매지 않도록, 기존 setup mode를 **state-classified onboarding entry**와 연결합니다.

#### 범위

- 별도 wizard를 만드는 것이 아니라 기존 setup mode 진입을 먼저 정리
- 6.0의 classifier 결과를 기반으로 entry를 분기
- runtime 고정 구조는 이 단계에서 바꾸지 않음

#### 구현 단계

1. 앱 시작 시 classifier를 먼저 실행
2. `first_run`, `resume_setup`, `needs_migration`, `broken_active_profile` 각각의 entry copy와 CTA를 분리
3. `first_run`과 `resume_setup`은 setup mode auto-entry 또는 강한 CTA로 유도
4. `needs_migration`, `broken_active_profile`은 일반 first-run copy 대신 복구/이관 중심 메시지 사용
5. `ready_normal`에서는 기존 home 진입 유지

#### 검증

- `tests/test_pipeline_gui_app.py`에 state별 진입 동작 테스트 추가
- active profile이 정상인 기존 프로젝트는 기존 흐름 유지 확인

#### 완료 기준

- 새 프로젝트, resume 대상, migration 대상, broken profile이 서로 다른 entry를 가짐
- auto-entry가 legacy 사용자 흐름을 깨지 않음

#### 남은 리스크

- `needs_migration`과 `broken_active_profile`의 경계가 흐리면 복구 UX가 혼란스러울 수 있음
- 그래서 classifier의 precedence를 먼저 lock해야 함

---

### 6.2 executor abstraction

#### 현재 상태

- `SetupExecutorAdapter` protocol이 있음
- local adapter와 fault injection adapter가 있음
- preview/result canonical promotion과 staged cleanup 경계가 있음
- 하지만 cancellation, timeout, single-flight, idempotency 같은 핵심 계약은 아직 없음

#### 목표

launcher setup state machine이 **local executor**와 **future agent executor**를 같은 규칙으로 다루도록 executor 계약을 마감합니다.

#### 범위

- adapter interface 확장
- preview/apply lifecycle rules 고정
- write allowlist와 idempotency 규칙 명시
- 실제 agent executor 구현은 다음 항목에서 진행

#### 구현 단계

1. executor contract에 `timeout`, `cancel`, `single-flight` semantics 추가
2. project별 동시에 1개의 active setup round만 허용하는 single-flight 규칙 고정
3. progress state를 사용자에게 보여줄 수 있게 `progress` payload 또는 동등한 상태 contract를 정의
4. preview 단계는 `.pipeline/setup/*.json`만 쓰고 repo 파일은 쓰지 못하게 고정
5. apply 단계의 repo write는 preview의 `planned_changes.write` allowlist 안에서만 허용
6. 같은 `setup_id`와 같은 `approved_preview_fingerprint` 재실행은 idempotent no-op 또는 동일 result 재생으로 제한
7. launcher는 active promotion을 단 한 번만 수행하고, executor는 promotion을 직접 하지 않음

#### 검증

- stale guard / promotion guard 회귀 확인
- timeout/cancel/single-flight 테스트
- write allowlist 위반 차단 테스트
- same `setup_id` 재실행 시 idempotency 테스트

#### 완료 기준

- local adapter와 future agent executor가 같은 lifecycle contract를 공유
- executor가 바뀌어도 setup state machine과 safety semantics가 유지됨

#### 남은 리스크

- progress payload를 과하게 세분화하면 setup slot이 복잡해질 수 있음
- 따라서 1차는 `queued/running/succeeded/failed/cancelled` 정도의 얇은 상태면 충분함

---

### 6.3 runtime 반영 P0

#### 현재 상태

- selected agents / role bindings / options / mode flags 저장 가능
- validation, support level, preview summary까지 launcher 안에서는 해석됨
- runtime은 여전히 fixed three-lane 전제

#### 목표

setup에서 저장한 active profile이 **단일 resolver를 통해 runtime P0에 실제 반영**되게 합니다.

#### 범위

- `active profile -> effective runtime plan` 변환기
- launcher / start script / watcher가 같은 runtime plan만 보도록 정리
- 최소 지원 profile subset만 우선 닫음

#### 구현 단계

1. resolver가 `effective_runtime_plan`을 생성
2. `start-pipeline.sh`, `watcher_core.py`, `pipeline-launcher.py`는 raw profile이 아니라 이 plan만 읽게 변경
3. P0 지원 집합을 먼저 고정
4. 권장 P0:
5. 기본 3-lane
6. `Claude + Codex`, advisory off
7. `Codex only`, self-verify warning
8. `blocked` plan은 apply와 launch 단계에서 명시 차단

#### 검증

- resolver 단위 테스트
- P0 profile별 launch smoke
- watcher dispatch 대상과 prompt owner가 plan과 일치하는지 확인

#### 완료 기준

- role binding이 launcher UI 안에만 머무르지 않고 runtime lane 구성까지 바꿈
- runtime 해석이 한 군데 resolver truth만 따라감

#### 남은 리스크

- P0에서 지원 범위를 너무 넓히면 launch path와 watcher path가 동시에 흔들릴 수 있음
- 그래서 rollout 확대는 6.8로 분리하는 편이 안전함

---

### 6.4 setup 후 재시작

#### 현재 상태

- preview 단계에서 `restart_required` 계산
- apply 성공 후 restart notice와 `지금 재시작` 버튼 표시
- 클릭 시 confirm dialog를 거쳐 기존 `_on_restart()` 흐름 호출
- 하지만 restart reconciliation에 쓸 durable marker는 없음

#### 목표

현재의 **확인형 재시작**을 `last_applied.json` 기반의 신뢰 가능한 shipped path로 마감합니다.

#### 범위

- 자동 재시작은 포함하지 않음
- restart 후 reconciliation과 stale cleanup 규칙을 먼저 닫음

#### 구현 단계

1. apply 성공 시 `last_applied.json` 기록
2. `last_applied.json`에는 `setup_id`, approved preview fingerprint, active profile fingerprint, applied time, `restart_required`, `executor`를 저장
3. launcher 재기동 후 active profile과 `last_applied.json`을 대조
4. 일치하면 success feedback을 표시
5. 불일치하면 stale result로 간주하지 말고 recovery guidance를 노출
6. cleanup은 in-flight setup과 last-applied setup을 보호하고, 나머지 artifacts만 정리

#### 검증

- restart confirmation 테스트 유지
- restart 후 reconciliation 성공/실패 테스트 추가
- stale artifact cleanup 테스트 추가

#### 완료 기준

- apply 후 수동 재시작 한 번으로 reconciliation 결과를 명확히 보여줄 수 있음
- stale result 때문에 restart notice가 잘못 되살아나지 않음

#### 남은 리스크

- 실제 프로세스 재시작은 플랫폼 의존성이 있어, 1차는 durable marker + reconciliation까지를 우선 보장하는 편이 안전함

---

### 6.5 agent-driven setup executor

#### 현재 상태

- preview/result는 local adapter가 비동기 흉내를 내며 생성
- 실제로 선택된 agent가 guide 문서나 `.pipeline` runtime slot 세팅을 적용하지는 않음

#### 목표

launcher는 orchestration만 담당하고, **선택된 agent가 setup executor로 실제 세팅 작업을 수행하는 구조**를 도입합니다.

#### 범위

- setup namespace는 `.pipeline/setup/**`로 유지
- active promotion은 여전히 launcher가 guard를 확인한 뒤 수행
- 6.2 executor contract를 그대로 따르는 agent executor 구현

#### 구현 단계

1. setup executor prompt contract를 고정
2. 선택된 executor agent가 `request.json`을 읽고 `preview.json` 작성
3. apply 승인 후 같은 executor가 allowlist 범위 안에서만 실제 변경 수행
4. 동일 `setup_id` 재실행 시 idempotent contract를 지키도록 구현
5. timeout/cancel/progress/single-flight도 local executor와 동일 semantics 유지

#### 검증

- request/preview/apply/result setup_id 일치 테스트
- stale preview canonical promotion 차단 테스트
- allowlist 밖 파일 쓰기 차단 테스트
- apply 실패 시 active profile 유지 테스트

#### 완료 기준

- executor가 local simulation이 아니라 실제 agent 선택 결과를 반영
- local executor와 agent executor가 같은 safety contract를 공유

#### 남은 리스크

- agent가 문서를 직접 바꾸는 구조는 mirror sync와 overwrite policy를 같이 점검해야 함
- preview/apply 분리와 launcher guard가 무너지지 않게 끝까지 유지해야 함

---

### 6.6 완전 자동 재시작 + 재진입

#### 현재 상태

- apply 후 confirm형 restart만 존재
- 재시작 이후 사용자를 어느 화면으로 돌려보낼지에 대한 re-entry contract는 없음

#### 목표

setup apply 성공 뒤에 **자동 재시작과 자동 재진입**을 묶어, 사용자가 추가 조작 없이 흐름을 마칠 수 있게 합니다.

#### 범위

- 1차는 opt-in 또는 명시 설정 기반
- 6.4의 durable marker와 reconciliation 위에서만 동작

#### 구현 단계

1. restart policy를 `manual_confirm` / `auto_after_apply`로 고정
2. 재시작 전에 project, mode, `last_applied.setup_id`를 보존
3. restart 완료 후 active profile과 `last_applied.json`을 대조
4. 일치하면 re-entry success 상태로 복귀
5. 실패하면 manual recovery guidance로 fallback

#### 검증

- restart orchestration mock 테스트
- restart 후 reconciliation mismatch fallback 테스트

#### 완료 기준

- 사용자가 apply 이후 추가 탐색 없이 재시작과 재진입을 마칠 수 있음
- 실패 시에도 active truth와 복구 경로가 명확함

#### 남은 리스크

- 자동 재시작은 플랫폼 차이가 있어 manual path보다 늦게 도입하는 것이 안전함

---

### 6.7 first-run wizard

#### 현재 상태

- setup mode는 launcher 내부 dedicated screen
- first-run 전용 step UI나 wizard container는 없음

#### 목표

처음 들어온 사용자가 기존 setup mode의 세부 필드를 한꺼번에 보지 않아도 되도록, **first-run 전용 안내형 UX**를 제공합니다.

#### 범위

- 새 state machine을 만드는 것이 아니라 기존 setup state machine 위에 wizard view를 얹음
- classifier 결과 중 `first_run`과 일부 `resume_setup` 경로만 대상

#### 구현 단계

1. first-run 전용 화면을 wizard 또는 stepper 형태로 설계
2. 내부 상태는 기존 form model과 setup JSON slot을 그대로 재사용
3. 마지막 단계에서 기존 preview/apply 흐름으로 연결
4. apply 성공 뒤에는 일반 setup mode 또는 home으로 자연스럽게 이관

#### 검증

- `first_run`에서는 wizard 진입
- `ready_normal`은 기존 home 진입 유지
- wizard 경유와 기존 setup mode 경유가 같은 draft/preview/apply 결과를 만드는지 확인

#### 완료 기준

- first-run 사용자가 runtime 배경지식 없이도 기본 프로필 적용까지 진행 가능
- wizard와 기존 setup mode가 서로 다른 truth를 만들지 않음

#### 남은 리스크

- wizard를 먼저 만들면 동일 로직을 두 군데에서 유지하게 될 가능성이 큼
- 따라서 classifier, onboarding, executor/state contract가 먼저 안정화돼야 함

---

### 6.8 지원 profile rollout 확대

#### 현재 상태

- setup UI는 거의 모든 조합을 입력받을 수 있음
- runtime P0 지원 집합은 아직 구현 전

#### 목표

6.3에서 닫은 `effective_runtime_plan` 위에서, **지원 profile 집합을 단계적으로 확대**합니다.

#### 범위

- resolver/plan schema는 유지
- rollout은 supported/experimental/blocked 매핑을 따름

#### 구현 단계

1. P0 지원 집합을 shipped contract로 고정
2. 다음 후보 profile을 `experimental`로 올려 검증
3. 검증이 끝난 profile만 `supported`로 승격
4. unsupported profile은 계속 `blocked` 또는 `experimental`로 명시
5. launcher 문구, watcher behavior, docs를 항상 같은 matrix로 동기화

#### 검증

- profile별 launch smoke
- support level 승격/강등에 따른 launch/apply behavior 테스트
- docs와 runtime matrix 일치 확인

#### 완료 기준

- 새 profile 지원이 resolver matrix 한 군데에서만 추가됨
- UI, launcher, watcher, docs가 서로 다른 support truth를 말하지 않음

#### 남은 리스크

- rollout 속도가 빠르면 experimental과 supported의 경계가 흐려질 수 있음
- 따라서 지원 승격은 smoke와 operator guidance까지 같이 닫는 조건으로 해야 함

---

## 7. 추천 결론

현재 가장 좋은 다음 슬라이스는 **6.0 전역 불변식 / 상태 분류 / active profile resolver 계약**입니다.

그 다음으로 붙는 슬라이스는 **6.1 최초 실행 onboarding 연결**이 가장 적절합니다.

이유:

- onboarding을 먼저 하겠다는 방향 자체는 맞지만, classifier 없이 auto-entry를 붙이면 legacy, migration, broken profile을 함께 빨아들일 수 있음
- runtime 반영 P0와 rollout 확대도 resolver가 먼저 있어야 한 truth로 묶임
- restart reconciliation도 `last_applied.json`이 없으면 안전하게 닫기 어려움

즉 지금의 실질적 우선순위는 아래처럼 보는 편이 가장 안정적입니다.

1. classifier + resolver + support-level behavior + `last_applied.json`
2. state-classified onboarding entry
3. executor contract 강화
4. runtime P0

---

## 8. 열어둘 질문

- `needs_migration`과 `broken_active_profile`의 판정 경계를 어디까지로 볼지
- executor progress를 별도 `progress.json`으로 둘지, 기존 slot 상태로 접을지
- agent-driven executor를 watcher reuse로 갈지, setup 전용 dispatcher를 둘지

현재 판단으로는 아래가 가장 안전합니다.

- classifier는 fail-open보다 fail-loud 우선
- `blocked`는 preview 허용, apply/launch 차단으로 고정
- executor progress는 얇게 시작
- runtime slot과 setup slot은 끝까지 분리
