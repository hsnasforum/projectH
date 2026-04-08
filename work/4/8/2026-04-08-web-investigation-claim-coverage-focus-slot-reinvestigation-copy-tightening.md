# Web Investigation claim-coverage focus-slot reinvestigation copy tightening

## 변경 파일

- `app/static/app.js`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `README.md`

## 사용 skill

- 없음

## 변경 이유

재조사 대상 슬롯(`is_focus_slot`)의 진행 상태가 `재조사 대상 ·` prefix, `변화: ...` 메타 파트, 글로벌 힌트에 분산되어 있어 사용자가 해당 슬롯이 실제로 보강됐는지, 단일 출처로 남았는지, 아직 미확인인지 한눈에 파악하기 어려웠음. `docs/PRODUCT_SPEC.md:293`의 `clearer slot-level reinvestigation UX` 항목에 해당.

## 핵심 변경

### app/static/app.js
1. `buildFocusSlotExplanation(item)` 함수 추가: focus-slot의 `status_label`, `previous_status_label`, `progress_state`를 조합하여 한 줄 plain-language 설명 생성
   - improved: `→ 재조사 결과: {prev} → {curr}으로 보강되었습니다.`
   - 단일 출처 유지: `→ 재조사 대상이지만, 아직 단일 출처 상태입니다. 추가 교차 검증이 권장됩니다.`
   - 미확인 유지: `→ 재조사 대상이지만, 아직 확인되지 않았습니다. 추가 출처가 필요합니다.`
   - 교차 확인 상태: `→ 재조사 대상이며, 현재 교차 확인 상태입니다.`
2. `renderClaimCoverage`에서 `is_focus_slot`인 경우 전용 설명 라인 출력, 기존 `단일 출처`/`미확인` 일반 힌트와 `변화:` 메타 파트는 focus-slot에서 제외

### e2e/tests/web-smoke.spec.mjs
- `renderClaimCoverage` 직접 호출 시나리오 2개 추가:
  - 단일 출처/미확인 focus-slot 설명 라인 렌더링 확인
  - improved focus-slot의 보강 설명 확인

### docs/PRODUCT_SPEC.md
- `clearer slot-level reinvestigation UX`를 In Progress에서 제거, Implemented에 slot-level reinvestigation UX 불릿 추가

### docs/ACCEPTANCE_CRITERIA.md
- focus-slot 전용 설명 라인 browser contract 추가

### README.md
- Playwright 시나리오 80, 81번 추가

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`: OK
- Playwright `claim-coverage panel은 재조사 대상 슬롯의 진행 상태를 명확히 렌더링합니다`: 1 passed
- Playwright `claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다`: 1 passed
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- full browser suite (`make e2e-test`)는 재실행하지 않아 무관한 시나리오 drift는 미확인.
- `buildFocusSlotExplanation`이 커버하지 않는 edge case (예: `progress_state`가 `regressed`인 경우)는 현재 백엔드에서 생성하지 않지만, 향후 추가 시 fallback 문구(`재조사 대상 슬롯입니다`)로 처리됨.
- `core/agent_loop.py`는 이번 슬라이스에서 변경하지 않았으므로, backend payload 구조는 기존과 동일.
