# /work 정책

`/work`는 projectH에서 구현 중심 라운드 종료 기록을 남기는 closeout 디렉터리입니다.
검증 재실행과 truth 재대조 결과는 sibling 디렉터리인 `/verify`에 별도로 남깁니다.

## tracked 대상

- `work/<month>/<day>/YYYY-MM-DD-<slug>.md` 형식의 closeout 메모
- 이 파일처럼 `/work` 운영 규칙을 설명하는 기준 문서

## 작성 원칙

- 작업 시작 시에는 먼저 `work/<현재월>/<현재일>/` 아래의 md 파일 중 가장 최근 문서를 확인합니다.
- 오늘 문서가 없으면 전날 날짜 폴더의 `/work` 문서 중 최신 파일을 확인하고 이어받습니다.
- 종료 기록을 저장할 때는 `work/<현재월>/<현재일>/` 폴더가 없으면 먼저 생성합니다.
- 한 라운드가 끝날 때 실제 변경, 실제 검증, 남은 리스크를 한 파일에 정리합니다.
- 한 라운드는 가능한 한 하나의 의미 있는 bounded slice를 닫는 단위로 남기고, 같은 파일/검증 축을 공유하는 작업을 불필요하게 micro-slice 여러 개로 쪼개지 않습니다.
- 구현이 없는 verification-only handoff는 `/work`가 아니라 `/verify`에 남깁니다.
- `/work` closeout은 기본적으로 한국어로 적습니다.
- 다만 파일 경로, 테스트 이름, selector, field name, literal code identifier는 원문을 그대로 유지합니다.
- 새 closeout에는 아래 섹션을 이 순서로 둡니다:
  - `## 변경 파일`
  - `## 사용 skill`
  - `## 변경 이유`
  - `## 핵심 변경`
  - `## 검증`
  - `## 남은 리스크`
- `## 사용 skill` 섹션은 항상 두고, 실제 사용한 skill이 없으면 `- 없음`으로 적습니다.
- 실행하지 않은 명령이나 검증 결과를 추측으로 적지 않습니다.
- `.codex/config.toml` 변경이 포함된 라운드는 그 파일이 로컬 설정이며 기본적으로 git tracked 대상이 아니라는 점을 메모에 적습니다.
- Playwright-only smoke tightening, selector drift, single-scenario fixture update 같은 좁은 브라우저 변경은 `cd e2e && npx playwright test ... -g "<scenario>" --reporter=line` 같은 isolated rerun을 먼저 적고, `make e2e-test`를 생략했다면 왜 full browser suite가 이번 라운드에 과한지 `## 검증`에 명시합니다.

## tracked 하지 않는 대상

- 임시 스크립트, scratch 메모, 로그, one-off 출력
- 이런 파일은 `tmp/` 또는 `work/local/` 아래에 두고 commit 대상에서 제외합니다.
- whole-project audit이나 milestone review는 `/work`가 아니라 `report/`에 두는 편이 더 적절합니다.

## 권장 예시

- tracked closeout: `work/3/26/2026-03-26-codex-work-log-adoption.md`
- local scratch: `work/local/<topic>.md`, `work/local/<topic>.log`

## 운영 메모

- 이 저장소의 `/work`는 finance 저장소의 closeout 패턴을 참조하되, product docs 대신 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.codex/config.toml`, repo skills/agents와의 정합성을 우선합니다.
- helper-agent, skill, Codex operator flow가 바뀌면 `/work`에도 그 라운드의 이유와 영향 범위를 남겨 후속 작업자가 문맥을 이어받을 수 있게 합니다.
- 구현 closeout에는 가능하면 기존 shared path를 재사용해 중복 코드를 늘리지 않았는지, 또는 왜 예외가 필요했는지를 짧게 드러내는 편이 좋습니다.
- `/work`가 구현 closeout, `/verify`가 검증 결과라는 경계가 바뀌면 두 README를 같은 라운드에서 함께 갱신합니다.
- `.pipeline/claude_handoff.md`는 현재 implement control slot의 rolling 최신 파일입니다. 파일명은 역사적 호환을 위해 유지되며, 구현 truth는 항상 최신 `/work`에 남기고 `.pipeline`은 그 내용을 넘겨주기 위한 보조 수단으로만 씁니다.
- `.pipeline` execution/control 슬롯은 `/work`와 달리 기본적으로 영어 중심 실행 지시를 유지하는 편이 맞습니다.
- canonical control slot은 pending일 때 `CONTROL_SEQ`를 같이 써서 newest-valid-control 판정을 `CONTROL_SEQ` 우선 / `mtime` 보조로 맞추는 편이 맞습니다.
- `.pipeline/gemini_request.md`와 `.pipeline/gemini_advice.md`는 현재 Gemini arbitration 슬롯입니다. 구현 truth를 대체하지 않습니다.
- `.pipeline/session_arbitration_draft.md`는 watcher가 active implement-owner session의 escalation pattern을 감지했고 verify/advisory lanes가 idle이며 implement owner가 idle이거나 짧게 settle된 상태일 때만 남길 수 있는 draft_only 메모이며, 구현 truth나 canonical arbitration 슬롯을 대체하지 않습니다. resolved 조건이 생기면 watcher가 정리할 수 있고, 같은 fingerprint는 짧은 cooldown 동안 반복 생성하지 않습니다.
- `.pipeline/operator_request.md`는 현재 operator 정지용 rolling 최신 슬롯입니다. 이 파일은 active implement owner가 구현 입력으로 읽지 않습니다.
- `.pipeline/codex_feedback.md`는 optional scratch 또는 legacy compatibility text일 뿐이며, 실행 신호로는 쓰지 않습니다.
- active implement-owner session에서 context exhaustion, session rollover, continue-vs-switch 같은 side question 때문에 Gemini arbitration이 열리더라도, active verify/handoff owner는 답을 짧은 lane reply로만 relay하고 `.pipeline/claude_handoff.md`는 그 세션이 끝날 때까지 유지하는 편이 맞습니다. 그래야 나중에 실제 구현 결과를 round-start handoff와 다시 대조할 수 있습니다.
- active implement owner는 보통 `.pipeline/claude_handoff.md`가 `STATUS: implement`일 때만 새 구현 `/work`를 남깁니다. 최신 control 파일이 `.pipeline/operator_request.md`라면 새 `/work` closeout을 억지로 만들지 않습니다.
- implement-owner round는 bounded 파일 수정과 `/work` closeout에서 끝나는 편이 맞습니다. implement lane에서 commit, push, branch publish, PR 생성까지 같이 진행하지 않습니다.
- 최신 control 파일이 `.pipeline/gemini_request.md` 또는 `.pipeline/gemini_advice.md`라면, 그 arbitration이 끝날 때까지 새 `/work` closeout을 억지로 만들지 않습니다.
- active `STATUS: implement` handoff가 blocked라면 active implement owner는 새 `/work` closeout 대신 pane-local `STATUS: implement_blocked` + `BLOCK_REASON_CODE` + `ESCALATION_CLASS` sentinel로 verify/handoff-owner triage를 기다리는 편이 맞습니다.
- `STATUS: needs_operator` stop request는 bare stop line 하나로 끝내지 않는 편이 맞습니다. 최소한 `CONTROL_SEQ`, `REASON_CODE`, `OPERATOR_POLICY`, `DECISION_CLASS`, `DECISION_REQUIRED`, `BASED_ON_WORK`, `BASED_ON_VERIFY`와 함께 왜 멈췄는지, operator가 다음에 무엇을 정해야 하는지는 `.pipeline/operator_request.md`에 남겨야 automation이 멈춘 이유를 나중에 다시 추적할 수 있습니다.
- Codex는 latest `/work`와 `/verify`가 한 family를 truthfully 닫았을 때 같은 family의 가장 작은 current-risk reduction을 먼저 자동 확정할 수 있습니다. 다음 슬라이스를 매번 operator가 직접 고를 필요는 없습니다.
- 다만 Codex가 next-slice ambiguity, overlapping candidates, low-confidence prioritization 때문에 바로 확정하지 못한 경우에는 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`를 먼저 여는 편이 맞습니다.
- 따라서 `.pipeline/operator_request.md`는 단순한 우선순위 망설임이 아니라 real operator-only decision, approval/truth-sync blocker, immediate safety stop, 또는 Gemini advice 이후에도 exact slice를 못 좁힌 경우를 의미하는 편이 맞습니다.
- 따라서 `/work` closeout도 다음 우선순위를 설명할 때는 같은 family 안의 더 작은 risk를 먼저 닫는지, 아니면 왜 새 quality axis로 넘어가야 하는지를 짧게 드러내는 편이 좋습니다.
- 다만 같은 날 same-family docs-only truth-sync가 이미 3회 이상 반복된 상태라면, 다음 `/work` closeout은 또 하나의 더 작은 docs-only micro-slice보다 남은 drift를 한 번에 닫는 bounded bundle이나 escalation 문맥을 반영하는 편이 맞습니다.
- `.pipeline/gpt_prompt.md`는 optional/legacy scratch 슬롯로 남길 수 있지만, canonical single-Codex 흐름의 필수 단계는 아닙니다.
- single tmux 흐름에서도 active implement owner가 `/work`를 남긴 뒤 active verify/handoff owner가 검증과 handoff를 처리하더라도, 구현의 canonical closeout은 계속 `/work`입니다.
- 현재 helper-agent 표면에는 `trace-implementer`가 포함되며, 이 역할은 grounded-brief trace/memory foundation의 작은 구현 슬라이스를 맡는 전용 구현 서브에이전트입니다.
- `/work`의 구현 closeout은 "무엇을 만들었는가"를 기록하는 곳이지, 단순히 아직 비어 있는 internal regression 자리를 채웠다는 이유만으로 다음 제품 우선순위를 정당화하는 곳이 아닙니다.
- 현재 reviewed-memory 구현은 계속 허용되지만, closeout reason은 user-visible value, current-risk reduction, 또는 현재 shipped contract 정합성 중 무엇을 개선했는지 먼저 드러내야 합니다.
