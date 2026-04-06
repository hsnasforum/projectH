# cancel transcript timestamp smoke tightening — 적용 불가 판정

## 변경 파일
- 없음 (변경 시도 후 되돌림)

## 사용 skill
- 없음

## 변경 이유
- `스트리밍 중 취소 버튼이 동작합니다` scenario에 transcript `.message-when` first/last regex assertion 2개를 추가하려 했음
- handoff에서 cancel flow의 partial stream timing sensitivity를 인지하고 있었으나, 실제 시도 결과 assertion 추가가 current runtime 동작과 맞지 않아 되돌림

## 핵심 변경
- assertion 2개를 additive하게 추가했으나 E2E에서 실패
- 실패 원인: cancel scenario는 stream을 즉시 중단하므로 transcript에 `.message-when` 요소 자체가 렌더링되지 않음 (`element(s) not found`, timeout 15s)
- 이는 current runtime의 정상 동작이며, cancel 시 partial response만 남기는 shipped contract와 일치함
- assertion을 되돌려 `e2e/tests/web-smoke.spec.mjs`에 최종 변경 없음

## 검증
- `make e2e-test` (assertion 추가 상태): 1 failed (`스트리밍 중 취소 버튼이 동작합니다` — `element(s) not found`)
- `git diff --stat -- e2e/tests/web-smoke.spec.mjs` (되돌린 후): 빈 결과 (원래 상태 복원 확인)
- `python3 -m unittest -v tests.test_web_app`: 생략 (코드 변경 없음)

## 남은 리스크
- cancel scenario의 transcript timestamp는 현재 runtime이 렌더링하지 않으므로 smoke assertion 대상이 아님
- cancel 후 transcript에도 timestamp를 보여주려면 runtime 변경이 필요하며, 이는 별도 product decision
- claim-coverage, web-search history badges, history-card reload scenario는 helper/render path 또는 secondary web mode로 별도 판단 필요
