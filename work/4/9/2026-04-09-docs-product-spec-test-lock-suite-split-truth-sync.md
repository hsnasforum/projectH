# docs: PRODUCT_SPEC response payload test-lock suite split truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 응답 페이로드 계약 섹션 끝(line 323)에 테스트 스위트 잠금 문구 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `docs/ARCHITECTURE.md:167`와 `docs/ACCEPTANCE_CRITERIA.md:121`는 이미 테스트 스위트 분할(Python smoke vs Playwright browser smoke)과 보정/저장 필드 앵커 잠금을 정확히 기술
- `docs/PRODUCT_SPEC.md`의 응답 페이로드 섹션에는 해당 정보 없음
- 3개 문서 간 정합 필요

## 핵심 변경
- `tests/test_web_app.py` + `tests/test_smoke.py`가 제어 필드와 보정/저장 필드 앵커를 잠근다는 문구 추가
- Playwright `e2e/tests/web-smoke.spec.mjs`가 브라우저 계약을 별도 커버한다는 구분 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 2줄 추가 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 계약 테스트 잠금 문구가 3개 문서 모두에서 정합 완료
