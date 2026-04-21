"""Pipeline Agent Orchestration Guide — canonical default text."""

DEFAULT_GUIDE = """\
# Pipeline Agent Orchestration Guide

## 이 문서의 목적

이 문서는 이 파이프라인에서 active `role_bindings` 기준으로 implement owner, verify/handoff owner, advisory owner가
어떤 순서와 조건으로 호출되는지 설명합니다.
핵심은 "누가 언제 일하고, 어떤 파일을 읽고, 어떤 파일을 써야 하는지"를 역할 기준으로 분명히 하는 것입니다.
Historical filename은 유지됩니다. 예를 들어 `.pipeline/claude_handoff.md`는 여전히 implement control slot 이름이지만,
실제 implement owner는 active profile이 정합니다.
runtime adapter는 physical lane 세 개(`Claude`, `Codex`, `Gemini`)를 고정 순서로 모두 들고 있으며,
현재 profile은 각 lane의 `enabled` 여부와 `roles`만 바꿉니다. UI와 launcher는 fixed owner를 재추론하지 않고 이 plan을 그대로 읽는 편이 맞습니다.

지원 수준도 특정 agent 이름 조합 whitelist가 아니라 profile shape로 판정합니다.
- 3-lane + implement/verify distinct + advisory enabled: `supported`
- 2-lane + implement/verify distinct + advisory disabled: `supported`
- 1-lane self-verify: `experimental`
- 그 외 validation 통과 조합: `experimental`
- validation 실패/불일치: `blocked` 또는 `broken`

## 기본 실행 순서

implement owner -> verify/handoff owner -> (필요 시 advisory owner -> verify/handoff owner) -> implement owner

1. implement owner가 구현을 수행합니다.
2. verify/handoff owner가 최신 구현 결과를 검증합니다.
3. verify/handoff owner가 다음 작업을 명확히 정할 수 있으면 다시 implement owner에게 넘깁니다.
4. verify/handoff owner가 혼자 결정하기 어렵다면 advisory owner에게 자문을 요청합니다.
5. advisory owner가 advisory를 남기면 verify/handoff owner가 다시 들어와 최종 결론을 내립니다.

advisory owner는 항상 호출되는 기본 단계가 아닙니다.
verify/handoff owner가 tie-break가 필요하다고 판단할 때만 호출됩니다.

## turbo-lite wrapper 순서

필요할 때만 아래 얇은 wrapper를 순서대로 사용합니다.

1. `onboard-lite` — repo나 subsystem이 낯설 때 실제 run/test entrypoint와 ownership boundary를 먼저 파악
2. implement owner 구현
3. `finalize-lite` — 구현 말미에 focused verification, doc sync 필요 여부, `/work` closeout readiness 점검
4. `round-handoff` — verification truth 재대조와 `/verify` 갱신이 필요할 때 사용
5. `next-slice-triage` — `/work`와 `/verify` truth가 이미 맞은 뒤 exact next slice만 좁힐 때 사용

이 wrapper들은 서로의 책임을 대신하지 않습니다.
예를 들어 `finalize-lite`가 `/verify`를 쓰거나 next slice를 고르지 않고,
`next-slice-triage`가 verification rerun을 다시 수행하지 않습니다.

## 시작 시 첫 에이전트 결정 (newest-valid-control 기준)

파이프라인이 시작/재시작될 때 watcher는 **가장 최신의 유효한 control 슬롯**을 기준으로 첫 agent를 결정합니다.
우선순위는 `CONTROL_SEQ`가 먼저이고, `CONTROL_SEQ`가 없을 때만 mtime을 보조로 씁니다.
오래된 control 파일은 더 새로운 유효한 슬롯이 존재하면 비활성(inactive/stale) 상태로 무시됩니다.

1. 최신 유효 슬롯이 operator_request (STATUS: needs_operator)이면 -> operator wait
2. 최신 유효 슬롯이 gemini_request (STATUS: request_open)이면 -> advisory request
3. 최신 유효 슬롯이 gemini_advice (STATUS: advice_ready)이면 -> verify follow-up
4. 최신 /work가 same-day /verify보다 새로우면 -> verify/handoff owner (미검증 구현 우선 검증)
5. 최신 유효 슬롯이 claude_handoff (STATUS: implement)이면 -> implement owner
6. 모든 파일이 비어 있으면 -> implement owner (초기 상태)
7. 그 외 -> verify/handoff owner

implement handoff가 있어도 최신 /work가 아직 검증되지 않았다면 verify/handoff owner가 먼저 들어갑니다.
오래된 pending 파일이 남아 있어도 더 새로운 유효 슬롯이 있으면 오래된 파일은 무시됩니다.

## 역할별 호출 조건

### Implement owner

호출 조건:
- .pipeline/claude_handoff.md의 STATUS가 implement
- operator stop 상태가 아님
- 최신 /work가 /verify 없이 남아 있지 않음

역할:
- 지정된 정확한 슬라이스 구현
- 구현 closeout을 /work/...에 기록
- implement lane은 bounded 파일 수정 + /work closeout에서 멈춤
- implement lane에서 commit, push, branch publish, PR 생성은 하지 않음

implement_blocked:
- 핸드오프를 실행할 수 없으면 implement owner는 STATUS: implement_blocked를 emit합니다
- watcher가 implement_blocked를 감지하면 자동으로 verify/handoff owner triage로 전환합니다
- operator stop을 직접 열지 않고, verify/handoff owner가 재분류하여 다음 행동을 결정합니다
- sentinel field name은 compatibility 때문에 여전히 `codex_triage`를 쓸 수 있지만, 실제 owner는 active verify/handoff owner입니다

쓰면 안 되는 파일:
- .pipeline/gemini_request.md
- .pipeline/gemini_advice.md
- .pipeline/operator_request.md

### Verify/handoff owner

호출 조건:
- implement owner 구현 다음 (기본)
- 최신 /work가 /verify 없이 남아 있을 때
- advisory owner advice 이후 follow-up이 필요할 때

역할:
- 최신 /work를 먼저 읽고, same-day /verify도 함께 읽음
- 검증 rerun 후 /verify/...를 남기거나 갱신
- 다음 implement 슬라이스를 하나 정함
- 애매하면 advisory owner 자문 요청
- 자동 진행 불가능하면 operator stop 선언

검증 라운드 종료 조건:
- pane 안 reasoning만 남기거나 control slot만 먼저 갱신하는 것으로는 round가 닫히지 않음
- verify/handoff owner는 /verify를 먼저 남기거나 갱신한 뒤에만 다음 control slot을 쓰는 편이 canonical임

결정 출력 (셋 중 하나):
- .pipeline/claude_handoff.md
- .pipeline/gemini_request.md
- .pipeline/operator_request.md

### Advisory owner

호출 조건:
- .pipeline/gemini_request.md의 STATUS가 request_open이고
- operator stop 상태가 아닐 때

역할:
- tie-break용 분석과 자문 제공

쓸 수 있는 출력:
- .pipeline/gemini_advice.md
- report/gemini/...md

advisory round 종료 조건:
- pane-only 답변만으로는 advisory round가 닫히지 않음
- advisory owner는 report/gemini/...md와 .pipeline/gemini_advice.md를 둘 다 남겨야 canonical closeout으로 봄

쓰면 안 되는 파일:
- .pipeline/claude_handoff.md
- .pipeline/operator_request.md

## advisory 이후 흐름

advisory owner가 .pipeline/gemini_advice.md를 STATUS: advice_ready로 갱신하면 watcher가 verify follow-up을 재호출합니다.

verify/handoff owner -> gemini_request.md -> advisory owner -> gemini_advice.md -> watcher -> verify follow-up

## control file 우선순위 (newest-valid-control)

watcher는 `CONTROL_SEQ` 우선 / mtime 보조 기준의 가장 최신 유효 control 슬롯만 실행 입력으로 사용합니다.
오래된 control 파일은 비활성(inactive/stale) 상태로, 더 새로운 유효 슬롯이 존재하면 무시됩니다.

- .pipeline/claude_handoff.md -> implement handoff
- .pipeline/gemini_request.md -> advisory request
- .pipeline/gemini_advice.md -> verify follow-up
- .pipeline/operator_request.md -> operator wait

.pipeline 내용과 /work, /verify가 충돌하면 /work와 /verify를 우선합니다.

## 파일 의미

### /work
implement owner closeout의 persistent 기록.
무엇을 바꿨는지, 왜, 어떤 검증을 했는지, 남은 리스크.

### /verify
verify/handoff owner 검증 기록.
/work 내용이 실제 코드와 맞는지, 검증 rerun 결과, 다음 슬라이스 선택 근거.

### report/gemini
advisory owner advisory/mediation 로그.

### .pipeline 슬롯
rolling handoff 슬롯. persistent truth는 /work와 /verify에 있습니다.

주요 슬롯:
- claude_handoff.md, gemini_request.md, gemini_advice.md, operator_request.md

Legacy/optional:
- codex_feedback.md, gpt_prompt.md (현재 canonical path에서 사용 안 함)

## 슬라이스 선택 원칙

verify/handoff owner 기본 우선순위:
1. 같은 계열 현재 리스크 감소
2. 같은 계열 사용자-visible 개선
3. 새로운 품질 축
4. 내부 cleanup

정말 애매할 때만 advisory owner를 부르고, 그래도 위험하면 operator stop.

## 자동 중단 조건

.pipeline/operator_request.md는 반드시 STATUS: needs_operator를 포함해야 합니다.
이 STATUS가 없으면 watcher는 operator stop으로 인식하지 않습니다.

파일에는 최소한:
- 왜 멈추는지
- 어떤 /work, /verify 기준으로 멈췄는지
- operator가 무엇을 결정해야 하는지

## implement_blocked 자동 전환

implement owner가 STATUS: implement_blocked를 emit하면:
- watcher가 이를 감지하고 자동으로 verify/handoff owner triage 라운드를 시작합니다
- operator stop을 직접 열지 않습니다
- verify/handoff owner가 block 사유를 분석하고 다음 슬라이스를 재선택하거나, 필요하면 operator stop 또는 advisory 자문을 결정합니다

## 운영 원칙

- owner는 active `role_bindings`를 따릅니다. fixed agent 이름보다 role이 우선입니다.
- persistent truth는 /work와 /verify.
- .pipeline은 실행 슬롯이지 영구 기록이 아닙니다.
- 최신 /work가 미검증이면 implement handoff가 있어도 verify/handoff owner가 먼저.
- 애매한 상태를 숨기지 말고 정직하게 기록합니다.
"""
