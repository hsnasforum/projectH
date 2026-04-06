# history-card reload transcript timestamp smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (+3 lines, 빈 줄 포함)

## 사용 skill
- 없음 (단일 파일 2줄 assertion + 1줄 빈 줄 추가)

## 변경 이유
- `history-card 다시 불러오기 클릭 후 response origin badge와 answer-mode badge가 유지됩니다` scenario는 remaining 후보 중 transcript/timeline rerender path를 실제로 타는 유일한 browser-visible reload flow였음
- cancel은 이전 라운드에서 inapplicable로 정리되었고, claim-coverage와 web-search history badges는 helper/render path라 transcript timestamp와 무관

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs` history-card reload scenario에서 `originDetail` assertion 이후, cleanup 이전에 transcript `.message-when` first/last regex assertion 2개 추가
- assertion shape: `/오[전후]\s\d{1,2}:\d{2}/` (earlier scenarios와 동일)

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (2.9m)
- `python3 -m unittest -v tests.test_web_app`: 생략 (test-only Playwright tightening, Python 코드 변경 없음)

## 남은 리스크
- claim-coverage와 web-search history badges scenario는 helper/render path로 transcript message path와 다르며, timestamp assertion 대상이 아닌 것으로 판단
- cancel scenario는 이전 라운드에서 inapplicable 판정 완료
- 이번 라운드로 transcript timeline rerender path를 타는 모든 browser-visible flow에 `.message-when` assertion이 추가됨
