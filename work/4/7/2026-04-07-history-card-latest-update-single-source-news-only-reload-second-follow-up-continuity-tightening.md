# history-card latest-update single-source/news-only reload second-follow-up continuity tightening

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
- latest-update second-follow-up family에서 mixed-source는 이전 라운드에서 닫혔으나, single-source와 news-only의 click-reload → first follow-up → second follow-up continuity contract가 service/browser/docs 어디에도 없었습니다.
- runtime 직접 probe에서는 둘 다 정상 유지되는 것이 확인되었으므로, 이를 explicit contract로 잠가야 합니다.

## 핵심 변경
1. **service test 2개 추가**
   - `test_handle_chat_latest_update_single_source_reload_second_follow_up_preserves_response_origin_and_source_paths`: badge=WEB, answer_mode=latest_update, verification_label=단일 출처 참고, source_roles=[보조 출처], source_paths에 example.com/seoul-weather 유지 확인
   - `test_handle_chat_latest_update_news_only_reload_second_follow_up_preserves_response_origin_and_source_paths`: badge=WEB, answer_mode=latest_update, verification_label=기사 교차 확인, source_roles=[보조 기사], source_paths에 hankyung.com, mk.co.kr 유지 확인
2. **Playwright scenario 55, 56 추가**
   - scenario 55: single-source click reload → first follow-up → second follow-up에서 origin badge, answer-mode badge, origin detail, context box 모두 assert
   - scenario 56: news-only click reload → first follow-up → second follow-up에서 동일 assert
3. **docs truth-sync**: README (scenario 55, 56 설명 + count 56), ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG, NEXT_STEPS 업데이트

## 검증
- `python3 -m unittest -v` 2 tests OK (0.103s)
- Playwright scenario 55: 1 passed (8.4s)
- Playwright scenario 56: 1 passed (7.6s)
- `git diff --check`: clean

## 남은 리스크
- latest-update second-follow-up family가 이제 mixed-source, single-source, news-only 세 갈래 모두 닫혔습니다.
- entity-card family의 second-follow-up은 별도로 이미 닫혀 있으므로 이 슬라이스에 포함하지 않았습니다.
