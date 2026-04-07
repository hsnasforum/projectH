# projectH 제품 트랙 / 플랫폼 트랙 분리 제안 (검토용 초안)

**작성일**: 2026-04-07  
**성격**: 검토용 제안서  
**목적**: 현재 `projectH`에서 제품 완성과 플랫폼 투자를 같은 저장소 안에서 어떻게 병행할지, 그리고 각 축의 1차 완료선을 어디에 둘지 정리

---

## 1. 이 문서의 위치

이 문서는 **현재 canonical 운영 규칙 문서가 아닙니다.**

즉:
- 아직 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에 고정하지 않음
- 아직 `plandoc/`의 staged roadmap을 수정하지 않음
- 먼저 `report/`에서 운영 방향을 검토하고, 승인 후에만 상위 규칙 문서로 승격

---

## 2. 현재 판단

현재 `projectH`에는 서로 다른 성격의 두 축이 동시에 존재합니다.

1. **제품 트랙**
   - 현재 shipped contract에 직접 연결되는 축
   - `app.web` 문서 비서 본체
   - 문서 읽기 / 요약 / 검색 / 승인 저장 / evidence / web investigation secondary mode / history-card smoke

2. **플랫폼 트랙**
   - 다른 프로젝트에도 재사용 가능한 운영 자동화 축
   - Claude / Codex / Gemini lane orchestration
   - watcher draft / arbitration / settled-lane 감지
   - Windows / WSL / packaged exe 운영 골격

현재 논의 기준에서는 **플랫폼 트랙을 “과한 우회”로 보지 않습니다.**
오히려 아래 이유로 **의도된 투자**로 봅니다.

- Claude / Codex / Gemini lane은 추후 다른 프로젝트에도 옮겨 쓸 수 있는 자동화 자산임
- watcher draft 규칙은 사람이 덜 개입하도록 하려는 운영 신뢰도 작업임
- Windows / WSL / packaged exe 골격은 지금 단계에서도 로컬 실사용 프로토타입으로 의미가 있음

---

## 3. 왜 지금 분리가 필요한가

현재 저장소에서 속도 저하처럼 보이는 부분은 “플랫폼 투자 자체”보다도, **제품 축과 플랫폼 축이 한 덩어리처럼 해석되는 것**에서 나옵니다.

문제가 되는 지점:
- 제품 family를 닫는 라운드와 watcher/arbitration 규칙 보강 라운드가 같은 우선순위처럼 섞여 보임
- 릴리즈 준비 추정 시 `app.web` shipped contract와 pipeline/controller/tooling 안정화가 한 일정 안에서 같이 계산됨
- 나중에 전략 문서를 고정할 때 “무엇이 제품 요구사항이고 무엇이 운영/플랫폼 자산인지” 경계가 흐려질 수 있음

따라서 지금 필요한 것은 “플랫폼 투자를 줄이기”가 아니라, **두 축을 명시적으로 분리하고 각 축의 1차 완료선을 정하는 것**입니다.

---

## 4. 제안 구조

### 4.1 제품 트랙

**정의**  
현재 release candidate와 직접 연결되는 shipped contract 축

**범위**
- `app.web`
- `core/`, `tools/`, `storage/`, `model_adapter/` 중 현재 문서 비서 루프에 직접 연결되는 부분
- approval / evidence / response-origin / history-card / web investigation secondary mode
- `tests.test_web_app`
- `tests.test_http_integration`
- `e2e/tests/web-smoke.spec.mjs`

**1차 완료선**
- `app.web` 기준 release candidate를 자신 있게 설명할 수 있음
- 주요 browser-visible contract가 smoke / focused unittest 기준으로 닫혀 있음
- current shipped contract와 문서(`README`, `PRODUCT_SPEC`, `ACCEPTANCE_CRITERIA`, `MILESTONES`, `TASK_BACKLOG`)가 큰 모순 없이 맞음
- 릴리즈 판단 시 pipeline/controller/operator tooling을 게이트 안으로 끌어들이지 않아도 됨

### 4.2 플랫폼 트랙

**정의**  
현재 제품을 넘어서도 재사용 가능한 운영 자동화 / 로컬 실행 기반 축

**범위**
- `pipeline_gui/`
- `watcher_core.py`
- `.pipeline/` slot orchestration
- Claude / Codex / Gemini lane 운영 규칙
- `controller.server`
- `windows-launchers/`
- Windows / WSL / packaged exe 실행 골격

**1차 완료선**
- watcher가 canonical 슬롯을 오염시키지 않고 draft-only mediation을 안전하게 생성함
- mid-session Claude side question은 handoff rewrite 없이 relay 구조로 정리됨
- Windows / WSL / packaged exe 기준으로 1차 실행 흐름과 fallback 경로가 설명 가능함
- 다른 프로젝트로 옮길 때 lane / watcher / draft 구조를 재사용할 수 있을 정도로 규칙이 고정됨

---

## 5. 현재 시점 평가

### 5.1 제품 트랙

현재 상태는 **release candidate 후반부**에 가깝습니다.

근거:
- `app.web` 본체는 이미 문서 비서 MVP로 usable한 상태
- history-card / latest-update / entity-card smoke family가 매우 많이 누적됨
- current shipped contract와 docs sync도 여러 차례 truth-sync가 진행됨

남은 일:
- 남아 있는 exact smoke family를 계속 닫기
- release gate 기준에서 포함/제외 범위를 더 흔들지 않기
- 필요 시 release-check 관점의 최종 truth reconciliation

### 5.2 플랫폼 트랙

현재 상태는 **1차 골격이 잡힌 프로토타입**으로 보는 것이 맞습니다.

근거:
- Claude / Codex / Gemini lane이 실제로 돌아감
- watcher가 `session_arbitration_draft.md`를 non-canonical draft-only로 쓰는 구조가 들어감
- settled lanes / cooldown / stale clear / scrollback suppression / phrase variants까지 기본적인 운영 리스크가 상당 부분 줄어듦
- Windows / WSL / packaged exe도 시행착오가 많았지만 “어디가 문제였는지”를 repo 관점에서 추적 가능한 수준으로 올라옴

남은 일:
- lane 운영을 더 많은 실제 세션에서 관찰
- packaged exe / localhost / runtime staging 같은 운영 예외를 1차 프로토타입 수준에서 더 매끈하게 다듬기
- 이후에야 다른 프로젝트 재사용성을 더 강하게 검증

---

## 6. 제안하는 운영 원칙

### 6.1 제품 진행 속도를 볼 때

`app.web` release candidate 일정은 **제품 트랙 기준으로만** 본다.

즉:
- `pipeline_gui`
- `controller`
- `windows-launchers`
- watcher arbitration 보강

이 축은 기본적으로 제품 release gate 바깥에서 본다.

### 6.2 플랫폼 투자를 볼 때

플랫폼 트랙은 “나중에 하면 되는 잡일”이 아니라,
**다른 프로젝트로 전이 가능한 운영 자산**이라는 전제로 유지한다.

즉:
- lane orchestration
- draft-only watcher mediation
- packaged exe / WSL 골격

은 별도 가치가 있는 축으로 인정한다.

### 6.3 실제 우선순위 해석

따라서 앞으로 우선순위는 아래처럼 읽는 것이 적절합니다.

1. 제품 트랙 안에서는 shipped user-visible family를 닫는 슬라이스를 우선
2. 플랫폼 트랙 안에서는 canonical slot safety와 운영 개입 감소 효과가 큰 슬라이스를 우선
3. 두 축을 한 라운드에서 섞더라도, closeout/보고에서는 어느 축의 작업이었는지 명시

---

## 7. 지금 승인되면 나중에 반영할 문서

이 초안이 승인되면 다음 문서에 반영하는 것이 자연스럽습니다.

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- 필요 시 `plandoc/`의 staged roadmap 문서

반영 방향:
- `current shipped contract`는 제품 트랙 기준으로 유지
- `platform track`을 별도 명시
- 각 축의 1차 완료선과 해석 기준을 짧게 고정

---

## 8. 아직 열어 둔 질문

1. 플랫폼 트랙을 언제부터 `report` 수준이 아니라 상위 규칙 문서로 승격할지
2. release candidate 설명 시 `controller`를 제품 부속 도구로 볼지, 플랫폼 도구로 볼지
3. `pipeline_gui`와 `windows-launchers`를 한 묶음의 “operator tooling”으로 계속 볼지
4. 제품/플랫폼 두 축을 `/work`, `/verify` 제목이나 closeout 문구에도 명시할지

---

## 9. 제안 결론

현재 `projectH`는 단순히 “제품 하나”만 만드는 저장소가 아니라,

- **문서 비서 제품 트랙**
- **재사용 가능한 로컬 운영 자동화 플랫폼 트랙**

을 함께 키우는 저장소로 보는 편이 더 truthful합니다.

따라서 지금 필요한 것은 플랫폼 투자를 줄이자는 판단이 아니라,
**그 투자가 어떤 축의 일인지 명시하고, 제품 완성 일정과 플랫폼 성숙 일정을 분리해서 해석하는 것**입니다.

이 문서가 승인되면, 그때 비로소 상위 규칙 문서에 짧게 승격하는 것이 적절합니다.
