# 2026-04-16 office view dead code strip

## 변경 파일

- `controller/index.html`
- `tests/test_controller_server.py`

## 사용 skill

- `work-log-closeout`: 이번 dead-code strip 작업의 변경 내용과 검증 사실을 `/work` 메모로 남겼습니다.
- `round-handoff`: 실제 통과한 검증만 적어서 다음 확인 라운드가 truthfully 이어지도록 정리했습니다.

## 변경 이유

이전 `Runtime Room` 바닥선 정리 이후에도 남아 있던 old office 시각화 장식과 헬퍼를 더 걷어내서, controller Office View를 현재 렌더에 필요한 최소 코드만 남긴 상태로 더 낮추기 위해서입니다.

## 핵심 변경

1. `controller/index.html`에서 더 이상 렌더에 쓰지 않는 `office-watcher-core`, `office-role-object`, `office-agent-pill`, `office-agent-strip` 관련 CSS 블록을 제거했습니다.
2. `office-summary`, `office-floor-kicker`, `officeLaneRole()` 같은 옛 보조 구조도 함께 제거했습니다.
3. 모바일 보정도 현재 쓰는 `office-shell`, `office-desk-scene`, `office-floor-title` 중심으로만 남겼습니다.
4. `tests/test_controller_server.py`는 새 최소 화면 기준으로 옛 office 장식 문자열을 더 이상 기대하지 않도록 바꿨습니다.

## 검증

- `python3 -m unittest -v tests.test_controller_server`
- `git diff --check -- controller/index.html tests/test_controller_server.py`

## 남은 리스크

- `controller/index.html` 안에는 sprite/fallback 쪽 최소 헬퍼가 아직 남아 있어, 다음 slice에서 더 걷어낼 수 있습니다.
- 실제 브라우저에서 남아 있는 fallback 시각 요소를 완전히 정리하려면 자산 보장 여부를 같이 봐야 합니다.
