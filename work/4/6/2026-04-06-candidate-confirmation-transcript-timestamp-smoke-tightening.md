# candidate confirmation transcript timestamp smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (+2 lines)

## 사용 skill
- 없음 (단일 파일 2줄 추가)

## 변경 이유
- `candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다` scenario는 per-message timestamp contract를 아직 smoke에서 잠그지 않은 next unprotected later flow였음
- 이전 라운드에서 corrected-save family 2건을 닫았으므로, 다음 unprotected flow인 candidate confirmation 1건을 잠그는 것이 가장 작은 current-risk reduction

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs` candidate confirmation scenario 끝(755줄 직전)에 transcript `.message-when` first/last regex assertion 2개 추가
- assertion shape: `/오[전후]\s\d{1,2}:\d{2}/` (earlier scenarios와 동일)

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (2.9m)
- `python3 -m unittest -v tests.test_web_app`: 생략 (test-only Playwright tightening, Python 코드 변경 없음)

## 남은 리스크
- aggregate scenario는 아직 transcript timestamp assertion 미보호
- 이번 라운드에서 의도적으로 candidate confirmation 1건만 닫음
