# history-card latest-update noisy-community click-reload initial exclusion exact-field smoke clarification

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 1573 부근, initial click-reload noisy-community scenario)

## 사용 skill

- 없음 (smoke test clarification only)

## 변경 이유

- initial click-reload noisy-community scenario title은 `본문과 origin detail에 노출되지 않습니다`로만 되어 있었고, body assertion에 context box positive/negative assertion이 빠져 있었음
- current docs (MILESTONES:51, TASK_BACKLOG:40, README:133, ACCEPTANCE:1342)는 context box exclusion까지 shipped truth로 적고 있음
- same-family follow-up/second-follow-up pattern(6106, 6173)은 이미 context box `hankyung.com`, `mk.co.kr` positive + `brunch` negative assertion을 포함
- initial scenario도 동일 contract로 정렬

## 핵심 변경

- title: `본문과 origin detail에 노출되지 않습니다` → `본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다`
- body: context box `hankyung.com`, `mk.co.kr` positive assertion + `brunch` negative assertion 추가

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean
- `npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source"` → 1 passed (6.3s)

## 남은 리스크

- 없음. initial scenario만 변경, follow-up/second-follow-up/natural-reload/docs는 무변경.
