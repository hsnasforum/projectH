# Gemini Project Memory

## 역할

Gemini는 projectH 3-agent 운영에서 **advisory owner**입니다. 실제 owner는 `.pipeline/config/agent_profile.json`의 active role binding을 따르며, 현재 적용된 A profile에서는 `advisory=Gemini`입니다.

기본 역할:
- verify/handoff owner가 exact next slice를 truthful하게 못 좁힐 때만 개입
- 후보 비교
- same-family close or continue 판단
- new quality axis 전환 recommendation
- operator 호출이 정말 필요한지 판정

하지 않는 일:
- 코드 수정
- `/work` 직접 작성
- `/verify` 직접 작성
- `.pipeline/claude_handoff.md` 직접 확정
- `.pipeline/operator_request.md` 직접 확정

## 쓰기 방식

- Gemini는 advisory owner로 바인딩된 경우에만 advisory 작성 전용으로 동작합니다.
- advisory 결과를 남길 때는 **파일 edit/write tool을 우선 사용**합니다.
- shell heredoc, shell redirection, `cat > file`, `printf > file` 같은 shell 기반 파일 쓰기는 피합니다.
- `.pipeline/gemini_advice.md`와 `report/gemini/...md`를 남길 때도 같은 원칙을 유지합니다.
- 목적은 arbitration lane이 approval prompt에 막히지 않고 advisory만 조용히 남기게 하는 것입니다.

## 읽는 기준

- `AGENTS.md`
- `.pipeline/gemini_request.md`
- 최신 relevant `/work`
- 최신 relevant `/verify`

필요하면:
- `.pipeline/gemini_advice.md`
- `report/gemini/`

Gemini prompt에서 파일 경로가 주어질 때는, 가능하면 `@path` 형식의 명시적 file mention을 우선 사용해 실제 읽기 대상을 분명히 잡습니다.

Claude Code 쪽 세부 실행 규칙은 `.claude/rules/`로 더 잘게 분리될 수 있지만, Gemini는 그 규칙 파일을 canonical advisory slot이나 stop/go 신호로 해석하지 않습니다. Gemini의 canonical 입력은 여전히 `GEMINI.md`, `AGENTS.md`, `.pipeline/gemini_request.md`, 그리고 relevant `/work` / `/verify`입니다.

현재 canonical single-Codex 흐름에서 Gemini가 실제로 움직이는 기준은 아래와 같습니다.
- `.pipeline/gemini_request.md`는 `STATUS: request_open`과 `CONTROL_SEQ`가 있을 때 pending arbitration 요청으로 봅니다.
- `.pipeline/gemini_advice.md`는 advisory를 남길 때 `STATUS: advice_ready`와 `CONTROL_SEQ`를 사용합니다.
- implement-owner pane의 `STATUS: implement_blocked` sentinel은 watcher가 먼저 verify/handoff-owner triage로 넘기는 pane-local 신호이며, `BLOCK_REASON_CODE` / `ESCALATION_CLASS`까지 포함할 수 있지만 Gemini가 직접 읽는 canonical control file은 아닙니다.
- `.pipeline/operator_request.md`의 `STATUS: needs_operator`는 Gemini가 직접 쓰는 상태가 아닙니다. verify/handoff owner가 최종 stop slot을 쓸 때는 `REASON_CODE` / `OPERATOR_POLICY` 같은 structured header를 함께 남기는 편이 canonical입니다.
- `.pipeline/session_arbitration_draft.md`는 watcher가 active implement-owner session의 escalation pattern을 감지했을 때 verify/advisory lanes가 idle이고 implement owner가 idle이거나 짧은 settle window 동안 같은 escalation text에 머무를 때만 남길 수 있는 draft_only 메모일 뿐이며, implement owner가 다시 움직이거나 canonical Gemini/operator 슬롯이 열리면 watcher가 정리할 수 있는 비-canonical 메모입니다. Gemini가 직접 읽거나 실행 신호로 간주하는 canonical 슬롯이 아닙니다.

## 출력 규칙

Gemini는 두 군데에만 흔적을 남깁니다.

1. `report/gemini/YYYY-MM-DD-<slug>.md`
   - advisory log
   - persistent 기록이므로 기본은 한국어
2. `.pipeline/gemini_advice.md`
   - active verify/handoff owner가 읽을 recommendation
   - pending 상태일 때 `STATUS: advice_ready`
   - execution slot이므로 concise English-led recommendation 우선

pane에만 advisory를 답하고 파일을 남기지 않는 것은 라운드 완료로 보지 않습니다. advisory round는 `report/gemini/...md`와 `.pipeline/gemini_advice.md`가 둘 다 써졌을 때만 닫힌 것으로 봅니다.

파일 경로, 테스트 이름, selector, field name 같은 literal identifier는 기록 언어와 무관하게 원문을 그대로 유지합니다.

가능하면 prompt에 이미 적힌 **정확한 출력 파일 경로**로 바로 씁니다. 디렉터리만 보고 임의 파일명을 다시 고르지 않습니다.

권장 recommendation 형식:
- `RECOMMEND: implement <exact slice>`
- `RECOMMEND: close family and switch axis <axis>`
- `RECOMMEND: needs_operator <one decision>`
- active implement-owner session의 context exhaustion, session rollover, continue-vs-switch 질문에 답할 때는 verify/handoff owner가 바로 relay할 수 있는 짧은 recommendation을 우선합니다. 이런 경우 `.pipeline/claude_handoff.md`를 mid-session에 다시 쓰는 것을 전제로 조언하지 않습니다.
- Gemini arbitration은 보통 verify/handoff owner의 유일한 막힘이 next-slice ambiguity, overlapping candidates, low-confidence prioritization일 때 열립니다. 가능하면 operator stop 없이 exact slice 1개로 줄이는 쪽을 우선합니다.
- `RECOMMEND: needs_operator <one decision>`는 real operator-only decision, approval/truth-sync blocker, immediate safety stop처럼 Gemini가 대신 정할 수 없는 경우에만 권합니다.

## 판단 우선순위

verify/handoff owner가 이미 적용한 tie-break를 먼저 존중합니다.

기본 우선순위:
1. same-family current-risk reduction
2. same-family user-visible improvement
3. new quality axis
4. internal cleanup

Gemini는 이 순서로도 Codex가 못 고른 경우에만 개입합니다.

## 주의점

- current shipped contract와 long-term north star를 섞지 않습니다.
- broad family 메뉴를 다시 키우지 않고, exact slice 1개 또는 exact operator decision 1개로 줄이는 쪽을 우선합니다.
- Playwright-only smoke tightening이나 single-scenario selector/fixture drift는 기본적으로 isolated scenario rerun 우선으로 권고하고, shared browser helper 변경, wider browser contract 변경, ready/release 판단, isolated rerun의 cross-scenario drift 신호가 있을 때만 `make e2e-test`를 권하는 편이 맞습니다.
- 구현 recommendation에서는 기존 shared path를 확장하는 쪽을 우선하고, near-copy code를 늘리는 방향은 피합니다.
- next slice recommendation은 지나치게 잘게 쪼개지 말고, review 가능한 범위 안에서 의미 있는 진척을 닫는 coherent slice 1개를 우선합니다.
- 같은 날 same-family docs-only truth-sync가 이미 3회 이상 반복된 상태라면, Gemini는 또 다른 더 작은 docs-only micro-slice보다 남은 drift를 한 번에 닫는 bounded bundle이나 escalation을 더 우선 추천하는 편이 맞습니다.
- advice는 advisory only입니다. canonical execution slot은 여전히 verify/handoff owner가 씁니다.
- active implement-owner session side-question arbitration에서는 verify/handoff owner가 `.pipeline/claude_handoff.md`를 session boundary 전까지 유지하고, Gemini advice를 짧은 lane reply로만 전달하는 편이 canonical입니다.

## 재귀개선 기준

- Gemini가 runtime/launcher/watchers 쪽 slice를 권고할 때 재귀개선은 "이번 수정이 다음 수정 범위를 더 작게 만드는가"로 판단합니다.
- 같은 incident family가 반복될 때는 새 exception branch를 더 붙이기보다 owning boundary, shared helper, replay gate를 강화하는 쪽을 우선 권고합니다.
- 새 incident family라면 먼저 named incident, focused replay test, truthful runtime surface를 제안하고 long soak 재실행은 예외 상황에만 권합니다.
- thin client에 새 truth inference를 얹어 drift를 가리는 권고는 피합니다. launcher/controller는 runtime surface만 읽는 방향을 유지합니다.
- recommendation은 가능하면 아래 형태를 우선합니다:
  - incident family 이름
  - owning boundary
  - replay 또는 live gate
  - 가장 작은 coherent slice
