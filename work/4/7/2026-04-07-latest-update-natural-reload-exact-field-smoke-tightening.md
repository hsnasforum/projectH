# latest-update natural-reload exact-field smoke tightening

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
- latest-update 자연어 reload(`방금 검색한 결과 다시 보여줘`)가 mixed-source, single-source, news-only 세 branch 모두에서 runtime 정상 동작하지만, explicit contract가 service/browser/docs에 없거나 불완전했습니다.
- mixed/single은 service test만 있었고 source_paths assert가 빠져 있었으며, news-only는 service test 자체가 없었습니다.
- browser와 docs에는 latest-update 자연어 reload contract가 전혀 없었습니다.

## 핵심 변경
1. **service test**
   - 기존 `test_handle_chat_mixed_source_latest_update_reload_exact_fields`에 `source_paths` assert 추가 (`store.steampowered.com`, `yna.co.kr`)
   - 기존 `test_handle_chat_single_source_latest_update_reload_exact_fields`에 `source_paths` assert 추가 (`example.com/seoul-weather`)
   - 새 `test_handle_chat_news_only_latest_update_reload_exact_fields` 추가: `actions_taken`, `web_search_record_path`, `badge=WEB`, `answer_mode=latest_update`, `verification_label=기사 교차 확인`, `source_roles=[보조 기사]`, `source_paths`에 `hankyung.com`, `mk.co.kr` 유지
2. **Playwright scenario 57, 58, 59 추가**
   - scenario 57: mixed-source 자연어 reload → origin badge, answer-mode badge, origin detail, context box assert
   - scenario 58: single-source 자연어 reload → 동일 assert
   - scenario 59: news-only 자연어 reload → 동일 assert
3. **docs truth-sync**: README (scenario 57-59 설명), ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG, NEXT_STEPS (count 56→59)

## 검증
- `python3 -m unittest -v` 3 tests OK (0.072s)
- Playwright scenario 57: 1 passed (7.7s)
- Playwright scenario 58: 1 passed (7.2s)
- Playwright scenario 59: 1 passed (7.3s)
- `git diff --check`: clean

## 남은 리스크
- latest-update 자연어 reload initial contract가 3 branch 모두 닫혔습니다.
- 자연어 reload 후 follow-up, second-follow-up은 아직 contract가 없으며, 별도 슬라이스 대상입니다.
