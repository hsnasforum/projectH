# 2026-04-28 M61 Axis 1 Correction Summary Endpoint

## 변경 파일
- `app/handlers/aggregate.py`
- `app/web.py`
- `tests/test_correction_summary.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m61-axis1-correction-summary-endpoint.md`

## 사용 skill
- `security-gate`: correction store 요약을 읽는 read-only GET endpoint 경계를 확인했습니다. 승인, 저장, overwrite, 삭제, 외부 네트워크, 로그 payload 변경은 없습니다.
- `doc-sync`: M61 Axis 1 진행 사실을 `docs/MILESTONES.md`에만 반영했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- M54-M60에서 correction/task log 타입 표면이 정리된 뒤, correction memory 현황을 확인할 수 있는 최소 요약 API가 필요했습니다.
- handoff의 M61 Axis 1 범위에 맞춰 correction store의 전체 개수, status별 개수, 상위 recurring fingerprint 요약을 반환하는 endpoint를 추가했습니다.

## 핵심 변경
- `AggregateHandlerMixin.get_correction_summary()`를 추가해 `total`, `by_status`, `top_recurring_fingerprints`를 반환하도록 했습니다.
- `GET /api/corrections/summary` route를 `app/web.py`의 기존 GET 처리 흐름에 추가했습니다.
- `tests/test_correction_summary.py`를 추가해 빈 store와 recurring correction store 요약 결과를 검증했습니다.
- `docs/MILESTONES.md`에 M61 Correction Analytics / Axis 1 항목을 추가했습니다.
- `core/contracts.py`, frontend, dist, E2E, preference store는 변경하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile app/handlers/aggregate.py app/web.py tests/test_correction_summary.py`
- 통과: `python3 -m unittest -v tests.test_correction_summary` (2 tests OK)
- 통과: `git diff --check -- app/handlers/aggregate.py app/web.py tests/test_correction_summary.py docs/MILESTONES.md`

## 남은 리스크
- 로컬 브랜치 `feat/m61-correction-analytics`를 `origin/main`에서 만들려 했지만 `.git/index.lock` 생성이 읽기 전용 파일시스템으로 막혀 실패했습니다. handoff가 현재 브랜치에서도 실행 가능하다고 명시해 현재 브랜치에서 작업을 계속했습니다.
- 이번 변경은 read-only summary endpoint와 단위 테스트에 한정되어 브라우저/E2E, 전체 unittest는 실행하지 않았습니다.
- GET route의 실제 HTTP 왕복 테스트는 추가하지 않았습니다. 단위 테스트는 `AggregateHandlerMixin.get_correction_summary()`의 payload 계약을 검증합니다.
