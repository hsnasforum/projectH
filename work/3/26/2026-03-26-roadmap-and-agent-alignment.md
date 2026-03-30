# 2026-03-26 Roadmap and agent alignment

## 변경 파일

- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.codex/config.toml`
- `.codex/agents/planner.toml`
- `.codex/agents/spec-editor.toml`
- `.codex/agents/reviewer.toml`
- `.codex/agents/documenter.toml`
- `.claude/agents/planner.md`
- `.claude/agents/spec-editor.md`
- `.claude/agents/reviewer.md`
- `.claude/agents/documenter.md`
- `.agents/skills/mvp-scope/SKILL.md`
- `.claude/skills/mvp-scope/SKILL.md`
- `plandoc/2026-03-26-teachable-local-agent-roadmap.md`

## 사용 skill

- `mvp-scope`: 현재 문서 비서 MVP와 장기 북극성 사이의 단계를 4단계 로드맵으로 구조화하기 위해 사용
- `doc-sync`: 운영 문서와 agent/skill 정의를 같은 방향으로 맞추기 위해 사용
- `work-log-closeout`: 이번 라운드 closeout 형식과 기록 항목을 일관되게 남기기 위해 사용

## 변경 이유

- 사용자 의도는 단순 문서 비서가 아니라, 장기적으로는 “가르치면 길들여지고 나중에는 프로그램까지 조작하는 로컬 개인 에이전트”였습니다.
- 기존 운영 문서와 subagent/skill 정의는 현재 문서 비서 MVP에는 맞았지만, 장기 북극성과 단계 구분을 드러내기에는 부족했습니다.

## 핵심 변경

- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에 현재 shipped contract와 장기 북극성을 분리해서 적고, `plandoc/`를 전략 문서 경로로 추가했습니다.
- `AGENTS.md`에 teachability, correction/approval memory, future operator layer를 다루는 규칙과 roadmap 문서 동기화 규칙을 추가했습니다.
- planner/spec-editor/reviewer/documenter 계열 Codex/Claude agent 정의를 장기 로드맵을 다룰 때 현재 구현과 aspiration을 섞지 않도록 보강했습니다.
- `mvp-scope` skill을 “현재 MVP + 장기 north star + staged roadmap”을 함께 다룰 수 있게 확장했습니다.
- `plandoc/2026-03-26-teachable-local-agent-roadmap.md`에 4단계 로드맵을 새로 작성했습니다.

## 검증

- `python3 - <<'PY' ... tomllib.load('.codex/config.toml') ... PY`
- `git diff --check -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .codex/config.toml .codex/agents/planner.toml .codex/agents/spec-editor.toml .codex/agents/reviewer.toml .codex/agents/documenter.toml .claude/agents/planner.md .claude/agents/spec-editor.md .claude/agents/reviewer.md .claude/agents/documenter.md .agents/skills/mvp-scope/SKILL.md .claude/skills/mvp-scope/SKILL.md plandoc/2026-03-26-teachable-local-agent-roadmap.md`
- `sed -n '1,260p' plandoc/2026-03-26-teachable-local-agent-roadmap.md`

## 남은 리스크

- `.codex/config.toml`은 현재 `.gitignore` 대상이라 로컬 Codex 동작에는 반영되지만 git tracked 설정 문서로는 남지 않습니다.
- 장기 북극성은 정리했지만, 아직 제품 문서(`docs/PRODUCT_PROPOSAL.md`, `docs/PRODUCT_SPEC.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`)에는 이번 방향 전환을 본격 반영하지 않았습니다.
- Python 테스트나 E2E는 이번 라운드가 운영/계획 문서 중심이라 별도로 실행하지 않았습니다.
