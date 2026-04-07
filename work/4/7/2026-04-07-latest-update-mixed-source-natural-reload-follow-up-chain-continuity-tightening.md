# latest-update mixed-source natural-reload follow-up chain continuity tightening

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
- mixed-source latest-update 자연어 reload 후 follow-up/second-follow-up에서 `verification_label`이 `공식+기사 교차 확인`에서 `단일 출처 참고`로, `source_roles`가 `['보조 기사', '공식 기반']`에서 `['보조 기사']`로, source path가 2개에서 1개로 drift하는 현상이 direct probe에서 확인되었습니다.
- explicit contract가 service/browser/docs 어디에도 없었으므로, 이를 잠가 regression을 감지할 수 있게 해야 합니다.

## 핵심 변경
1. **service test 2개 추가**
   - `test_handle_chat_latest_update_mixed_source_natural_reload_follow_up_preserves_response_origin_and_source_paths`: 자연어 reload → first follow-up에서 badge=WEB, answer_mode=latest_update, verification_label=공식+기사 교차 확인, source_roles=[보조 기사, 공식 기반], source_paths 2개 유지
   - `test_handle_chat_latest_update_mixed_source_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`: 자연어 reload → first follow-up → second follow-up에서 동일 exact field 유지
2. **Playwright scenario 60, 61 추가**
   - scenario 60: mixed-source natural-reload → follow-up에서 origin badge, answer-mode badge, origin detail, context box assert
   - scenario 61: mixed-source natural-reload → first follow-up → second follow-up에서 동일 assert
3. **docs truth-sync**: README (scenario 60-61 설명), ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG, NEXT_STEPS (count 59→61)

## 검증
- `python3 -m unittest -v` 2 tests OK (0.091s)
- Playwright scenario 60: 1 passed (8.0s)
- Playwright scenario 61: 1 passed (7.5s)
- `git diff --check`: clean

## 남은 리스크
- single-source, news-only의 자연어 reload follow-up chain contract는 아직 없으며 별도 슬라이스 대상입니다.
- mixed-source follow-up chain에서 verification_label/source_roles/source_paths가 drift하는 runtime 버그 자체는 이 슬라이스에서 고치지 않았습니다 (contract 추가만). direct probe에서는 정상 동작했으나, 향후 regression이 발생하면 이 테스트로 감지됩니다.
