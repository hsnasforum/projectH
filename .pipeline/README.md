# /.pipeline 정책

`.pipeline`은 projectH의 single-Codex tmux 운영에서 쓰는 **rolling automation handoff 슬롯**입니다.

이 폴더는 최신 프롬프트를 자동화 프로그램이 읽기 쉽게 두는 용도이며, 역사 기록이나 canonical truth 저장소가 아닙니다.

## 파일 역할

- `codex_feedback.md`
  - 작성자: Codex
  - 역할: verification-backed handoff 뒤 다음 Claude 라운드에 넘길 지시사항
  - 형식: 반드시 `STATUS: implement` 또는 `STATUS: needs_operator` 포함
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

- `.pipeline/codex_feedback.md`는 단순히 "다음으로 비어 있는 내부 regression"을 채우는 문서가 아닙니다.
- `.pipeline/codex_feedback.md`는 기본적으로 최신 Claude 작업을 검수한 결과를 다음 Claude 라운드에 넘기는 문서입니다.
- 이 파일은 현재 MVP 우선순위에 맞는 다음 Claude 라운드 한 슬라이스만 남겨야 합니다.
- 이 파일은 아래 두 상태 중 하나만 사용합니다.
  - `STATUS: implement`
  - `STATUS: needs_operator`
- `STATUS: implement`이면 Codex가 다음 단일 슬라이스를 이미 확정한 상태입니다. Claude는 그 한 슬라이스만 구현합니다.
- `STATUS: needs_operator`이면 Codex가 아직 다음 단일 슬라이스를 truthful하게 확정하지 못한 상태입니다. Claude는 새 구현을 시작하지 않고 operator 판단을 기다립니다.
- stop/go 판단은 `STATUS` 줄이 담당합니다. 멈추고 싶다면 본문 설명만 고치는 대신 `STATUS`를 바꿔야 합니다.
- 다음 슬라이스는 아래 중 하나를 직접 개선해야 합니다.
  - user-visible document workflow
  - current reviewed-memory user-visible clarity
  - approval, evidence, summary, search quality
  - current shipped flow risk reduction
- route-by-route handler completeness, contract-family completeness, internal helper completeness는 기본 handoff 우선순위가 아닙니다.
- stale handoff를 줄이기 위해 현재 `/work`와 `/verify`의 최신 truth를 먼저 확인하고, 그 범위 안에서만 handoff를 작성합니다.
- whole-project trajectory review나 milestone audit은 `.pipeline` handoff가 아니라 `report/`에서 별도로 다룹니다.

## 권장 흐름

1. Claude가 구현 후 최신 `/work` closeout을 남깁니다.
2. Codex가 최신 `/work`, 최신 same-day `/verify`를 읽고 실제 검증을 재실행합니다.
3. Codex가 `/verify` note를 남깁니다.
4. Codex가 다음 Claude 지시사항을 `.pipeline/codex_feedback.md`에 씁니다.
5. watcher 또는 자동화는 `STATUS: implement`일 때만 Claude에 전달하고, `STATUS: needs_operator`이면 자동 진행하지 않는 쪽이 맞습니다.
6. watcher의 책임은 파일 변경 감지와 올바른 pane 전달까지입니다. 전송 후 Claude 또는 Codex pane이 바쁘거나 interrupted 상태여서 처리가 안 되는 경우는 watcher contract 문제가 아니라 세션 상태 문제입니다.

## tmux 레인 예시

- pane 1: Claude CLI
- pane 2: Codex (verification + handoff lane)
- pane 3: watcher
