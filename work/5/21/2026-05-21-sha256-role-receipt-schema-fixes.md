# 2026-05-21 sha256 role receipt schema fixes

## 변경 파일
- `pipeline_runtime/schema.py` 수정
- `pipeline_runtime/state_contract.py` 수정
- `pipeline_runtime/receipts.py` 수정
- `tests/test_pipeline_runtime_schema.py` 수정
- `tests/test_pipeline_runtime_state_contract.py` 수정
- `tests/test_pipeline_runtime_supervisor.py` 수정
- `work/5/21/2026-05-21-sha256-role-receipt-schema-fixes.md` 신규 작성

## 사용 skill
- `security-gate`: receipt/state/hash 표면 변경이 local-first 기록과 operator 승인 경계를 완화하지 않는지 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `sha256_file()`이 대용량 verify artifact를 다룰 때 더 작은 고정 청크로 읽도록 해 supervisor poll loop의 긴 파일 읽기 부담을 낮추기 위해 변경했습니다.
- `state_contract._role_owners()`의 fallback role owner가 `lane_catalog.default_role_bindings()`와 달라 상태 표면의 active lane 추론이 어긋날 수 있었습니다.
- receipt schema version 리터럴을 모듈 상수로 분리해 wrapper event schema version 패턴과 맞추고, 향후 schema 변경 지점을 명확히 하기 위해 변경했습니다.

## 핵심 변경
- `sha256_file(path)`를 `iter(lambda: f.read(65536), b"")` 기반 64KiB 청크 읽기로 교체하고 순수 hex digest를 반환하도록 맞췄습니다.
- `state_contract._role_owners()` fallback이 하드코딩 dict 대신 `lane_catalog.default_role_bindings()`를 사용하도록 했습니다. 현재 저장소의 lane catalog 기본값은 `{"implement": "Codex", "verify": "Codex", "advisory": "Claude"}`입니다.
- `receipts.py`에 `RECEIPT_SCHEMA_VERSION = "1"`을 추가하고 `build_receipt()`가 이 상수를 참조하도록 했습니다.
- schema 테스트에 64KiB read size와 digest 결과를 고정했고, state contract 테스트에 lane catalog 기본값 일치를 추가했습니다.
- supervisor receipt 테스트가 생성된 receipt의 `schema_version`이 `RECEIPT_SCHEMA_VERSION`과 같은지 확인하도록 보강했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/state_contract.py pipeline_runtime/receipts.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_state_contract.py tests/test_pipeline_runtime_supervisor.py`
- 통과: `python3 -m unittest -v tests.test_pipeline_runtime_schema.RuntimeSchemaTest.test_sha256_file_reads_in_64k_chunks tests.test_pipeline_runtime_state_contract.RuntimeStateContractTests.test_default_role_owners_follow_lane_catalog_defaults tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_emits_receipt_and_control_block`
  - 결과: `Ran 3 tests`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_state_contract -v`
  - 결과: `Ran 9 tests`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_schema -v 2>&1 | tail -5`
  - 결과: `Ran 267 tests`, `OK`
- 통과: `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/state_contract.py pipeline_runtime/receipts.py`
- 통과: `git diff --check -- pipeline_runtime/schema.py pipeline_runtime/state_contract.py pipeline_runtime/receipts.py`
- 통과: `git diff --check -- pipeline_runtime/schema.py pipeline_runtime/state_contract.py pipeline_runtime/receipts.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_state_contract.py tests/test_pipeline_runtime_supervisor.py`

## 남은 리스크
- `sha256_file()`의 반환값은 요청 범위대로 `sha256:` prefix 없는 hex digest로 바뀌었습니다. 현재 직접 사용처는 receipt 생성 경로로 확인했지만, 과거 receipt와의 표시 형식 차이는 남습니다.
- `lane_catalog._DEFAULT_ROLE_BINDINGS`의 실제 현재값은 handoff 예시와 달리 advisory가 빈 문자열이 아니라 `Claude`입니다. 이번 변경은 source of truth를 `default_role_bindings()`로 통일하는 데 한정했습니다.
- `receipts.py`의 `validate_manifest()` 중복 읽기나 manifest schema migration은 이번 슬라이스 범위 밖으로 남겼습니다.
- `.pipeline/config/agent_profile.json`, runtime policy 관련 파일, tmux adapter 변경, 기존 `/work`/`verify` dirty 항목은 이번 슬라이스 이전부터 이어진 변경이며 되돌리지 않았습니다.
- commit, push, PR 생성, merge, release, publication은 실행하지 않았습니다.
