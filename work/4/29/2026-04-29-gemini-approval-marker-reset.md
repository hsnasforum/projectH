# 2026-04-29 Gemini 승인 마커 초기화

## 변경 파일
- `controller/monitor.py`
- `tests/test_controller_monitor.py`
- `work/4/29/2026-04-29-gemini-approval-marker-reset.md`

## 사용 skill
- `work-log-closeout`: 컨트롤러 모니터 수정, 실제 검증, 남은 리스크를 한국어 closeout으로 정리했다.

## 변경 이유
- Cozy controller 화면에서 Gemini가 `READY` / `REST` 상태인데도 노란 `!` 승인 대기 마커가 남아 있었다.
- 라이브 `/api/runtime/monitor-snapshot` 확인 결과 런타임은 `RUNNING`, `automation_health=ok`, Gemini lane은 `READY / prompt_visible`였지만, 컨트롤러 모니터의 `coordination_state.Gemini.approval_wait=true`가 남아 있었다.
- 원인은 이전 approval wait 흔적이 `lane_ready` 또는 `ready` 이벤트를 받은 뒤에도 내려가지 않는 상태 오염이었다.

## 핵심 변경
- `controller/monitor.py`에 approval wait 해제 상태 집합과 이벤트 집합을 추가했다.
- `ready`, `idle`, `working`, `off`, `dead`, `broken` 상태가 들어오면 stale `approval_wait`를 해제하도록 했다.
- `lane_ready`, `lane_working`, `handoff`, `resume`, `approval_granted` 이벤트도 stale `approval_wait` 해제 조건으로 통합했다.
- 실제 approval wait 이벤트가 들어온 경우에는 기존처럼 우선 `approval_wait=true`를 유지한다.
- `tests/test_controller_monitor.py`에 Gemini approval wait가 `lane_ready`로 해제되는 회귀 테스트를 추가했다.

## 검증
- `python3 -m py_compile controller/monitor.py tests/test_controller_monitor.py` 통과.
- `python3 -m unittest -v tests.test_controller_monitor` 통과: 5 tests OK.
- `git diff --check -- controller/monitor.py tests/test_controller_monitor.py` 통과.
- 패치 전 `http://127.0.0.1:8780/api/runtime/monitor-snapshot`에서 `Gemini.approval_wait=true` 확인.
- 컨트롤러 서버만 재시작한 뒤 같은 API에서 `gemini_coordination=null`, `Gemini hud approval_wait=false` 확인.
- 파이프라인 런타임 상태는 `RUNNING`, `automation_health=ok`로 유지됨을 확인.

## 남은 리스크
- 브라우저가 기존 WebSocket 세션을 계속 들고 있으면 화면에 낡은 상태가 잠깐 남을 수 있어 새로고침이 필요할 수 있다.
- 이번 변경은 컨트롤러 모니터의 stale approval marker만 수정했고, 파이프라인 제어 슬롯이나 실제 승인 정책은 변경하지 않았다.
- 기존 작업트리에는 이번 라운드와 무관한 문서/SQLite 관련 변경과 다수의 미추적 work/verify/report 파일이 남아 있다.
