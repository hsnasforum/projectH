"""Pipeline Agent Orchestration Guide — canonical default text."""

DEFAULT_GUIDE = """\
# Pipeline Agent Orchestration Guide

## 이 문서의 목적

이 문서는 이 파이프라인에서 Claude, Codex, Gemini가 어떤 순서와 조건으로 호출되는지 설명합니다.
핵심은 "누가 언제 일하고, 어떤 파일을 읽고, 어떤 파일을 써야 하는지"를 분명히 하는 것입니다.

## 기본 실행 순서

Claude -> Codex -> (필요 시 Gemini -> Codex) -> Claude

1. Claude가 구현을 수행합니다.
2. Codex가 최신 구현 결과를 검증합니다.
3. Codex가 다음 작업을 명확히 정할 수 있으면 다시 Claude에게 넘깁니다.
4. Codex가 혼자 결정하기 어렵다면 Gemini에게 자문을 요청합니다.
5. Gemini가 advisory를 남기면 Codex가 다시 들어와 최종 결론을 내립니다.

Gemini는 항상 호출되는 기본 단계가 아닙니다.
Codex가 tie-break가 필요하다고 판단할 때만 호출됩니다.

## 시작 시 첫 에이전트 결정 (newest-valid-control 기준)

파이프라인이 시작/재시작될 때 watcher는 **가장 최신의 유효한 control 슬롯**을 기준으로 첫 agent를 결정합니다.
오래된 control 파일은 더 새로운 유효한 슬롯이 존재하면 비활성(inactive/stale) 상태로 무시됩니다.

1. 최신 유효 슬롯이 operator_request (STATUS: needs_operator)이면 -> operator 대기
2. 최신 유효 슬롯이 gemini_request (STATUS: request_open)이면 -> Gemini
3. 최신 유효 슬롯이 gemini_advice (STATUS: advice_ready)이면 -> Codex follow-up
4. 최신 /work가 same-day /verify보다 새로우면 -> Codex (미검증 구현 우선 검증)
5. 최신 유효 슬롯이 claude_handoff (STATUS: implement)이면 -> Claude
6. 모든 파일이 비어 있으면 -> Claude (초기 상태)
7. 그 외 -> Codex

implement handoff가 있어도 최신 /work가 아직 검증되지 않았다면 Codex가 먼저 들어갑니다.
오래된 pending 파일이 남아 있어도 더 새로운 유효 슬롯이 있으면 오래된 파일은 무시됩니다.

## 에이전트별 역할과 호출 조건

### Claude (구현)

호출 조건:
- .pipeline/claude_handoff.md의 STATUS가 implement
- operator stop 상태가 아님
- 최신 /work가 /verify 없이 남아 있지 않음

역할:
- 지정된 정확한 슬라이스 구현
- 구현 closeout을 /work/...에 기록

implement_blocked:
- 핸드오프를 실행할 수 없으면 Claude는 STATUS: implement_blocked를 emit합니다
- watcher가 implement_blocked를 감지하면 자동으로 Codex triage로 전환합니다
- operator stop을 직접 열지 않고, Codex가 재분류하여 다음 행동을 결정합니다

쓰면 안 되는 파일:
- .pipeline/gemini_request.md
- .pipeline/gemini_advice.md
- .pipeline/operator_request.md

### Codex (검증)

호출 조건:
- Claude 구현 다음 (기본)
- 최신 /work가 /verify 없이 남아 있을 때
- Gemini advice 이후 follow-up이 필요할 때

역할:
- 최신 /work를 먼저 읽고, same-day /verify도 함께 읽음
- 검증 rerun 후 /verify/...를 남기거나 갱신
- 다음 Claude 슬라이스를 하나 정함
- 애매하면 Gemini 자문 요청
- 자동 진행 불가능하면 operator stop 선언

결정 출력 (셋 중 하나):
- .pipeline/claude_handoff.md
- .pipeline/gemini_request.md
- .pipeline/operator_request.md

### Gemini (조언)

호출 조건:
- .pipeline/gemini_request.md의 STATUS가 request_open이고
- operator stop 상태가 아닐 때

역할:
- tie-break용 분석과 자문 제공

쓸 수 있는 출력:
- .pipeline/gemini_advice.md
- report/gemini/...md

쓰면 안 되는 파일:
- .pipeline/claude_handoff.md
- .pipeline/operator_request.md

## Gemini advice 이후 흐름

Gemini가 .pipeline/gemini_advice.md를 STATUS: advice_ready로 갱신하면 watcher가 Codex follow-up을 재호출합니다.

Codex -> gemini_request.md -> Gemini -> gemini_advice.md -> watcher -> Codex follow-up

## control file 우선순위 (newest-valid-control)

watcher는 가장 최신의 유효한 control 슬롯만 실행 입력으로 사용합니다.
오래된 control 파일은 비활성(inactive/stale) 상태로, 더 새로운 유효 슬롯이 존재하면 무시됩니다.

- .pipeline/claude_handoff.md -> Claude 실행
- .pipeline/gemini_request.md -> Gemini 실행
- .pipeline/gemini_advice.md -> Codex follow-up
- .pipeline/operator_request.md -> 자동 진행 중단

.pipeline 내용과 /work, /verify가 충돌하면 /work와 /verify를 우선합니다.

## 파일 의미

### /work
Claude 구현 closeout의 persistent 기록.
무엇을 바꿨는지, 왜, 어떤 검증을 했는지, 남은 리스크.

### /verify
Codex 검증 기록.
/work 내용이 실제 코드와 맞는지, 검증 rerun 결과, 다음 슬라이스 선택 근거.

### report/gemini
Gemini advisory/mediation 로그.

### .pipeline 슬롯
rolling handoff 슬롯. persistent truth는 /work와 /verify에 있습니다.

주요 슬롯:
- claude_handoff.md, gemini_request.md, gemini_advice.md, operator_request.md

Legacy/optional:
- codex_feedback.md, gpt_prompt.md (현재 canonical path에서 사용 안 함)

## 슬라이스 선택 원칙

Codex 기본 우선순위:
1. 같은 계열 현재 리스크 감소
2. 같은 계열 사용자-visible 개선
3. 새로운 품질 축
4. 내부 cleanup

정말 애매할 때만 Gemini를 부르고, 그래도 위험하면 operator stop.

## 자동 중단 조건

.pipeline/operator_request.md는 반드시 STATUS: needs_operator를 포함해야 합니다.
이 STATUS가 없으면 watcher는 operator stop으로 인식하지 않습니다.

파일에는 최소한:
- 왜 멈추는지
- 어떤 /work, /verify 기준으로 멈췄는지
- operator가 무엇을 결정해야 하는지

## implement_blocked 자동 전환

Claude가 STATUS: implement_blocked를 emit하면:
- watcher가 이를 감지하고 자동으로 Codex triage 라운드를 시작합니다
- operator stop을 직접 열지 않습니다
- Codex가 block 사유를 분석하고 다음 슬라이스를 재선택하거나, 필요하면 operator stop 또는 Gemini 자문을 결정합니다

## 운영 원칙

- Claude는 구현, Codex는 검증+다음 결정, Gemini는 advisory only.
- persistent truth는 /work와 /verify.
- .pipeline은 실행 슬롯이지 영구 기록이 아닙니다.
- 최신 /work가 미검증이면 implement handoff가 있어도 Codex가 먼저.
- 애매한 상태를 숨기지 말고 정직하게 기록합니다.
"""
