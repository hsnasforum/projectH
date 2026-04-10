## 변경 파일
- pipeline_gui/agents.py
- tests/test_pipeline_gui_agents.py

## 사용 skill
- 없음

## 변경 이유
- Claude pane이 작업을 끝내고 `❯` 프롬프트가 떠 있어도, 최근 출력에 `✻ Sautéed for ...` closeout 문구가 남아 있으면 launcher가 `WORKING`으로 잘못 표시했습니다.
- 이 경우 실제 상태와 UI 상태가 어긋나서 누가 멈췄는지 판단하기 어렵습니다.

## 핵심 변경
- `pipeline_gui/agents.py`의 busy 패턴에서 Claude 완료형 closeout 문구인 `sautéed`를 제거했습니다.
- `tests/test_pipeline_gui_agents.py`에 `Sautéed for ... + ❯ + bypass permissions` 조합이 `READY`로 판정되는 회귀 테스트를 추가했습니다.
- 기존 Codex `• Working (37s • esc to interrupt)` 판정은 유지됩니다.

## 검증
- `python3 -m py_compile pipeline_gui/agents.py tests/test_pipeline_gui_agents.py`
- `python3 -m unittest -v tests.test_pipeline_gui_agents`
- `git diff --check -- pipeline_gui/agents.py tests/test_pipeline_gui_agents.py`

## 남은 리스크
- Claude가 다른 완료형 표현을 쓰기 시작하면 비슷한 오탐이 다시 생길 수 있습니다.
- 이번 수정은 `Sautéed for ...` closeout 오탐만 좁게 잡은 것이고, 실제 busy/ready 판정의 다른 텍스트 규칙은 그대로 유지됩니다.
