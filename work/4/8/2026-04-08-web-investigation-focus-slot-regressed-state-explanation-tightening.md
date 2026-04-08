# Web Investigation focus-slot regressed-state explanation tightening

## 변경 파일

- `app/static/app.js`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `README.md`

## 사용 skill

- 없음

## 변경 이유

이전 슬라이스에서 `buildFocusSlotExplanation()`이 improved/unchanged 케이스를 처리했지만, 백엔드가 이미 `progress_state: "regressed"` 상태를 생성하고 있음에도 브라우저는 generic fallback(`→ 재조사 대상 슬롯입니다.`)으로 처리하고 있었음. 사용자가 슬롯이 약해졌다는 정보를 한눈에 파악할 수 없는 user-visible gap이었음.

## 핵심 변경

### app/static/app.js
- `buildFocusSlotExplanation()`에 `progress_state === "regressed"` 분기 추가
- 출력: `→ 재조사 결과: {prev} → {curr}으로 약해졌습니다. 추가 교차 검증이 권장됩니다.`
- 백엔드 summary 언어(`약해졌습니다`)와 일관성 유지

### e2e/tests/web-smoke.spec.mjs
- `renderClaimCoverage` 직접 호출 시나리오 1개 추가: regressed focus-slot의 약화 설명 확인

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- slot-level reinvestigation UX 설명에 `regressed` 케이스 추가

### README.md
- Playwright 시나리오 82번 추가

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`: OK
- Playwright `claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다`: 1 passed
- Playwright `claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다`: 1 passed
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- full browser suite (`make e2e-test`)는 재실행하지 않음.
- `buildFocusSlotExplanation`의 regressed 분기는 `prev`/`curr`가 모두 있어야 동작. 둘 중 하나가 빈 문자열이면 generic fallback으로 처리됨.
