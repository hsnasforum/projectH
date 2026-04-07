# latest-update single-source/news-only natural-reload follow-up chain continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- latest-update 자연어 reload follow-up chain에서 mixed-source는 이전 라운드에서 닫혔으나, single-source와 news-only의 자연어 reload → follow-up → second-follow-up continuity contract가 service/browser/docs 어디에도 없었습니다.
- direct probe에서는 둘 다 정상 유지되는 것이 확인되었으므로, 이를 explicit contract로 잠가야 합니다.

## 핵심 변경
1. **service test 4개 추가**
   - single-source natural-reload follow-up: badge=WEB, answer_mode=latest_update, verification_label=단일 출처 참고, source_roles=[보조 출처], source_paths에 example.com/seoul-weather
   - single-source natural-reload second-follow-up: 동일 exact field
   - news-only natural-reload follow-up: badge=WEB, answer_mode=latest_update, verification_label=기사 교차 확인, source_roles=[보조 기사], source_paths에 hankyung.com, mk.co.kr
   - news-only natural-reload second-follow-up: 동일 exact field
2. **Playwright scenario 62, 63, 64, 65 추가**
   - scenario 62: single-source 자연어 reload → follow-up
   - scenario 63: single-source 자연어 reload → second follow-up
   - scenario 64: news-only 자연어 reload → follow-up
   - scenario 65: news-only 자연어 reload → second follow-up
3. **docs truth-sync**: README (scenario 62-65 설명), ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG (68-71), NEXT_STEPS (count 65)

## 검증
- `python3 -m unittest -v` 4 tests OK (0.147s)
- Playwright scenario 62: 1 passed (7.7s)
- Playwright scenario 63: 1 passed (7.3s)
- Playwright scenario 64: 1 passed (7.3s)
- Playwright scenario 65: 1 passed (7.3s)
- `git diff --check`: clean

## 남은 리스크
- latest-update 자연어 reload follow-up chain이 mixed-source, single-source, news-only 3 branch 모두 닫혔습니다.
- latest-update continuity family 전체(click-reload, natural-reload, follow-up, second-follow-up)가 3 branch 모두 explicit contract로 잠긴 상태입니다.
