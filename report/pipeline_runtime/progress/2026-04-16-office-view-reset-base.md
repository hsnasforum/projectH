# 2026-04-16 office view reset to base

## 요약

- 기존 Office View를 다시 바닥선으로 낮췄습니다.
- 지금 화면은 `Runtime Room` 중심의 최소 구조이고, Claude / Codex / Gemini 3개 lane만 먼저 보이도록 정리했습니다.
- runtime authority와 API 경계는 그대로 유지했습니다.

## 판단

- 이번 변경은 `war-room`의 추가 연출을 더 얹는 방향이 아니라, 다음 시각화 작업을 시작할 수 있는 zero-base 정리입니다.
- 화면 복잡도를 낮춰서 desk와 상태가 먼저 읽히는 쪽으로 되돌렸습니다.

## 검증

- `python3 -m unittest -v tests.test_controller_server`
- `git diff --check -- controller/index.html tests/test_controller_server.py`

## 남은 과제

- 남아 있는 Office View CSS/helper를 더 걷어내는 후속 정리
- sprite/animation 품질에 대한 별도 개선
