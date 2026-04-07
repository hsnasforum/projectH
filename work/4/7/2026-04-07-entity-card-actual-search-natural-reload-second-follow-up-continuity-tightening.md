# entity-card actual-search natural-reload second-follow-up continuity tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (신규 서비스 테스트 + 신규 브라우저 scenario + docs sync)

## 변경 이유
- actual-search natural-reload second-follow-up에서 response-origin + source-path continuity가 잠기지 않았음
- direct probe에서 4단계 flow 모두 정상 유지 확인

## 핵심 변경
1. **서비스 (신규)**: `test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` — 4단계 flow 후 `badge=WEB`, `answer_mode=entity_card`, `verification_label=설명형 다중 출처 합의`, `source_roles=["백과 기반"]`, source_paths assertion
2. **브라우저 (scenario 53, 신규)**: `entity-card 붉은사막 자연어 reload 후 두 번째 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다` — natural reload → first follow-up → second follow-up 후 badge/origin detail/context-box assertion
3. **docs**: scenario count 52→53, README 1곳, ACCEPTANCE_CRITERIA 1곳, MILESTONES 1곳, TASK_BACKLOG 1곳, NEXT_STEPS 1곳

## 검증
- `python3 -m unittest -v ...actual_entity_search_natural_reload_second_follow_up_preserves_response_origin_and_source_paths` → OK (0.072s)
- `cd e2e && npx playwright test ... -g "entity-card 붉은사막 자연어 reload 후 두 번째 follow-up에서..."` → 1 passed (7.8s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- actual-search natural-reload family는 show-only 40/46 + first follow-up 45/47 + second follow-up 53까지 완료
- 전체 entity-card source-path + response-origin continuity tightening 완료
