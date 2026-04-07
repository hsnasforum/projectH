# latest-update noisy-community natural-reload follow-up chain exclusion tightening

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
- latest-update continuity family의 positive contract는 닫혔으나, noisy-community exclusion의 자연어 reload follow-up chain에 대한 negative contract가 service/browser/docs 어디에도 없었습니다.
- 이전 라운드에서 follow-up chain 회귀가 실제로 발생한 적 있으므로, noisy-source exclusion도 동일 패턴으로 방어해야 합니다.

## 핵심 변경
1. **service test 2개 추가**
   - `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_follow_up`: 자연어 reload → follow-up에서 badge=WEB, verification_label=기사 교차 확인, source_roles=[보조 기사], 보조 커뮤니티/brunch 미노출, brunch.co.kr source_paths 미포함, hankyung.com/mk.co.kr 유지
   - `test_handle_chat_latest_update_noisy_source_excluded_after_natural_reload_second_follow_up`: 자연어 reload → second follow-up에서 동일 exact field
2. **Playwright scenario 66, 67 추가**
   - scenario 66: noisy-community natural-reload → follow-up에서 positive+negative assertions
   - scenario 67: noisy-community natural-reload → second follow-up에서 동일 assertions
3. **docs truth-sync**: README (scenario 66-67), ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG (72-73), NEXT_STEPS (count 67)

## 검증
- `python3 -m unittest -v` 2 tests OK (0.085s)
- Playwright scenario 66: 1 passed (7.8s)
- Playwright scenario 67: 1 passed (7.3s)
- `git diff --check`: clean

## 남은 리스크
- noisy-community exclusion이 자연어 reload, click reload, follow-up, second-follow-up 전체에서 explicit contract로 잠긴 상태입니다.
- entity-card noisy-source exclusion의 follow-up chain은 별도 슬라이스 대상입니다.
