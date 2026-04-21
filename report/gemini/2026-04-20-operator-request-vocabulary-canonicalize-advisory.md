# 2026-04-20 operator-request-vocabulary-canonicalize advisory

## 상황 요약
- `G7` advisory-mode 테스트(seq 507)가 성공적으로 구현되어 `operator_request.md` 헤더의 구조적 무결성을 검증하는 기초가 마련되었습니다.
- 현재 `DECISION_CLASS` 어휘는 테스트 파일 내부에 `OBSERVED_DECISION_CLASSES`라는 이름으로 로컬하게 정의되어 있으며, 이는 실제 운영 환경의 `pipeline_runtime/operator_autonomy.py`와 분리되어 있습니다.
- 이전 Gemini 조언(seq 506)에서 제안된 `advisory_only` 리터럴은 현재 레포지토리 내 관찰된 사용 사례가 없어 seq 507 구현에서는 제외되었습니다.

## 판단
- **G7-canonicalize: Promote OBSERVED_DECISION_CLASSES to SUPPORTED_DECISION_CLASSES in operator_autonomy** 슬라이스를 권고합니다.
- **이유**: 어휘 정의를 중앙 집중화함으로써 테스트 유지보수 부담을 줄이고, 3-agent 아키텍처에서 Gemini의 역할을 명시적으로 지원하는 `advisory_only`를 공식 어휘에 포함시켜 향후 확장성을 확보합니다. 이는 `GEMINI.md`의 "same-family current-risk reduction" 원칙에 따라 현재 진행 중인 G7 패밀리를 가장 작고 안전하게 진전시키는 단계입니다.
- **우선순위**: 이미 G7 패밀리가 truthful하게 시작되었으므로, 다른 품질 축(G8)으로 넘어가기 전에 이 패밀리의 구조적 완결성을 높이는 것이 우선입니다.

## 권고 세부사항 (G7-canonicalize)
- **대상 파일 1**: `pipeline_runtime/operator_autonomy.py`
  - `SUPPORTED_OPERATOR_POLICIES` 정의 근처에 `SUPPORTED_DECISION_CLASSES` 상수를 추가합니다.
  - 포함 어휘: `operator_only`, `advisory_only`, `next_slice_selection`, `internal_only`, `truth_sync_scope`, `red_test_family_scope_decision`.
- **대상 파일 2**: `tests/test_operator_request_schema.py`
  - 로컬 `OBSERVED_DECISION_CLASSES` 정의를 제거합니다.
  - `pipeline_runtime.operator_autonomy`에서 `SUPPORTED_DECISION_CLASSES`를 import하여 `test_decision_class_is_observed`에서 사용하도록 수정합니다. (테스트 메서드 이름은 `test_decision_class_is_canonical`로 변경 권장)
- **주의 사항**: `normalize_decision_class` 함수의 동작은 이번 슬라이스에서 변경하지 않습니다. 순수하게 어휘 정의와 테스트 연동만 수행합니다.

## 검증
- `python3 -m unittest tests.test_operator_request_schema`가 5개 테스트 모두 통과하는지 확인.
- `python3 -m unittest tests.test_pipeline_gui_backend` (45/OK) 및 `tests.test_smoke` 회귀 테스트 확인.
- `pipeline_runtime/operator_autonomy.py`에 새로 추가된 상수가 올바르게 정의되었는지 정적 분석 확인.
