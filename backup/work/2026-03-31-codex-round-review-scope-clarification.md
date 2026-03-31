# 2026-03-31 Codex round review scope clarification

## 변경 파일
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/README.md`
- `verify/README.md`
- `.pipeline/README.md`

## 사용 skill
- `doc-sync`
  - single-Codex 운영 문서 전반에 `Codex = 이번 Claude 작업 검수 + 방향 가드` 기준을 동기화했습니다.
- `work-log-closeout`
  - 오늘 운영 규칙 변경을 `/work` closeout 형식으로 정리했습니다.

## 변경 이유
- 최근 운영 대화에서 `/verify`가 매 라운드 전체 프로젝트 진단서처럼 커지는 경향이 문제로 드러났습니다.
- 현재 single-Codex 흐름에서 필요한 Codex 기본 역할은 전체 audit이 아니라, 최신 Claude `/work`를 검수하고 그 범위 안에서 다음 한 슬라이스를 좁게 제안하는 것입니다.
- whole-project trajectory audit은 필요할 때만 `report/`에 따로 남기는 경계가 문서에 더 분명하게 적힐 필요가 있었습니다.

## 핵심 변경
- `AGENTS.md`에 `report/`를 repository map에 추가하고, `Codex Review Scope` 섹션에서 Codex 기본 모드를 "latest Claude round review"로 못 박았습니다.
- `AGENTS.md`의 `/work`·`/verify` 규칙에 whole-project audit은 `report/`로 분리하고 `/verify`를 매 라운드 전체 감사로 쓰지 않는다는 기준을 추가했습니다.
- `CLAUDE.md`에 whole-project audit은 예외적이며 `report/`로 분리된다는 문구를 추가했습니다.
- `PROJECT_CUSTOM_INSTRUCTIONS.md`에 Codex 기본 모드는 "이번 Claude 작업 검수자 + 방향 가드"이며 전체 프로젝트 진단은 별도 `report/` 문서로 분리한다는 규칙을 추가했습니다.
- `verify/README.md`와 `.pipeline/README.md`에는 `/verify`와 `.pipeline/codex_feedback.md`가 최신 Claude 작업 검수 결과를 기반으로 한다는 점을 분명히 적었습니다.
- `work/README.md`에도 whole-project audit은 `/work`보다 `report/`가 더 적절하다는 경계를 추가했습니다.

## 검증
- `git diff --check`
  - 통과
- `rg -n "Codex Review Scope|전체 프로젝트 진단|whole-project|최신 Claude 작업을 검수|report/" AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md work/README.md verify/README.md .pipeline/README.md`
  - 관련 운영 문구가 각 문서에 반영된 것을 확인했습니다.

## 남은 리스크
- 이번 라운드는 운영 문서 수정만 했으므로 앱 코드나 테스트는 다시 돌리지 않았습니다.
- 실제 후속 `/verify` note가 새 규칙대로 "latest Claude round review" 범위를 지키는지는 다음 Codex 라운드에서 확인이 필요합니다.
- `report/`의 whole-project audit 문서를 언제, 어떤 기준으로 갱신할지는 아직 별도 운영 세부 규칙이 없습니다.
