# history-card latest-update mixed-source reload second-follow-up continuity tightening

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
- latest-update mixed-source click-reload second-follow-up에서 response-origin + source-path continuity가 잠기지 않았음
- direct probe에서 4단계 flow 모두 정상 유지 확인

## 핵심 변경
1. **서비스 (신규)**: `test_handle_chat_latest_update_mixed_source_reload_second_follow_up_preserves_response_origin_and_source_paths` — 4단계 flow 후 `badge=WEB`, `answer_mode=latest_update`, `verification_label=공식+기사 교차 확인`, `source_roles=["보조 기사", "공식 기반"]`, source_paths assertion
2. **브라우저 (scenario 54, 신규)**: click reload → first follow-up → second follow-up 후 `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`, `store.steampowered.com`, `yna.co.kr` assertion
3. **docs**: scenario count 53→54, README 1곳, ACCEPTANCE_CRITERIA 1곳, MILESTONES 1곳, TASK_BACKLOG 1곳, NEXT_STEPS 1곳

## 검증
- `python3 -m unittest -v ...latest_update_mixed_source_reload_second_follow_up_preserves_response_origin_and_source_paths` → OK (0.055s)
- `cd e2e && npx playwright test ... -g "history-card latest-update mixed-source 다시 불러오기 후 두 번째 follow-up..."` → 1 passed (7.8s)
- `git diff --check` → whitespace error 없음

## 남은 리스크
- latest-update mixed-source second-follow-up 완료
- single-source, news-only latest-update second-follow-up은 별도 슬라이스 필요 시 추가
