# 2026-04-09 setup reconciliation hardening

## 변경 파일
- `pipeline_gui/setup_profile.py`
- `pipeline_gui/app.py`
- `tests/test_pipeline_gui_setup_profile.py`
- `tests/test_pipeline_gui_app.py`

## 사용 skill
- `work-log-closeout` - 구현 라운드 종료 후 변경 사실, 검증, 잔여 리스크를 저장소 형식에 맞춰 정리하기 위해 사용

## 변경 이유
- `selected_agents`에 허용되지 않은 agent 이름이 들어와도 조용히 버려져 malformed payload가 부분 정상화된 profile처럼 보일 여지가 있었습니다.
- `last_applied.json`은 있는데 active profile이 사라진 경우 restart reconciliation이 UI에서 무음 처리되고 있었습니다.
- 깨진 `preview.json`/`result.json` 같은 canonical setup artifact가 cleanup에서 남아 false resume 신호가 될 가능성이 있었습니다.

## 핵심 변경
- `pipeline_gui/setup_profile.py`에서 unknown `selected_agents`를 명시 오류로 올려 active profile resolution이 fail-loud 하게 `broken/blocked`로 떨어지도록 보강했습니다.
- `reconcile_last_applied()`는 record가 있는데 active profile이 없으면 `mismatch`로 돌리고, 앱 UI가 이 상태를 recovery guidance로 노출하도록 `app.py`의 feedback/notice 경로를 보강했습니다.
- `cleanup_stale_setup_artifacts()`가 unreadable canonical artifact를 정리하도록 바꿔 corrupted `preview.json`/`apply.json`/`result.json`이 setup entry 판단을 흐리지 않게 했습니다.
- 관련 회귀 테스트를 추가해 unknown agent, missing active reconciliation, unreadable canonical cleanup 시나리오를 잠갔습니다.

## 검증
- `python3 -m py_compile pipeline_gui/setup_profile.py pipeline_gui/app.py tests/test_pipeline_gui_setup_profile.py tests/test_pipeline_gui_app.py`
- `python3 -m unittest -v tests.test_pipeline_gui_setup_profile tests.test_pipeline_gui_app`
- `python3 -m unittest -v tests.test_pipeline_gui_setup_profile tests.test_pipeline_gui_setup tests.test_pipeline_gui_app`

## 남은 리스크
- setup support label/gating은 여전히 `pipeline_gui/app.py`의 `_setup_support_level()` 체계와 `pipeline_gui/setup_profile.py`의 foundation policy가 분리돼 있어 단일 truth가 아닙니다.
- 이번 라운드는 fail-loud와 reconciliation hardening까지 닫았고, 다음 단계는 app 시작/preview/apply gating을 `classifier/resolver/support-policy` 기준으로 올리는 작업이 자연스럽습니다.
