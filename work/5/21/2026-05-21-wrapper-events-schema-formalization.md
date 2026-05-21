# 2026-05-21 Wrapper events schema formalization

## 변경 파일

- `pipeline_runtime/wrapper_events.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/21/2026-05-21-wrapper-events-schema-formalization.md`

## 사용 skill

- `security-gate`: wrapper event 로그 payload 계약과 `_schema_warnings` 기록이 런타임 감사 표면에 닿으므로, 로컬 로그 기록이 중단 없이 경고 중심으로 남는지 확인했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증 명령, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- tmux pane 텍스트 추론을 줄이고 wrapper event side-channel을 공식 truth channel로 키우기 위한 기반 계약이 필요했습니다.
- Step 2(supervisor 우선순위 재정렬)와 Step 3(Claude `stream-json` normalize)의 선행 작업으로 이벤트 타입별 필수 필드와 schema version을 코드에 명시했습니다.

## 핵심 변경

- `pipeline_runtime/wrapper_events.py`에 `WRAPPER_EVENT_SCHEMA_VERSION = "1"`과 `ALL_EVENT_TYPES`를 추가했습니다.
- 이벤트 타입별 필수 필드를 `_WRAPPER_EVENT_REQUIRED_FIELDS`로 명시했습니다.
- `validate_wrapper_event_payload(event_type, payload)`를 추가해 필수 필드 누락 목록을 반환하도록 했습니다.
  - 미정의 이벤트 타입은 확장성을 위해 `[]`로 통과합니다.
  - 필수 필드 누락 순서는 이벤트 계약 순서대로 고정했습니다.
- `append_wrapper_event()`가 모든 신규 wrapper event entry에 `schema_version`을 기록합니다.
- 필수 필드가 빠진 이벤트는 예외를 던지지 않고 top-level `_schema_warnings`에 누락 필드 목록을 기록합니다.
- `build_lane_read_models()`는 기존처럼 `event.get()` 기반으로 읽기 때문에 `schema_version`이 없는 legacy event도 계속 처리됩니다. 이를 별도 테스트로 확인했습니다.

## 검증

- focused 신규 테스트:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_wrapper_event_schema_validation_contract tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_append_wrapper_event_records_schema_version_and_warnings tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_lane_read_models_accepts_legacy_events_without_schema_version`
  - 결과: `Ran 3 tests in 0.004s` / `OK`.
- 컴파일:
  - `python3 -m py_compile pipeline_runtime/wrapper_events.py`
  - 통과했습니다.
- supervisor 전체 테스트:
  - `bash -o pipefail -lc 'python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5'`
  - 결과: `Ran 196 tests in 1.173s` / `OK`.
- CLI 테스트:
  - `bash -o pipefail -lc 'python3 -m unittest tests.test_pipeline_runtime_cli -v 2>&1 | tail -5'`
  - 결과: `Ran 38 tests in 0.062s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/wrapper_events.py tests/test_pipeline_runtime_supervisor.py`
  - 통과했습니다.

## 남은 리스크

- 이번 라운드는 schema + 검증만 수행했습니다. `supervisor.py`의 wrapper event 우선순위 재정렬은 건드리지 않았습니다.
- Claude `--output-format stream-json` 연결과 wrapper event normalize는 아직 구현하지 않았습니다.
- 기존 wrapper event 파일 마이그레이션은 하지 않았고, legacy event 호환만 유지했습니다.
- 필수 필드 누락은 런타임 중단 대신 `_schema_warnings`로 남기므로, 후속 라운드에서 이 경고를 operator-visible surface로 올릴지 결정해야 합니다.
- commit, push, PR, merge, publish는 수행하지 않았습니다.
