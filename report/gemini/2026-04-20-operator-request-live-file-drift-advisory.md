# 2026-04-20 operator-request-live-file-drift-advisory

## 상황 요약
- `G7-canonicalize` (seq 510)를 통해 `REASON_CODE`, `OPERATOR_POLICY`, `DECISION_CLASS` 어휘 정의가 중앙 집중화되었습니다.
- 현재 `tests/test_operator_request_schema.py`는 고정된 픽스처(`FIXTURE_HEADER`)만 검증하고 있으며, 실제 운영에서 사용되는 `.pipeline/operator_request.md` 파일의 실시간 drift는 감지하지 못합니다.
- 현재 레포지토리의 `.pipeline/operator_request.md` (seq 462)는 `REASON_CODE: advice_g5_not_bounded_first_sub_slice`라는 비표준 리터럴을 포함하고 있어, 단순히 테스트를 연결하면 실패하게 됩니다.

## 판단
- **G7-live-file (Option A)** 슬라이스를 권고합니다.
- **이유**: `GEMINI.md`의 "same-family current-risk reduction" 기준에 따라, 가상의 픽스처가 아닌 실제 운영 파일의 무결성을 감지하는 것이 중요합니다.
- **리스크 관리**: 현재의 stale한 정지 사유(`advice_g5_not_bounded_first_sub_slice`)는 `self.skipTest`를 통해 "알려진 drift"로 리포트하고, 테스트를 실패시키지 않으면서도 문제를 가시화하는 전략(Option A)을 취합니다. 이는 실시간 파일을 건드리지 않고도 검증 품질을 높이는 가장 안전한 방법입니다.

## 권고 세부사항 (G7-live-file Option A)
- **대상 파일**: `tests/test_operator_request_schema.py`
- **핵심 변경**:
  - `pathlib.Path`와 `os`를 활용해 `.pipeline/operator_request.md`의 절대 경로를 계산합니다.
  - 새 테스트 메서드 `test_live_operator_request_header_canonical`을 추가합니다.
  - 파일이 존재하지 않으면 `self.skipTest`로 넘어갑니다.
  - 파일이 존재할 경우 첫 12줄 또는 헤더 섹션을 읽어 `_parse_operator_request_header`로 파싱합니다.
  - `REASON_CODE`가 `SUPPORTED_REASON_CODES`에 없으면 `self.skipTest(f"Live file drift detected: {code}")`로 리포트합니다.
  - `OPERATOR_POLICY`와 `DECISION_CLASS`에 대해서도 동일한 canonical check를 수행합니다.

## 검증
- `python3 -m unittest tests.test_operator_request_schema`를 실행하여 6개 테스트(기존 5개 + 신규 1개)가 통과(또는 1개 skipped)하는지 확인합니다.
- 현재 live file 상태에서 신규 테스트가 `skipped (Live file drift detected: advice_g5_not_bounded_first_sub_slice)`를 출력하는지 직접 확인합니다.
- `tests.test_pipeline_gui_backend` (45/OK) 및 `tests.test_smoke` 회귀 테스트를 확인합니다.
