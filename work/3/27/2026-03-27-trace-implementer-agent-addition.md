# 2026-03-27 Trace implementer agent addition

## 변경 파일

- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/README.md`
- `.codex/agents/trace-implementer.toml`
- `.claude/agents/trace-implementer.md`
- `.codex/config.toml`

## 사용 skill

- `doc-sync`: helper-agent 역할 추가에 맞춰 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `work/README.md`, `.codex/config.toml`을 같은 기준으로 동기화하기 위해 사용
- `release-check`: agent 표면, 로컬 config 파싱, git diff 형식 검증, gitignore 상태를 실제 실행 결과 기준으로 확인하기 위해 사용
- `work-log-closeout`: 이번 operator/helper-agent 변경 라운드의 실제 변경 파일, 검증, 남은 리스크를 `/work` 규칙에 맞춰 남기기 위해 사용

## 변경 이유

- 이전 라운드들에서 grounded-brief trace / snapshot 구현은 진행됐지만, repo-local helper agents는 설계/리뷰/감사/문서 역할 위주라 구현 전용 역할이 비어 있었습니다.
- 반복되는 구현 슬라이스가 `artifact_id linkage`, `snapshot normalization`, `corrected-outcome linkage`처럼 명확해져서, 현재 MVP 범위를 넓히지 않는 전용 구현 서브에이전트가 필요했습니다.
- helper-agent 역할과 Codex config가 바뀌는 라운드이므로 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `work/README.md`까지 함께 맞춰야 했습니다.

## 핵심 변경

- 새 Codex 구현 전용 서브에이전트 `.codex/agents/trace-implementer.toml`을 추가했습니다.
- Claude mirror인 `.claude/agents/trace-implementer.md`를 추가해 역할 정의를 맞췄습니다.
- `trace-implementer`를 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`의 helper role 표면에 반영했습니다.
- `.codex/config.toml`에 `trace-implementer` agent registry를 추가했습니다.
- `work/README.md`에 현재 helper-agent 표면에 `trace-implementer`가 포함된다는 운영 메모를 추가했습니다.
- `trace-implementer` 역할은 grounded-brief trace/memory foundation의 작은 구현 슬라이스만 맡고, review queue, user-level memory, operator surface 같은 다음 단계 범위를 끌어오지 않도록 제한했습니다.

## 검증

- 실행: `rg -n "trace-implementer" AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md work/README.md .codex/config.toml .codex/agents/trace-implementer.toml .claude/agents/trace-implementer.md`
- 실행: `python3 - <<'PY' ... tomllib.load(Path(".codex/config.toml").open("rb")) ... PY`
- 실행: `git diff --check -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md work/README.md .codex/agents/trace-implementer.toml .claude/agents/trace-implementer.md`
- 실행: `rg -n "\.codex/config\.toml" .gitignore`
- 미실행: `python3 -m unittest -v`
- 미실행: `make e2e-test`
- 참고: `.codex/config.toml`은 로컬 설정 파일이며 `.gitignore` 대상이라 git diff 대상 검증에는 포함되지 않았습니다.

## 남은 리스크

- 이번 라운드에서 해소한 리스크:
  - repo-local 구현 전용 helper-agent 부재
  - helper-agent 표면과 운영 문서 간 동기화 부재
- 여전히 남은 리스크:
  - `trace-implementer`를 실제 병렬 구현 라운드에서 아직 사용해 보지 않았으므로 prompt 범위가 충분히 날카로운지는 후속 라운드에서 검증이 필요합니다.
  - `.codex/config.toml`은 gitignored라 로컬 Codex 동작에는 반영되지만 git tracked 설정 파일로는 공유되지 않습니다.
  - 이후 helper-agent 역할이 더 바뀌면 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `work/README.md`, mirror agent files를 계속 같이 맞춰야 합니다.
