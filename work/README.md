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
- 구현이 없는 verification-only handoff는 `/work`가 아니라 `/verify`에 남깁니다.
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
- `/work`가 구현 closeout, `/verify`가 검증 결과라는 경계가 바뀌면 두 README를 같은 라운드에서 함께 갱신합니다.
- `.pipeline/codex_feedback.md`는 자동화용 rolling 최신 슬롯입니다. 구현 truth는 항상 최신 `/work`에 남기고, `.pipeline`은 그 내용을 넘겨주기 위한 보조 수단으로만 씁니다.
- Claude는 보통 `.pipeline/codex_feedback.md`가 `STATUS: implement`일 때만 새 구현 `/work`를 남깁니다. `STATUS: needs_operator`일 때는 새 `/work` closeout을 억지로 만들지 않습니다.
- `STATUS: needs_operator`는 bare stop line 하나로 끝내지 않는 편이 맞습니다. 최소한 왜 멈췄는지와 operator가 다음에 무엇을 정해야 하는지는 `.pipeline/codex_feedback.md`에 남겨야, Claude가 멈춘 이유를 나중에 다시 추적할 수 있습니다.
- Codex는 latest `/work`와 `/verify`가 한 family를 truthfully 닫았을 때 같은 family의 가장 작은 current-risk reduction을 먼저 자동 확정할 수 있습니다. 다음 슬라이스를 매번 operator가 직접 고를 필요는 없습니다.
- 따라서 `/work` closeout도 다음 우선순위를 설명할 때는 같은 family 안의 더 작은 risk를 먼저 닫는지, 아니면 왜 새 quality axis로 넘어가야 하는지를 짧게 드러내는 편이 좋습니다.
- `.pipeline/gpt_prompt.md`는 optional/legacy scratch 슬롯로 남길 수 있지만, canonical single-Codex 흐름의 필수 단계는 아닙니다.
- single-Codex tmux 흐름에서도 Claude가 `/work`를 남긴 뒤 Codex가 검증과 handoff를 처리하더라도, 구현의 canonical closeout은 계속 `/work`입니다.
- 현재 helper-agent 표면에는 `trace-implementer`가 포함되며, 이 역할은 grounded-brief trace/memory foundation의 작은 구현 슬라이스를 맡는 전용 구현 서브에이전트입니다.
- `/work`의 구현 closeout은 "무엇을 만들었는가"를 기록하는 곳이지, 단순히 아직 비어 있는 internal regression 자리를 채웠다는 이유만으로 다음 제품 우선순위를 정당화하는 곳이 아닙니다.
- 현재 reviewed-memory 구현은 계속 허용되지만, closeout reason은 user-visible value, current-risk reduction, 또는 현재 shipped contract 정합성 중 무엇을 개선했는지 먼저 드러내야 합니다.
