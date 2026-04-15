# 2026-04-16 office view dead code strip

## 요약

- Office View에서 더 이상 쓰이지 않는 old office 장식과 helper를 추가로 걷어냈습니다.
- 현재 화면은 `Runtime Room` 기반의 최소 뼈대에 더 가까워졌습니다.
- runtime authority와 API 경계는 그대로 유지했습니다.

## 판단

- 이번 slice는 시각 연출을 추가하는 작업이 아니라, 남아 있던 dead path를 제거해서 바닥선을 더 깨끗하게 만드는 작업입니다.
- controller UI는 여전히 최소 scene 유지, inspector 최소 표시, runtime API only라는 원칙을 지킵니다.

## 검증

- `python3 -m unittest -v tests.test_controller_server`
- `git diff --check -- controller/index.html tests/test_controller_server.py`

## 남은 과제

- sprite fallback 경로를 더 걷어낼지 여부 결정
- 필요하면 다음 slice에서 fallback까지 더 단순화
