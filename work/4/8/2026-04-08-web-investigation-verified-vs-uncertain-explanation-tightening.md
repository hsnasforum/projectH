# Web Investigation verified-vs-uncertain explanation tightening

## 변경 파일

- `core/agent_loop.py`
- `app/static/app.js`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `README.md`

## 사용 skill

- 없음

## 변경 이유

사용자가 응답 본문의 섹션 헤더(`확인된 사실`, `단일 출처 정보`, `확인되지 않은 항목`)와 claim-coverage 패널의 상태 태그(`교차 확인`, `단일 출처`, `미확인`) 간의 연결을 추론해야 했음. `docs/PRODUCT_SPEC.md:293`의 In Progress 항목 `stronger explanation of verified vs uncertain claims`에 해당.

## 핵심 변경

### core/agent_loop.py (응답 본문 섹션 헤더)
1. `확인된 사실:` → `확인된 사실 [교차 확인]:` (3곳: entity-card, latest-update confirmed, latest-update fallback)
2. `단일 출처 정보 (교차 확인 부족, 추가 확인 필요):` → `단일 출처 정보 [단일 출처] (추가 확인 필요):` (entity-card)
3. `단일 출처 정보 (교차 확인 필요):` → `단일 출처 정보 [단일 출처] (추가 확인 필요):` (latest-update)
4. `확인되지 않은 항목:` → `확인되지 않은 항목 [미확인]:` (entity-card)

### app/static/app.js (claim-coverage 패널 힌트)
- `교차 확인은 여러 출처 합의, 단일 출처는 신뢰 가능한 1개 출처 기준, 미확인은 추가 조사 필요 상태입니다.`
- → `[교차 확인] 여러 출처가 합의한 사실, [단일 출처] 1개 출처에서만 확인된 정보, [미확인] 추가 조사가 필요한 항목입니다.`

### docs/PRODUCT_SPEC.md
- Local Web Shell Implemented에 verified-vs-uncertain explanation 불릿 추가
- Local Web Shell In Progress에서 `stronger explanation of verified vs uncertain claims` 제거
- Web Investigation Rules Implemented에 status-tag annotation 불릿 추가

### docs/ACCEPTANCE_CRITERIA.md
- Implemented에 response-body section header annotation 불릿 추가

### README.md
- Playwright 시나리오 22번에서 `확인된 사실:` → `확인된 사실 [교차 확인]:` 업데이트

### 테스트 (test_smoke.py, test_web_app.py, web-smoke.spec.mjs)
- 모든 관련 assertion을 새 문구에 맞춰 업데이트

## 검증

- `python3 -m unittest tests.test_smoke tests.test_web_app`: 330 tests OK
- Playwright `claim-coverage panel` 시나리오: 1 passed
- Playwright `history-card entity-card 다시 불러오기` 시나리오: 1 passed
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `docs/PRODUCT_SPEC.md` Local Web Shell In Progress에 `clearer slot-level reinvestigation UX`가 아직 남아 있음 (별도 슬라이스).
- latest-update 경로의 `단일 출처 정보 [단일 출처]` 문구 변경은 해당 경로 전용 Playwright 시나리오에서는 직접 검증되지 않음 (unit test에서만 커버).
