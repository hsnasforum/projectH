# 2026-04-16 controller uncertain runtime hardening verification

## 변경 파일
- 없음

## 사용 skill
- 없음

## 변경 이유
- 최신 `/work` 기준으로 ambiguous recent snapshot이 더 이상 clean `RUNNING`처럼 보이지 않는지, 그리고 controller HTML contract가 uncertain runtime 표현과 modal wrap을 실제로 포함하는지 재검증하는 라운드입니다.

## 핵심 변경
- `pipeline_gui/backend.py`의 recent ambiguous snapshot 정규화는 test fixture 기준으로 `DEGRADED(supervisor_missing_recent_ambiguous)`를 반환하고, stale timeout 경과 후에는 기존대로 `BROKEN(supervisor_missing)`으로 내려갑니다.
- `controller/index.html`은 `getRuntimePresentation(data)` helper를 통해 toolbar badge / runtime sidebar / event log의 uncertain runtime 규칙을 공유합니다.
- log modal info strip wrap CSS와 body full-width 계약은 정적 HTML contract test에서 함께 확인했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_controller_server`
  - 결과: `Ran 58 tests`, `OK`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/server.py tests/test_controller_server.py`
  - 결과: 오류 없음
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/index.html tests/test_controller_server.py README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: 출력 없음

## 남은 리스크
- controller 브라우저를 실제로 띄운 수동 smoke는 이번 verification 범위에 포함하지 않았습니다.
- ambiguous normalization은 의도적으로 보수적이라, pid/field/updated_at이 더 손상된 payload family는 여전히 후속 hardening 후보로 남습니다.
