# corrected-save late reject / re-correct transcript timestamp smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (+2 lines)

## 사용 skill
- 없음 (단일 파일 2줄 추가)

## 변경 이유
- `corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다` scenario는 per-message timestamp contract를 아직 smoke에서 잠그지 않은 next unprotected later flow였음
- 이전 라운드에서 corrected-save first bridge를 닫았으므로, 같은 family 다음 1건을 잠그는 것이 가장 작은 current-risk reduction

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs` corrected-save late reject / re-correct scenario 끝(585줄 직전)에 transcript `.message-when` first/last regex assertion 2개 추가
- assertion shape: `/오[전후]\s\d{1,2}:\d{2}/` (earlier scenarios와 동일)

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (2.9m)
- `python3 -m unittest -v tests.test_web_app`: 생략 (test-only Playwright tightening, Python 코드 변경 없음)

## 남은 리스크
- candidate confirmation scenario, aggregate scenario는 아직 transcript timestamp assertion 미보호
- 이번 라운드에서 의도적으로 corrected-save family next unprotected flow 1건만 닫음
