# 2026-03-30 verify log policy adoption

## 변경 파일
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/README.md`
- `verify/README.md`
- `.agents/skills/round-handoff/SKILL.md`
- `.claude/skills/round-handoff/SKILL.md`
- `.agents/skills/release-check/SKILL.md`
- `.claude/skills/release-check/SKILL.md`

## 사용 skill
- `doc-sync`
  - `/verify` 도입에 맞춰 operator 규칙, mirrored skill 문서, README 경계를 같이 맞추는 기준으로 사용했습니다.
- `release-check`
  - 앱 동작 변경이 없는 operator-rule 작업으로서 필요한 최소 검증만 다시 확인하는 기준으로 사용했습니다.
- `work-log-closeout`
  - 오늘 operator-flow 변경을 `/work` closeout 형식에 맞춰 정리하는 기준으로 사용했습니다.

## 변경 이유
- 현재 `/work`가 구현 closeout과 검증 재대조 결과를 함께 담고 있어, 구현 truth와 검증 truth를 나중에 구분하기 어려웠습니다.
- 구현자와 검증자를 분리해 운영하는 흐름에서, verification-backed handoff 결과를 `/work`와 별도로 남길 형제 디렉터리 정책이 필요했습니다.
- 같은 규칙을 Codex와 Claude 양쪽에서 일관되게 따르도록 operator 문서와 mirrored skill까지 함께 동기화해야 했습니다.

## 핵심 변경
- top-level `verify/README.md`를 새로 추가해 `/verify`를 verification rerun, truth 재대조, handoff 결과 전용 디렉터리로 정의했습니다.
- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에 `/work`는 구현 closeout, `/verify`는 검증 결과라는 경계를 추가했고, verification 라운드는 최신 `/work`를 먼저 읽고 같은 날짜의 최신 `/verify`를 이어받도록 규칙을 명시했습니다.
- `work/README.md`에 `/verify` sibling 경계를 추가해 구현-only closeout과 verification-only handoff를 분리했습니다.
- `.agents/skills/round-handoff/SKILL.md`와 `.claude/skills/round-handoff/SKILL.md`를 업데이트해 meaningful handoff는 `/verify` note를 남기도록 바꿨습니다.
- `.agents/skills/release-check/SKILL.md`와 `.claude/skills/release-check/SKILL.md`를 업데이트해 verification / handoff 라운드에서는 `/verify` note 존재도 점검하도록 맞췄습니다.

## 검증
- `rg -n "verify/README.md|/verify|closeout or handoff policy changed|operator logging|verification" AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md work/README.md verify/README.md .agents/skills/round-handoff/SKILL.md .claude/skills/round-handoff/SKILL.md .agents/skills/release-check/SKILL.md .claude/skills/release-check/SKILL.md`
- `git diff --check`

## 남은 리스크
- 이번 라운드는 operator-rule / docs-only 변경이어서 앱 코드 테스트나 browser smoke는 다시 돌리지 않았습니다.
- 기존 worktree가 매우 dirty해서, 이번 closeout은 제 변경 파일만 기준으로 정리했고 unrelated 변경은 건드리지 않았습니다.
- `/verify` 실제 사용 패턴은 다음 handoff 라운드들에서 다듬어질 수 있습니다. 예를 들어 verification-only note slug 규칙이나 `/verify/local/` 운용은 실제 사용 후 보완이 필요할 수 있습니다.
