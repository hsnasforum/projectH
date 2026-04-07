# latest-update noisy-community click-reload follow-up chain exclusion tightening

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
- noisy-community exclusion의 자연어 reload follow-up chain은 이전 라운드에서 닫혔으나, click-reload(`다시 불러오기`) 뒤 follow-up/second-follow-up chain에 대한 negative contract가 아직 없었습니다.
- same-family risk reduction으로 click-reload path도 동일 패턴으로 방어해야 합니다.

## 핵심 변경
1. **service test 2개 추가**
   - `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_follow_up`: click reload → follow-up에서 noisy 미노출 + 기사 교차 확인 유지
   - `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload_second_follow_up`: click reload → second follow-up에서 동일
2. **Playwright scenario 68, 69 추가**
   - scenario 68: click-reload → follow-up에서 positive+negative assertions
   - scenario 69: click-reload → second follow-up에서 동일
3. **docs truth-sync**: README (scenario 68-69), ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG (74-75), NEXT_STEPS (count 69)

## 검증
- `python3 -m unittest -v` 2 tests OK (0.089s)
- Playwright scenario 68: 1 passed (7.8s)
- Playwright scenario 69: 1 passed (7.3s)
- `git diff --check`: clean

## 남은 리스크
- latest-update noisy-community exclusion이 자연어 reload, click reload, follow-up, second-follow-up 전체 경로에서 explicit contract로 닫혔습니다.
- entity-card noisy-source exclusion의 follow-up chain은 별도 슬라이스 대상입니다.
