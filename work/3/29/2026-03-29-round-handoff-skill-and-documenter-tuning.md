# 2026-03-29 round-handoff skill and documenter tuning

## 변경 파일
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.agents/skills/round-handoff/SKILL.md`
- `.claude/skills/round-handoff/SKILL.md`
- `.codex/config.toml` (로컬 설정 파일, git tracked 대상 아님)
- `.codex/agents/documenter.toml` (현재 로컬 agent 파일, git tracked 대상 아님)
- `.claude/agents/documenter.md` (현재 로컬 mirror 파일, git tracked 대상 아님)

## 사용 skill
- `skill-creator`: 반복되는 handoff 검증/다음 라운드 지시사항 작성 흐름을 저장소 전용 skill로 좁게 정리했습니다.
- `doc-sync`: 새 skill과 documenter 보강에 맞춰 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`를 현재 운영 truth와 맞췄습니다.
- `release-check`: 로컬 config 파싱, skill mirror 정합성, 참조 경로, diff 포맷을 실제 명령으로 다시 확인했습니다.
- `work-log-closeout`: 이번 운영 표면 수정 라운드를 `/work` 형식에 맞춰 기록했습니다.

## 변경 이유
- 이전 handoff 패턴을 보면 최신 `/work` closeout 재검증, 현재 코드/문서 truth 정렬, 다음 Codex 프롬프트 작성이 반복적으로 등장했지만 이를 직접 설명하는 repo skill은 없었습니다.
- 반면 새 전용 agent를 추가하면 기존 `documenter`와 역할이 겹칠 가능성이 커서, 이번 라운드에서는 새 agent 추가보다 handoff skill 신설과 `documenter` 보강이 더 작은 정직한 수정보완이라고 판단했습니다.

## 핵심 변경
- `.agents/skills/round-handoff/SKILL.md`와 `.claude/skills/round-handoff/SKILL.md`를 추가해, 최신 closeout 재검증, 실제 검증 재실행, current shipped truth 요약, one-next-slice handoff 프롬프트 작성 흐름을 저장소 전용 skill로 표준화했습니다.
- `.codex/config.toml`에 `round-handoff` skill을 기본 활성화로 등록했습니다.
- `.codex/agents/documenter.toml`와 `.claude/agents/documenter.md`에 “다음 라운드 요청 시 최신 `/work` + 현재 docs + 실제 검증을 먼저 reconcile한 뒤 프롬프트를 쓴다”는 책임을 추가해 handoff 품질 기준을 명시했습니다.
- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에는 `round-handoff`를 현재 유용한 운영 skill로 반영하고, 새 agent를 쉽게 늘리지 말고 기존 `documenter`와 중복을 피하자는 현재 운영 원칙을 적었습니다.

## 검증
- `python3 - <<'PY'`
  - `.codex/config.toml`을 `tomllib`로 파싱해 `round-handoff` 등록 여부를 확인했습니다.
  - 결과: `config_ok`, `True`
- `diff -rq .agents/skills .claude/skills`
- `rg -n "round-handoff|verification-backed next-round|next round" AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .codex/config.toml .codex/agents/documenter.toml .claude/agents/documenter.md .agents/skills/round-handoff/SKILL.md .claude/skills/round-handoff/SKILL.md`
- `git diff --check`

## 남은 리스크
- 새 `round-handoff` skill은 아직 실제 후속 라운드 여러 번을 거쳐 다듬은 상태는 아니므로, 이후 handoff 패턴이 더 넓어지면 추가 조정이 필요할 수 있습니다.
- 이번 라운드에서는 새 agent를 추가하지 않았기 때문에, handoff 작업이 더 구조화되면 나중에 `documenter`와 별도 역할 분리가 필요한지 다시 볼 수 있습니다.
- `.codex/config.toml`, `.codex/agents/documenter.toml`, `.claude/agents/documenter.md`는 현재 로컬 운영 표면이어서 git-tracked 범위와 배포 범위를 혼동하지 않도록 주의가 필요합니다.
