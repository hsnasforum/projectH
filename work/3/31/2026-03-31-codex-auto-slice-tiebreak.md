# 2026-03-31 codex auto slice tiebreak

## 변경 파일
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.pipeline/README.md`
- `work/README.md`
- `verify/README.md`
- `work/3/31/2026-03-31-codex-auto-slice-tiebreak.md`

## 사용 skill
- `doc-sync`
- `work-log-closeout`

## 변경 이유
- single-Codex tmux 흐름에서 Codex가 다음 단일 슬라이스를 충분히 자주 `STATUS: needs_operator`로 되돌리고 있어, same-family current-risk reduction까지 operator가 직접 골라야 하는 반복이 생겼습니다.
- current MVP 범위 안에서 truthful하게 자동 선택할 수 있는 경우와, 정말 operator 판단이 필요한 경우의 경계를 문서에 더 명확히 적을 필요가 있었습니다.

## 핵심 변경
- `AGENTS.md`에 Codex 자동 다음 슬라이스 선택 우선순위를 추가했습니다.
  - same-family current-risk reduction
  - same-family user-visible improvement
  - new quality axis
  - internal cleanup
- `STATUS: needs_operator`는 진짜 동률이 남았거나 approval-record / truth-sync가 구현보다 먼저일 때만 쓰도록 조건을 더 명시했습니다.
- `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/README.md`에 같은 tie-break 규칙을 반영해 Claude가 handoff를 다시 넓게 해석하지 않도록 했습니다.
- `work/README.md`, `verify/README.md`에도 같은 operator-flow 보강을 추가해 `/work`와 `/verify` closeout이 다음 우선순위 설명을 더 일관되게 남기도록 맞췄습니다.

## 검증
- `sed -n '152,215p' AGENTS.md`
- `sed -n '96,135p' CLAUDE.md`
- `sed -n '80,130p' PROJECT_CUSTOM_INSTRUCTIONS.md`
- `sed -n '1,110p' .pipeline/README.md`
- `sed -n '35,65p' work/README.md`
- `sed -n '45,75p' verify/README.md`

## 남은 리스크
- 이 규칙을 실제로 얼마나 잘 따르는지는 다음 몇 라운드의 Codex handoff에서 확인이 필요합니다.
- watcher나 pane session-state 문제는 이번 규칙 보강과 별개이므로, 자동 전달 품질은 여전히 세션 상태에 영향을 받습니다.
