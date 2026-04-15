# 2026-04-16 controller office view reset to base

## 변경 파일

- `controller/index.html`
- `tests/test_controller_server.py`

## 사용 skill

- `work-log-closeout`: 이번 리셋 작업의 변경 내용과 검증 사실을 `/work` 메모로 정리했습니다.
- `round-handoff`: 실제 재검증 결과를 함께 맞춰서 다음 라운드가 바로 읽을 수 있게 정리했습니다.

## 변경 이유

사용자 요청에 따라 기존 Office View를 복잡한 war-room 연출에서 다시 낮춰, 다음 시각화 작업을 시작할 수 있는 최소 기반으로 되돌렸습니다. runtime authority와 API 경계는 건드리지 않고, controller read-model의 화면 밀도만 정리했습니다.

## 핵심 변경

1. Office View를 `Runtime Room` 중심의 최소 레이아웃으로 정리했습니다.
2. Claude / Codex / Gemini 3개 desk만 남기고, 보조 summary와 과한 scene 장식을 줄였습니다.
3. inspector는 유지하되 project root, runtime state, control seq, round, watcher, latest work/verify만 보이게 낮췄습니다.
4. controller HTML contract 테스트를 현재 렌더 텍스트와 runtime API 경계에 맞게 정리했습니다.

## 검증

- `python3 -m unittest -v tests.test_controller_server`
- `git diff --check -- controller/index.html tests/test_controller_server.py`

## 남은 리스크

- `controller/index.html` 안에 예전 Office View용 CSS와 helper가 일부 남아 있어, 다음 slice에서 더 과감하게 정리할 수 있습니다.
- sprite/asset 품질은 아직 완전히 균일하지 않아서, 실제 시각 품질 개선은 별도 후속 작업이 필요합니다.
