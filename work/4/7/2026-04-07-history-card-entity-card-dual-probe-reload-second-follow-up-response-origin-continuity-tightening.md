# history-card entity-card dual-probe reload second-follow-up response-origin continuity tightening

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
- dual-probe click-reload second-follow-up에서 response-origin + source-path continuity가 잠기지 않았음
- direct probe에서 badge drift가 보고되었으나, 현재 코드에서는 `WEB` badge가 정상 유지됨을 확인 (runtime fix 불필요)
- service/browser/docs에 explicit lock 추가

## 핵심 변경
1. **서비스 (신규)**: `test_handle_chat_dual_probe_entity_card_history_card_reload_second_follow_up_preserves_stored_response_origin` — stored-record 기반 4단계 flow 후 `badge=WEB`, `answer_mode=entity_card`, `verification_label=설명형 다중 출처 합의`, `source_roles=["공식 기반", "백과 기반"]`, source_paths assertion
2. **브라우저 (scenario 51, 신규)**: `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe response origin badge와 answer-mode badge가 drift하지 않습니다` — click reload → first follow-up → second follow-up 후 badge/origin detail/context-box assertion
3. **docs**: scenario count 50→51, README 1곳, ACCEPTANCE_CRITERIA 1곳, MILESTONES 1곳, TASK_BACKLOG 1곳, NEXT_STEPS 1곳

## 검증
- `python3 -m unittest -v ...dual_probe_entity_card_history_card_reload_second_follow_up_preserves_stored_response_origin` → OK (0.057s)
- `cd e2e && npx playwright test ... -g "...dual-probe response origin badge와 answer-mode badge가 drift하지 않습니다"` → 1 passed (7.7s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- runtime badge drift는 현재 코드에서 재현되지 않음; 핸드오프 관찰과 다른 결과이므로 monitor 필요
- dual-probe click-reload second-follow-up family 완료
