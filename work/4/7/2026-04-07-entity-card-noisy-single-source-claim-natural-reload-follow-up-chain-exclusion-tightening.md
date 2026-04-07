# entity-card noisy single-source claim natural-reload follow-up chain exclusion tightening

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
- entity-card noisy single-source claim exclusion은 initial 검색과 자연어 reload까지만 잠겨 있었고, follow-up/second-follow-up chain에 대한 negative contract가 없었습니다.
- latest-update noisy family에서 follow-up chain 회귀가 실제로 발생한 전례가 있으므로, entity-card family도 동일 패턴으로 방어해야 합니다.

## 핵심 변경
1. **service test 2개 추가**
   - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up`: 자연어 reload → follow-up에서 badge=WEB, answer_mode=entity_card, verification_label=설명형 다중 출처 합의, source_roles=[백과 기반], 출시일/2025 미노출, namu.wiki/ko.wikipedia.org 유지
   - `test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up`: second follow-up에서 동일
2. **Playwright scenario 70, 71 추가**
   - scenario 70: natural-reload → follow-up에서 positive+negative assertions (origin detail, response text, context box)
   - scenario 71: natural-reload → second follow-up에서 동일
3. **docs truth-sync**: README (scenario 70-71), ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG (76-77), NEXT_STEPS (count 71)

## 검증
- `python3 -m unittest -v` 2 tests OK (0.162s)
- Playwright scenario 70: 1 passed (7.7s)
- Playwright scenario 71: 1 passed (7.4s)
- `git diff --check`: clean

## 남은 리스크
- source_paths에는 noisy source URL이 provenance 목적으로 유지됩니다. 이는 현재 runtime 동작과 일치하며, noisy exclusion은 텍스트/source_roles/origin_detail에서만 적용됩니다.
- click-reload variant의 entity-card noisy exclusion follow-up chain은 별도 슬라이스 대상입니다.
