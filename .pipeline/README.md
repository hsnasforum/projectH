# /.pipeline 정책

`.pipeline`은 projectH의 single-Codex tmux 운영에서 쓰는 **rolling automation handoff 슬롯**입니다.

이 폴더는 최신 프롬프트를 자동화 프로그램이 읽기 쉽게 두는 용도이며, 역사 기록이나 canonical truth 저장소가 아닙니다.

## 파일 역할

- `codex_feedback.md`
  - 작성자: Codex
  - 역할: verification-backed handoff 뒤 다음 Claude 라운드에 넘길 지시사항
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

## 권장 흐름

1. Claude가 구현 후 최신 `/work` closeout을 남깁니다.
2. Codex가 최신 `/work`, 최신 same-day `/verify`를 읽고 실제 검증을 재실행합니다.
3. Codex가 `/verify` note를 남깁니다.
4. Codex가 다음 Claude 지시사항을 `.pipeline/codex_feedback.md`에 씁니다.

## tmux 레인 예시

- pane 1: Claude CLI
- pane 2: Codex (verification + handoff lane)
- pane 3: watcher
