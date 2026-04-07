# projectH 3-Agent Pipeline Operating Spec (Proposal)

**작성일**: 2026-04-03  
**성격**: 운영 설계 제안서  
**목적**: Claude / Codex / Gemini 3자 협업 자동화를 실제 파일명과 상태명 기준으로 정리

---

## 1. 이 문서의 위치

이 문서는 **현재 적용 완료된 규칙의 canonical 문서가 아니라**, 향후 watcher와 handoff 슬롯을 정리할 때 기준으로 삼을 **운영 제안서**입니다.

즉:
- 현재 shipped product contract 변경 문서가 아님
- 현재 `/work`, `/verify`, `.pipeline/README.md`를 즉시 대체하지 않음
- 3-agent 협업을 실제 운영에 옮길 때의 기준선 제안

현재 적용 상태:
- 2026-04-03 stage-3 rollout에서는 이 제안 전체를 한 번에 적용하지 않았습니다.
- 실제 반영된 범위는 아래입니다.
  - `.pipeline/claude_handoff.md` 도입
  - `.pipeline/operator_request.md` 도입
  - `.pipeline/gemini_request.md` 도입
  - `.pipeline/gemini_advice.md` 도입
  - `report/gemini/` advisory log 위치 도입
  - `start-pipeline.sh` + `watcher_core.py` 기준 Gemini pane / arbitration routing 도입
  - `codex_feedback.md`를 execution path에서 분리하고 optional scratch로 격하
- `.pipeline/codex_feedback.md`는 이제 optional scratch 또는 legacy compatibility text일 뿐, watcher execution path에는 포함되지 않습니다.

---

## 2. 현행 구조 요약

현재 canonical 자동화 흐름은 아래와 같습니다.

1. Claude가 구현
2. Claude가 `/work/<month>/<day>/...md` 작성
3. watcher가 `/work` 갱신 감지
4. Codex가 최신 `/work`와 same-day 최신 `/verify`를 기준으로 검수
5. Codex가 `/verify/<month>/<day>/...md` 작성
6. Codex가 `.pipeline/codex_feedback.md` 갱신
7. watcher가 `.pipeline/codex_feedback.md`를 보고 Claude에 전달

현행 단일 rolling slot:
- `.pipeline/codex_feedback.md`

현행 상태:
- `STATUS: implement`
- `STATUS: needs_operator`

현행 문제:
- `needs_operator`가 Claude lane까지 전달되면, 구현자가 operator 선택을 되묻게 되는 흐름이 생길 수 있음
- Codex/Gemini/operator 역할이 한 파일에 섞임
- watcher가 긴 장문 프롬프트를 직접 생성해야 하므로 중복 규칙이 많아짐

---

## 3. 제안 구조 핵심

제안 구조의 원칙은 아래와 같습니다.

- Claude는 **구현만**
- Codex는 **검수 + 다음 슬라이스 기본 결정 + canonical handoff 작성**
- Gemini는 **Codex가 못 좁힐 때만 들어오는 제3 조율자**
- 사람(operator)은 **Gemini까지 봐도 못 정할 때만 최종 개입**

핵심 변화:
- `.pipeline/codex_feedback.md` 하나에 모든 상태를 몰아넣지 않음
- Claude / Gemini / Operator가 읽는 슬롯을 분리함
- watcher는 긴 지시문 작성자보다 **역할/상태 라우터**에 가까워짐
- launcher 종료 후에도 자동 진행이 이어져야 하므로, watcher는 launcher shell background보다 tmux session 내부 hidden watcher window로 두는 편이 안정적임

---

## 4. 제안 파일 구조

### 4.1 Persistent truth

- `work/<month>/<day>/YYYY-MM-DD-<slug>.md`
  - Claude 구현 closeout
- `verify/<month>/<day>/YYYY-MM-DD-<slug>.md`
  - Codex verification closeout
- `report/YYYY-MM-DD-<slug>.md`
  - whole-project audit 또는 운영 설계 문서
- `report/gemini/YYYY-MM-DD-<slug>.md`
  - Gemini advisory log

### 4.2 Rolling automation slots

- `.pipeline/claude_handoff.md`
  - Claude만 읽음
  - 구현 가능한 단일 슬라이스만 포함
- `.pipeline/gemini_request.md`
  - Codex가 Gemini에게 자문 요청할 때 사용
- `.pipeline/gemini_advice.md`
  - Gemini가 Codex에게 남기는 추천
- `.pipeline/operator_request.md`
  - 사람이 직접 봐야 하는 결정 요청

### 4.3 Legacy slot 처리

- `.pipeline/codex_feedback.md`
  - transition 기간 동안 legacy/compatibility slot로 남길 수 있음
  - 최종적으로는 canonical execution slot에서 제외하는 편이 바람직함

---

## 5. 역할별 책임

### 5.1 Claude

역할:
- `STATUS: implement` handoff만 구현
- 구현 결과를 `/work`에 기록

허용:
- 구현
- 필요한 최소 검증
- feasibility objection 제기

비허용:
- 다음 슬라이스 자의적 선택
- `needs_operator` 해석 후 사용자에게 선택 요구
- Gemini 자문 직접 참조 후 독자 구현

읽는 문서:
- `CLAUDE.md`
- `.pipeline/claude_handoff.md`
- 필요한 최신 `/work`, `/verify` pair

### 5.2 Codex

역할:
- 최신 `/work` 검수
- same-day 최신 `/verify` 참고
- 필요한 검증 재실행
- `/verify` 작성
- 다음 슬라이스 결정
- 최종 canonical handoff 작성

허용:
- same-family current-risk reduction 자동 결정
- same-family user-visible improvement 자동 결정
- Gemini 자문 요청

비허용:
- broad whole-project audit를 `/verify`로 위장
- `needs_operator`를 Claude lane으로 전달

읽는 문서:
- `AGENTS.md`
- `work/README.md`
- `verify/README.md`
- `.pipeline/README.md`
- 최신 `/work`
- same-day 최신 `/verify`
- 필요 시 Gemini advisory

### 5.3 Gemini

역할:
- `needs_operator` 직전의 제3 조율자
- exact slice 추천 또는 family close/switch 판단

허용:
- 후보 비교
- same-family close or continue 판단
- new quality axis 전환 recommendation
- advisory log 작성
 - advisory 출력 시 file edit/write tool 우선 사용

비허용:
- 코드 수정
- `/work`, `/verify` 직접 작성
- Claude handoff 직접 확정

읽는 문서:
- `AGENTS.md`
- 별도 `GEMINI.md` 또는 Gemini 전용 지침 문서
- `.pipeline/gemini_request.md`
- 최신 `/work`
- latest relevant `/verify`

---

## 6. 첫 실행 시 watcher 판단 규칙

첫 실행은 지금처럼 **고정적으로 Claude부터**가 아니라, watcher가 상태를 보고 결정합니다.

권장 순서:

1. `.pipeline/operator_request.md`가 열려 있으면 자동 진행 중단
2. `.pipeline/gemini_request.md`가 최신이고 `.pipeline/gemini_advice.md`가 더 오래되었으면 Gemini 호출
3. 최신 `/work`가 최신 relevant `/verify`보다 새로우면 Codex 호출
4. `.pipeline/claude_handoff.md`가 있고 `STATUS: implement`이면 Claude 호출
5. 위 조건이 모두 없고 초기 상태면 seed handoff를 만들어 Claude 호출

의미:
- operator 결정이 pending이면 아무 agent도 억지로 진행하지 않음
- Gemini 요청이 있으면 Gemini가 우선
- 최신 구현이 검수보다 앞서 있으면 Codex가 우선
- 이 규칙은 `claude_handoff.md`의 mtime보다 semantic state를 우선합니다. 즉 handoff가 더 최근에 저장됐더라도 latest `/work`가 same-day latest `/verify`보다 새로우면 Codex가 먼저 붙어야 합니다.
- 구현 가능한 handoff가 있으면 Claude가 우선

---

## 7. 정상 루프

### 7.1 평소 루프

1. Claude가 `.pipeline/claude_handoff.md`를 읽음
2. Claude가 구현 후 `/work/...md`를 작성
3. watcher가 `/work` 갱신 감지
4. Codex가 최신 `/work` 검수
5. Codex가 `/verify/...md` 작성
6. Codex가 다음 슬라이스를 바로 정할 수 있으면 `.pipeline/claude_handoff.md`를 갱신
7. watcher가 Claude 호출

### 7.2 애매한 경우 루프

1. Codex가 exact next slice를 정하지 못함
2. Codex는 `.pipeline/gemini_request.md` 작성
3. watcher가 Gemini 호출
4. Gemini는 `report/gemini/...md` advisory log 작성
5. Gemini는 `.pipeline/gemini_advice.md` 작성
6. watcher가 Codex 재호출
7. Codex가 최종 `.pipeline/claude_handoff.md` 또는 `.pipeline/operator_request.md` 작성

### 7.3 진짜 사람 호출

아래 조건이면 `.pipeline/operator_request.md`를 씁니다.

- Gemini까지 봤는데도 후보 2개 이상이 genuinely tied
- 제품 방향 자체를 바꾸는 판단이 필요
- current shipped truth보다 roadmap 이동이 더 큰 라운드

이 경우:
- watcher는 Claude/Gemini/Codex 자동 호출을 멈춤
- operator만 decision을 내림

---

## 8. 상태 정의

### 8.1 `.pipeline/claude_handoff.md`

허용 상태:
- `STATUS: implement`

이 파일에는 `needs_operator`를 두지 않습니다.

### 8.2 `.pipeline/gemini_request.md`

허용 상태:
- `STATUS: request_open`
- `STATUS: request_resolved`

### 8.3 `.pipeline/gemini_advice.md`

허용 상태:
- `STATUS: advice_ready`

### 8.4 `.pipeline/operator_request.md`

허용 상태:
- `STATUS: needs_operator`
- `STATUS: resolved`

핵심 원칙:
- `needs_operator`는 **Claude가 읽는 파일에 있으면 안 됩니다**
- operator-facing stop은 반드시 별도 슬롯에서 다룹니다

---

## 9. 최소 메시지 포맷

watcher는 긴 프롬프트 대신 아래 수준의 **역할 신호 + 읽을 파일 + 상태**만 전달합니다.

### 9.1 Claude 호출

```text
ROLE: claude_implement
STATE: implement
HANDOFF: .pipeline/claude_handoff.md
READ_FIRST:
- CLAUDE.md
- .pipeline/claude_handoff.md
```

해석:
- watcher는 “한 슬라이스를 구현하라”는 장문을 쓰지 않음
- Claude는 `CLAUDE.md`와 handoff를 읽고 스스로 행동 규칙을 복원

### 9.2 Codex 호출

```text
ROLE: codex_verify
STATE: verify_pending
LATEST_WORK: work/4/3/2026-04-03-<slug>.md
LATEST_VERIFY: verify/4/3/2026-04-03-<slug>.md
READ_FIRST:
- AGENTS.md
- work/README.md
- verify/README.md
- .pipeline/README.md
```

해석:
- Codex는 최신 `/work` 검수
- 필요한 검증
- `/verify` 작성
- 다음 슬라이스 또는 Gemini request 작성

### 9.3 Gemini 호출

```text
ROLE: gemini_arbitrate
STATE: codex_needs_tiebreak
Open these files now:
- @GEMINI.md
- @.pipeline/gemini_request.md
- @AGENTS.md
- @work/4/3/2026-04-03-<slug>.md
- @verify/4/3/2026-04-03-<slug>.md
Write exactly two files using edit/write tools only:
- advisory log: report/gemini/2026-04-03-<slug>.md
- recommendation slot: .pipeline/gemini_advice.md
```

해석:
- Gemini는 candidate 비교와 exact slice recommendation만 수행
- 최종 handoff 확정은 Codex가 담당

### 9.4 Operator stop

watcher는 operator에게 자동 프롬프트를 보내지 않고, `.pipeline/operator_request.md`를 화면/알림으로만 노출합니다.

```text
ROLE: operator
STATE: needs_operator
REQUEST: .pipeline/operator_request.md
```

---

## 10. 각 슬롯의 본문 규칙

### 10.1 `.pipeline/claude_handoff.md`

반드시 포함:
- `STATUS: implement`
- 이번 라운드 단일 슬라이스
- 근거가 된 latest `/work`, latest `/verify`
- 정확한 범위
- 구현 제한
- 최소 검증

포함하면 안 되는 것:
- broad family 메뉴
- operator choice 목록
- `needs_operator`

### 10.2 `.pipeline/gemini_request.md`

반드시 포함:
- 왜 Codex가 exact slice를 못 좁혔는지
- 비교 후보 2~3개
- Codex가 이미 적용한 tie-break 순서
- Gemini에게 기대하는 출력 형식

### 10.3 `.pipeline/gemini_advice.md`

반드시 포함:
- `RECOMMEND: implement <slice>` 또는
- `RECOMMEND: close family and switch axis <axis>` 또는
- `RECOMMEND: needs_operator <one decision>`

### 10.4 `.pipeline/operator_request.md`

반드시 포함:
- stop reason
- 근거가 된 latest `/work`와 `/verify`
- Gemini recommendation 요약
- operator가 한 번에 내려야 할 결정 1개

---

## 11. Gemini advisory log 규칙

위치:
- `report/gemini/YYYY-MM-DD-<slug>.md`

필수 항목:
- 입력 pair (`/work`, `/verify`)
- candidate list
- Gemini recommendation
- 왜 그 판단이 current MVP 우선순위와 맞는지
- Codex가 참고해야 할 주의점

의미:
- canonical implementation truth 아님
- canonical verification truth 아님
- advisory/mediation log

---

## 12. 현재 구조에서의 전환 방법

### 12.1 1단계

현행 유지:
- `/work`
- `/verify`
- watcher state machine

추가:
- `.pipeline/claude_handoff.md`
- `.pipeline/gemini_request.md`
- `.pipeline/gemini_advice.md`
- `.pipeline/operator_request.md`
- `report/gemini/`

### 12.2 2단계

`codex_feedback.md`는 legacy mirror로만 유지

- watcher의 Claude 실행 기준을 `codex_feedback.md`에서 `claude_handoff.md`로 이동
- `needs_operator`는 `operator_request.md`에서만 사용

### 12.3 3단계

`codex_feedback.md`를 완전히 optional scratch로 격하

---

## 13. 권장 기본 원칙

1. 평소에는 `Claude -> Codex` 2인 루프를 유지합니다.
2. Codex가 못 좁힐 때만 `Codex -> Gemini -> Codex`로 갑니다.
3. Gemini는 자문만 하고 canonical slot을 직접 확정하지 않습니다.
4. `needs_operator`는 Claude에게 절대 직접 전달하지 않습니다.
5. 최종 구현 handoff는 항상 Claude 전용 슬롯에서만 다룹니다.

---

## 14. 한 줄 결론

projectH의 3-agent 협업 자동화는 **“자유대화형 3인조”보다 “Claude 구현 / Codex 검수 / Gemini 조율”로 분리된 구조화 협업 파이프라인**으로 설계하는 편이 가장 안전하고, 현재 `/work`·`/verify` 기반 운영과도 가장 잘 이어집니다.

현재 `start-pipeline.sh` 기준 tmux 기본 레이아웃은 좌에서 우로 `Claude | Codex | Gemini` 3열입니다.

---

## 15. Repo-local live smoke

- stage-3 이후의 권장 운영 확인은 `.pipeline/smoke-three-agent-arbitration.sh`를 쓰는 편이 맞습니다.
- 이 helper는 workspace 안의 `.pipeline/live-arb-smoke-XXXXXX/`를 custom `base_dir`로 써서:
  - smoke-local `work/4/3/...`와 `verify/4/3/...` synthetic note를 함께 만들고
  - `gemini_request -> gemini_advice -> codex follow-up`을 실제 pane에서 확인하고
  - advisory log와 최종 handoff/operator slot 생성을 한 번에 봅니다.
- `/tmp` 같은 workspace 밖 임시 경로는 Gemini write 제약 때문에 false negative를 만들 수 있으므로, smoke 기준으로는 repo-local 경로를 우선합니다.
- 성공 시 기본값으로 최근 `3`개 smoke 디렉터리만 남기고, 더 오래된 `live-arb-smoke-*` 디렉터리는 자동 정리합니다.
- 별도 수동 정리가 필요하면 `.pipeline/cleanup-old-smoke-dirs.sh`로 최근 `N`개만 남기고 오래된 smoke 디렉터리를 한 번에 정리할 수 있습니다.
