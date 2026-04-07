# /.pipeline 정책

`.pipeline`은 projectH의 single-Codex tmux 운영에서 쓰는 **rolling automation handoff 슬롯**입니다.

이 폴더는 최신 프롬프트를 자동화 프로그램이 읽기 쉽게 두는 용도이며, 역사 기록이나 canonical truth 저장소가 아닙니다.

현재 stage-3 흐름은 `start-pipeline.sh`가 띄우는 `watcher_core.py` experimental 경로에 반영되어 있습니다.
실제 자동 실행 기준은 `start-pipeline.sh` + `watcher_core.py` 경로를 우선합니다.

## 파일 역할

- `claude_handoff.md`
  - 작성자: Codex
  - 역할: Claude만 읽는 실행 슬롯
  - 형식: 현재 stage-3에서는 `STATUS: implement`만 포함
- `gemini_request.md`
  - 작성자: Codex
  - 역할: Codex가 못 좁힌 후보를 Gemini에게 넘기는 arbitration 요청 슬롯
  - 형식: 현재 stage-3에서는 `STATUS: request_open`만 포함
- `gemini_advice.md`
  - 작성자: Gemini
  - 역할: Gemini가 Codex에게 recommendation을 남기는 advisory 슬롯
  - 형식: 현재 stage-3에서는 `STATUS: advice_ready`만 포함
  - advisory 출력은 file edit/write tool 우선, shell heredoc/redirection은 피하는 편이 맞음
  - 읽기 대상은 가능하면 `@path` 형식의 명시적 file mention으로 붙이고, advisory log / advice slot도 prompt에 적힌 정확한 경로로 바로 쓰는 편이 맞음
- `operator_request.md`
  - 작성자: Codex
  - 역할: operator만 읽는 정지 슬롯
  - 형식: 현재 stage-3에서는 `STATUS: needs_operator`만 포함
- `session_arbitration_draft.md`
  - 작성자: watcher
  - 역할: active Claude session의 live side question을 감지했고 Codex/Gemini가 idle이며 Claude가 idle이거나 같은 escalation text에 짧게 안정됐을 때만 남기는 non-canonical draft 슬롯
  - 형식: `STATUS: draft_only`만 포함
  - 자동 실행 슬롯이 아니며 watcher / Claude / Gemini는 이 파일만으로 dispatch하지 않음
  - resolved 조건이 생기면 watcher가 정리할 수 있으며, 같은 fingerprint는 짧은 cooldown 동안 즉시 다시 열지 않음
- `codex_feedback.md`
  - 작성자: optional
  - 역할: scratch / legacy compatibility text only
  - canonical execution path에서는 읽지 않음
- `gpt_prompt.md`
  - 작성자: Codex 또는 operator
  - 역할: optional/legacy scratch 슬롯
  - canonical single-Codex 흐름에서는 필수 아님

## 운영 원칙

- 이 두 파일은 최신 슬롯 파일이므로 라운드마다 덮어써도 됩니다.
- persistent truth는 항상 아래에 남깁니다.
  - 구현 truth: `/work`
  - 검증 truth: `/verify`
- `.pipeline` 내용과 `/work` 또는 `/verify`가 충돌하면 `/work`와 `/verify`를 우선합니다.

## handoff 작성 원칙

- `.pipeline/claude_handoff.md`는 단순히 "다음으로 비어 있는 내부 regression"을 채우는 문서가 아닙니다.
- `.pipeline/claude_handoff.md`는 최신 Claude 작업을 검수한 결과를 다음 Claude 라운드에 넘기는 **실행 슬롯**입니다.
- `.pipeline/gemini_request.md`는 Codex가 실제로 exact slice를 못 좁혔을 때만 쓰는 **arbitration 요청 슬롯**입니다.
- `.pipeline/gemini_advice.md`는 Gemini가 Codex에게 recommendation을 남기는 **advisory 슬롯**입니다.
- `.pipeline/operator_request.md`는 Codex가 실제로 operator 판단이 필요할 때만 쓰는 **정지 슬롯**입니다.
- `.pipeline/session_arbitration_draft.md`는 watcher가 active session의 context exhaustion / session rollover / continue-vs-switch를 감지했고 Codex/Gemini가 idle이며 Claude가 idle이거나 같은 escalation text에 짧게 안정됐을 때만 남기는 **draft 슬롯**이며, canonical stop/go 신호가 아닙니다.
- 이 draft는 Claude activity resume, canonical Gemini/operator slot open, signal cleared 같은 resolved 조건이 생기면 watcher가 다시 정리할 수 있고, 같은 fingerprint는 짧은 cooldown 동안 곧바로 재생성하지 않는 편이 맞습니다.
- 실행 슬롯, Gemini arbitration 슬롯, 정지 슬롯을 Claude가 같이 읽지 않도록 분리하는 것이 stage-3 구조의 핵심입니다.
- `.pipeline/claude_handoff.md`는 현재 MVP 우선순위에 맞는 다음 Claude 라운드 한 슬라이스만 남겨야 합니다.
- active Claude session 중 context exhaustion, session rollover, continue-vs-switch 같은 live side question이 생기면, Codex는 `.pipeline/gemini_request.md` / `.pipeline/gemini_advice.md`를 coordination에만 쓰고 답은 Claude에게 짧은 lane reply로 relay합니다. 이 경우 `.pipeline/claude_handoff.md`는 session boundary 전까지 그대로 둡니다.
- `.pipeline/claude_handoff.md`는 `STATUS: implement`만 사용합니다.
- `.pipeline/gemini_request.md`는 `STATUS: request_open`만 사용합니다.
- `.pipeline/gemini_advice.md`는 `STATUS: advice_ready`만 사용합니다.
- `.pipeline/operator_request.md`는 `STATUS: needs_operator`만 사용합니다.
- `.pipeline/session_arbitration_draft.md`는 `STATUS: draft_only`만 사용합니다.
- `STATUS: implement`이면 Codex가 다음 단일 슬라이스를 이미 확정한 상태입니다. Claude는 그 한 슬라이스만 구현합니다.
- `STATUS: request_open`이면 Codex가 Gemini arbitration을 먼저 요청한 상태입니다. watcher는 Gemini를 먼저 부릅니다.
- `STATUS: advice_ready`이면 Gemini가 recommendation을 남긴 상태입니다. watcher는 Codex follow-up을 먼저 부릅니다.
- `STATUS: needs_operator`이면 Codex가 아직 다음 단일 슬라이스를 truthful하게 확정하지 못한 상태입니다. Claude는 이 stop 슬롯을 읽지 않고 operator 판단을 기다립니다.
- `STATUS: needs_operator`는 bare stop line만 남기는 용도가 아닙니다. 이 상태를 쓸 때는 최소한 아래를 같이 적는 편이 canonical입니다.
  - stop reason
  - 근거가 된 latest `/work`와 latest `/verify`
  - operator가 다음에 무엇을 정해야 하는지
- stop/go 판단은 최신 control 파일과 `STATUS` 줄이 담당합니다. 멈추고 싶다면 본문 설명만 고치는 대신 stop 슬롯을 최신으로 갱신해야 합니다.
- latest `/work`와 `/verify`가 한 family를 truthfully 닫았고 그 family 안에 더 작은 후속 risk가 남아 있다면, Codex는 보통 `needs_operator`보다 그 same-family current-risk reduction을 먼저 자동 확정하는 편이 맞습니다.
- 기본 자동 tie-break 순서는 아래와 같습니다.
  - same-family current-risk reduction
  - same-family user-visible improvement
  - new quality axis
  - internal cleanup
- 위 순서로도 truthful한 단일 슬라이스를 못 고를 때만 `STATUS: needs_operator`를 씁니다.
- 다음 슬라이스는 아래 중 하나를 직접 개선해야 합니다.
  - user-visible document workflow
  - current reviewed-memory user-visible clarity
  - approval, evidence, summary, search quality
  - current shipped flow risk reduction
- route-by-route handler completeness, contract-family completeness, internal helper completeness는 기본 handoff 우선순위가 아닙니다.
- stale handoff를 줄이기 위해 현재 `/work`와 `/verify`의 최신 truth를 먼저 확인하고, 그 범위 안에서만 handoff를 작성합니다.
- Playwright-only smoke tightening, selector drift, single-scenario fixture update handoff는 기본적으로 isolated browser rerun을 요구하는 편이 맞습니다. shared browser helper 변경, 여러 browser scenario 변경, release/ready 판단, isolated rerun의 broader drift 신호가 없는데도 `make e2e-test`를 기본처럼 요구하는 stale handoff는 피합니다.
- whole-project trajectory review나 milestone audit은 `.pipeline` handoff가 아니라 `report/`에서 별도로 다룹니다.

## 권장 흐름

1. Claude가 구현 후 최신 `/work` closeout을 남깁니다.
2. Codex가 최신 `/work`, 최신 same-day `/verify`를 읽고 실제 검증을 재실행합니다.
3. Codex가 `/verify` note를 남깁니다.
4. Codex가 구현 가능한 경우 `.pipeline/claude_handoff.md`에 `STATUS: implement`를 씁니다.
5. Codex가 exact slice를 못 좁히면 `.pipeline/gemini_request.md`에 `STATUS: request_open`을 씁니다.
6. Gemini가 `report/gemini/...md`와 `.pipeline/gemini_advice.md`에 `STATUS: advice_ready`를 남깁니다.
7. Codex가 Gemini advice를 읽고 최종 `.pipeline/claude_handoff.md` 또는 `.pipeline/operator_request.md`를 씁니다.
7-1. 예외적으로 active Claude session의 side-question arbitration이면, Codex는 Gemini advice를 Claude에게 짧은 lane reply로만 relay하고 `.pipeline/claude_handoff.md`는 덮어쓰지 않습니다. handoff 갱신은 session boundary 또는 다음 라운드 시작 시점으로 미룹니다.
7-2. watcher는 이런 active-session side-question을 감지해도 `.pipeline/gemini_request.md`를 자동으로 열지 않습니다. 필요하면 Codex/Gemini가 idle이고 Claude가 idle이거나 짧게 settle된 상태일 때 `.pipeline/session_arbitration_draft.md`만 생성하고, Codex가 직접 canonical 슬롯 승격 여부를 정합니다.
7-3. watcher가 생성한 `.pipeline/session_arbitration_draft.md`는 perpetual slot이 아닙니다. Claude가 다시 작업을 시작하거나 canonical Gemini/operator 슬롯이 열리면 watcher가 정리하고, 같은 fingerprint는 짧은 cooldown 동안 반복 생성하지 않는 편이 맞습니다.
8. `.pipeline/codex_feedback.md`는 필요하면 scratch로 남길 수 있지만, watcher는 그것을 stop/go 실행 신호로 읽지 않습니다.
9. watcher 또는 자동화는 `.pipeline/claude_handoff.md`의 `STATUS: implement`일 때만 Claude에 전달하고, `.pipeline/gemini_request.md`가 최신이면 Gemini를, `.pipeline/gemini_advice.md`가 최신이면 Codex follow-up을, `.pipeline/operator_request.md`가 최신 pending stop이면 자동 진행을 중단하는 쪽이 맞습니다.
10. watcher의 책임은 파일 변경 감지와 올바른 pane 전달까지입니다. 전송 후 Claude 또는 Codex or Gemini pane이 바쁘거나 interrupted 상태여서 처리가 안 되는 경우는 watcher contract 문제가 아니라 세션 상태 문제입니다.
11. Codex가 다음 슬라이스를 고를 때는, 같은 family 안의 작은 current-risk reduction을 먼저 닫고 그다음 새 quality axis로 넘어가는 편이 기본값입니다.
12. startup dispatch는 pane이 실제로 입력을 받을 준비가 됐는지 먼저 확인한 뒤 보내는 편이 맞습니다. 그 뒤에는 짧은 readiness 확인과 watcher retry에 맡기는 쪽이 기본값입니다.
13. startup 또는 rolling dispatch에서 최신 canonical `/work`가 latest same-day `/verify`보다 새로우면, fresher `claude_handoff.md`가 남아 있어도 Codex verification이 Claude 구현보다 우선입니다.
14. launcher가 `tmux attach`에서 빠져나와도 자동 진행이 이어져야 하므로, watcher는 launcher shell background보다 tmux session 내부의 별도 hidden watcher window에서 유지하는 편이 더 안전합니다.

## 최소 `needs_operator` 예시

```md
STATUS: needs_operator

이유:
- latest `/work`와 `/verify` 기준으로 다음 단일 슬라이스를 아직 truthful하게 확정하지 못했습니다.

근거:
- `work/<month>/<day>/<latest-work>.md`
- `verify/<month>/<day>/<latest-verify>.md`

operator 확인 필요:
- 다음 단일 user-visible slice 또는 current-risk reduction slice 1개 확정
- 확정 후 `STATUS: implement`로 갱신
```

## tmux 레인 예시

- pane 1: Claude CLI
- pane 2: Codex (verification + handoff lane)
- pane 3: Gemini (arbitration lane)

## 3-agent smoke helper

- repo-local live arbitration smoke는 `.pipeline/smoke-three-agent-arbitration.sh`로 반복 확인할 수 있습니다.
- 이 helper는 workspace 안에 `.pipeline/live-arb-smoke-XXXXXX/` 임시 base dir를 만들고:
  - `gemini_request.md`를 seed한 뒤
  - smoke-local `work/4/3/...`와 `verify/4/3/...` synthetic note를 같이 만들고
  - dummy Claude shell + Codex + Gemini tmux session을 띄우고
  - `watcher_core.py`를 custom `--base-dir`로 실행합니다.
- 성공 기준:
  - `gemini_advice.md`가 `STATUS: advice_ready`
  - `report/gemini/*.md` advisory log 생성
  - 이후 `claude_handoff.md` 또는 `operator_request.md` 생성
- 성공 시 기본값으로 smoke tmux session은 정리하고, smoke 산출물 디렉터리는 남겨 둡니다.
- 성공 시 기본값으로 최근 `3`개 smoke 디렉터리만 남기고 더 오래된 `live-arb-smoke-*` 디렉터리는 정리합니다.
- `PIPELINE_SMOKE_KEEP_RECENT=0`이면 자동 정리를 끌 수 있습니다.
- 실패 시 기본값으로 tmux session과 산출물을 남겨 inspection에 씁니다.
- 오래된 smoke 디렉터리만 수동으로 정리하려면 `.pipeline/cleanup-old-smoke-dirs.sh`를 쓸 수 있습니다.
- 기본값은 최근 `3`개 유지이며, `PIPELINE_SMOKE_CLEANUP_DRY_RUN=1`로 삭제 없이 대상만 확인할 수 있습니다.
