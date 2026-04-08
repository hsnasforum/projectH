# Web Investigation focus-slot transition copy particle normalization

## 변경 파일

- `app/static/app.js`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`

## 사용 skill

- 없음

## 변경 이유

`buildFocusSlotExplanation()`이 `${curr}으로`를 리터럴로 붙여서 `단일 출처으로 약해졌습니다`처럼 부자연스러운 한국어가 브라우저에 노출되고 있었음. 한국어 문법상 받침이 없거나 ㄹ 받침이면 `로`, 그 외이면 `으로`를 사용해야 함.

## 핵심 변경

### app/static/app.js
1. `selectParticleEuroRo(text)` helper 추가: 마지막 글자의 종성을 검사하여 `으로`/`로` 선택
2. `buildFocusSlotExplanation()`에서 improved/regressed 문구의 `으로`를 동적 조사로 교체
   - `단일 출처 → 교차 확인으로 보강` (확인 = ㄴ 받침 → 으로, 정상)
   - `교차 확인 → 단일 출처로 약해짐` (처 = 받침 없음 → 로, 수정됨)

### e2e/tests/web-smoke.spec.mjs
- regressed 시나리오 assertion: `단일 출처으로` → `단일 출처로`

### README.md
- 시나리오 82번 문구: `단일 출처으로` → `단일 출처로`

## 검증

- Playwright `claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다`: 1 passed
- Playwright `claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다`: 1 passed
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- full browser suite 미재실행.
- `selectParticleEuroRo`는 한글 음절 범위 밖의 문자열에 대해 `으로` fallback. 현재 `status_label` 값은 모두 한글이므로 문제 없음.
