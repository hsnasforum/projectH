# 2026-04-15 active lane auth failure surfacing

## 요약
- Claude implement lane이 실제로는 `API Error: 401`, `Invalid authentication credentials`, `Please run /login` 상태인데도 runtime 표면에서는 `READY + prompt_visible`처럼 보일 수 있었습니다.
- 이번 수정으로 supervisor가 active lane pane tail에서 auth/login failure를 감지하면 lane을 `BROKEN`, note를 `auth_login_required`로 surface하고 blind restart를 막도록 보강했습니다.

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 핵심 변경
- active lane에 대해서만 pane tail을 읽어 auth/login failure 패턴을 확인합니다.
- `401`, `Invalid authentication credentials`, `Please run /login`, `authentication_error`가 보이면 lane surface를 `BROKEN + auth_login_required`로 바꿉니다.
- 이 경우 supervisor recovery는 자동 restart를 반복하지 않고 degraded reason으로 남깁니다.
- operator runbook과 QA 문서에도 auth/login failure를 false `READY` 방지 시나리오로 추가했습니다.

## 메모
- 이번 수정은 wrapper event contract를 확장한 것이 아니라, live wrapper path가 아직 완전히 들어오지 않은 구간에서 supervisor read-model을 truthfully 보정한 1차 방어선입니다.
- 장기적으로는 wrapper-events live path가 더 넓어지면 같은 failure를 wrapper `BROKEN(reason=...)`로 내리는 쪽이 더 깔끔합니다.
