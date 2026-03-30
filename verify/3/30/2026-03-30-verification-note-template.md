# 2026-03-30 verification note template

이 파일은 `/verify` 검증 메모를 새로 만들 때 복사해서 쓰는 예시 템플릿입니다.
실제 verification note를 남길 때는 파일명과 제목의 날짜/slug를 현재 라운드에 맞게 바꾸고,
실제로 실행한 명령과 실제 현재 truth만 남기세요.

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`
  - 최신 `/work` closeout, 현재 코드, 현재 문서를 다시 대조하고 다음 라운드 handoff를 준비할 때 사용합니다.
- `release-check`
  - 실제로 다시 실행한 검증과 미실행 수동 확인을 구분해 정리할 때 사용합니다.

## 변경 이유
- 최신 `/work` closeout을 기준으로 현재 코드와 문서가 아직 같은 truth를 가리키는지 다시 확인합니다.
- 실제 검증을 다시 실행한 결과를 구현 closeout과 분리된 verification note로 남깁니다.
- 다음 라운드 지시사항이 구현자의 자기 보고가 아니라, rerun된 검증과 current truth에 기반하도록 고정합니다.

## 핵심 변경
- 최신 `/work` closeout:
  - `<읽은 최신 /work 파일 경로>`
- 이번 verification에서 다시 확인한 문서:
  - `<docs/NEXT_STEPS.md>`
  - `<docs/MILESTONES.md>`
  - `<docs/TASK_BACKLOG.md>`
  - `<필요 시 추가 문서>`
- 이번 verification에서 다시 확인한 구현/테스트 파일:
  - `<app/web.py>`
  - `<tests/test_smoke.py>`
  - `<tests/test_web_app.py>`
- 현재 truth 요약:
  - `<현재 shipped truth>`
- 다음 최소 slice:
  - `<one smallest next slice only>`

## 검증
- `<실제로 다시 실행한 명령 1>`
- `<실제로 다시 실행한 명령 2>`
- `<실제로 다시 실행한 명령 3>`
- 수동 확인 미실행:
  - `<예: 실제 Ollama 로컬 모델 수동 품질 확인은 이번 verification에서 수행하지 않음>`

## 남은 리스크
- `<현재도 unresolved / absent 인 층>`
- `<dirty worktree 또는 manual QA 미실행 같은 운영 리스크>`
- `<다음 slice를 하나만 열어야 하는 이유>`
