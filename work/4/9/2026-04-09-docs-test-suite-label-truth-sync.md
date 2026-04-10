# docs: ARCHITECTURE ACCEPTANCE_CRITERIA test-suite label truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 응답 페이로드 테스트 잠금 문구(line 167)에서 `browser smoke tests` → `Python smoke tests` 수정, Playwright 구분 문장 추가
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 문구(line 121)에서 동일 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `tests/test_smoke.py`는 Python unittest 스모크 스위트이며 브라우저 테스트가 아님(`tests/test_smoke.py:1-14`)
- 실제 브라우저 스모크는 Playwright `e2e/tests/web-smoke.spec.mjs`
- 기존 문서 다른 곳(`README.md:110`, `docs/ARCHITECTURE.md:1313`)에서도 이미 구분
- 응답 페이로드 섹션만 잘못된 라벨 사용

## 핵심 변경
- `browser smoke tests (tests/test_smoke.py)` → `Python smoke tests (tests/test_smoke.py)`
- `Playwright browser smoke (e2e/tests/web-smoke.spec.mjs) covers the browser-visible contract separately.` 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 각 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 테스트 스위트 라벨 진실 동기화 완료
