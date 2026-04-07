# entity-card noisy single-source claim click-reload follow-up chain exclusion tightening

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
- entity-card noisy single-source claim exclusion은 initial 검색, 자연어 reload, natural-reload follow-up chain까지 닫혔으나, click-reload 뒤 follow-up/second-follow-up chain에 대한 dedicated negative contract가 없었습니다.

## 핵심 변경
1. **service test 2개 추가**
   - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_follow_up`: click reload → follow-up에서 noisy claim 미노출 + entity_card contract 유지
   - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_history_card_reload_second_follow_up`: second follow-up에서 동일
2. **Playwright scenario 72, 73 추가**
   - scenario 72: click-reload → follow-up에서 positive+negative assertions
   - scenario 73: click-reload → second follow-up에서 동일
3. **docs truth-sync**: README (scenario 72-73), ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG (78-79), NEXT_STEPS (count 73)

## 검증
- `python3 -m unittest -v` 2 tests OK (0.136s)
- Playwright scenario 72: 1 passed (7.7s)
- Playwright scenario 73: 1 passed (7.5s)
- `git diff --check`: clean

## 남은 리스크
- entity-card noisy single-source claim exclusion이 natural-reload와 click-reload 전체 follow-up chain에서 explicit contract로 닫혔습니다.
- source_paths에는 noisy source URL이 provenance 목적으로 유지됩니다 (현재 runtime truth).
