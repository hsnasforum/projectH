# /verify 정책

`/verify`는 projectH에서 **최신 Claude 작업을 검수**하기 위해 검증 재실행, 현재 truth 재대조, 다음 라운드 handoff 결과를 남기는 verification 디렉터리입니다.

## tracked 대상

- `verify/<month>/<day>/YYYY-MM-DD-<slug>.md` 형식의 verification 메모
- 이 파일처럼 `/verify` 운영 규칙을 설명하는 기준 문서

## 작성 원칙

- 검증 라운드를 시작할 때는 먼저 `work/<현재월>/<현재일>/` 아래의 최신 md 파일을 확인합니다.
- 오늘 `/work` 문서가 없으면 전날 날짜 폴더의 최신 `/work` 문서를 확인하고 이어받습니다.
- 같은 날짜의 `verify/<현재월>/<현재일>/` 아래에 기존 verification 메모가 있으면 그중 최신 파일도 이어서 확인합니다.
- verification 메모를 저장할 때는 `verify/<현재월>/<현재일>/` 폴더가 없으면 먼저 생성합니다.
- 한 verification 라운드가 끝날 때 실제 재실행한 검증, 실제 코드/문서 대조 결과, 현재 truth, 남은 리스크를 한 파일에 정리합니다.
- 기본 모드에서 verification 메모는 "이번 Claude `/work` 주장이 맞는가"를 확인하는 검수 결과서여야 합니다.
- 새 verification 메모에는 아래 섹션을 이 순서로 둡니다:
  - `## 변경 파일`
  - `## 사용 skill`
  - `## 변경 이유`
  - `## 핵심 변경`
  - `## 검증`
  - `## 남은 리스크`
- `## 사용 skill` 섹션은 항상 두고, 실제 사용한 skill이 없으면 `- 없음`으로 적습니다.
- verification-only 라운드에서 파일을 바꾸지 않았다면 `## 변경 파일`에는 `- 없음`으로 적습니다.
- 실행하지 않은 명령이나 검증 결과를 추측으로 적지 않습니다.

## `/work`와의 경계

- `/work`는 구현 closeout입니다.
- `/verify`는 최신 `/work`에 대한 검수 결과와 truth 재대조 결과입니다.
- 구현이 있었다면 먼저 `/work`가 있고, 그 다음 verification-backed handoff가 의미 있으면 `/verify`가 따라옵니다.
- `/verify`는 `/work`를 대체하지 않습니다. 최신 구현 truth는 항상 최신 `/work`부터 읽고 시작합니다.
- `.pipeline/codex_feedback.md`는 자동화용 rolling handoff 슬롯이며, 최신 verification truth를 편하게 넘기기 위한 보조 수단일 뿐 `/verify`를 대체하지 않습니다.
- `.pipeline/gpt_prompt.md`는 optional/legacy scratch 슬롯로 남길 수 있지만, canonical single-Codex 흐름의 필수 단계는 아닙니다.
- whole-project trajectory audit이나 milestone-level 평가는 `/verify`가 아니라 `report/`에 남기는 편이 맞습니다.

## 권장 예시

- verification note: `verify/3/30/2026-03-30-reviewed-memory-conflict-source-ref-verification.md`
- reusable same-day template: `verify/3/30/2026-03-30-verification-note-template.md`
- local scratch: `verify/local/<topic>.md`, `verify/local/<topic>.log`

## 운영 메모

- `/verify`는 `/work`와 같은 섹션 순서를 유지하되, 검증자가 실제로 다시 실행한 명령과 현재 truth를 더 엄격하게 기록하는 용도입니다.
- round-handoff, release-check 같은 verification/handoff 성격의 skill을 썼다면 그 사실을 `## 사용 skill`에 적습니다.
- `/work` 또는 `/verify` 정책이 바뀌면 두 README를 같은 라운드에서 함께 갱신해 후속 작업자가 경계를 헷갈리지 않게 합니다.
- single-Codex tmux 흐름에서는 Codex가 실제 검증 후 `/verify`를 남긴 다음 `.pipeline/codex_feedback.md`를 씁니다. persistent verification truth는 항상 `/verify`가 먼저입니다.
- Codex는 `.pipeline/codex_feedback.md`를 쓸 때 항상 다음 둘 중 하나를 명시합니다.
  - `STATUS: implement` = 다음 단일 슬라이스 확정
  - `STATUS: needs_operator` = 다음 단일 슬라이스 미확정, 자동 진행 금지
- `/verify`의 1차 목적은 현재 truth를 정직하게 다시 맞추는 것입니다. 다음 슬라이스 제안은 가능하지만, 단순한 uncovered regression 채우기보다 현재 MVP 우선순위를 먼저 통과해야 합니다.
- `/verify`의 1차 목적은 repo 전체 상태를 새로 재판정하는 것이 아니라, 최신 Claude 라운드가 truthful한지 확인하고 그 범위 안에서 다음 한 슬라이스를 좁게 제안하는 것입니다.
- 따라서 `/verify`에서 바로 다음 단일 슬라이스를 고르지 못했다면, Claude에게 선택권을 넘기지 말고 `.pipeline/codex_feedback.md`를 `STATUS: needs_operator`로 남기는 편이 맞습니다.
- focused regression만 다시 돌렸다면 그 이유를 적고, full browser 또는 end-to-end verification을 생략했다면 왜 이번 변경과 직접 관련이 없었는지 분명히 적습니다.
- `route-level`, `handler-level`, `helper-level` completeness 공백은 현재 shipped user flow를 지키는 경우가 아니라면 기본적으로 리스크 메모에 가깝게 다루고, 다음 기능 슬라이스의 자동 기본값으로 승격하지 않습니다.
