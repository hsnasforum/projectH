# entity-card dual-probe natural-reload follow-up source-path continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_dual_probe_natural_reload_follow_up_preserves_source_paths` 추가
- `e2e/tests/web-smoke.spec.mjs` — entity-card dual-probe natural-reload follow-up source-path continuity scenario 1건 추가 (scenario 43)
- `README.md` — scenario 43 추가
- `docs/ACCEPTANCE_CRITERIA.md` — dual-probe natural-reload follow-up source-path continuity criteria 추가
- `docs/MILESTONES.md` — dual-probe natural-reload follow-up source-path continuity smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 49 추가
- `docs/NEXT_STEPS.md` — scenario count 42→43 갱신, dual-probe natural-reload follow-up source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- dual-probe natural-reload의 show-only source-path(scenario 41)와 exact-field(scenario 42)는 잠겼지만, natural reload 후 follow-up에서 source-path가 context box에 유지되는지는 미검증

## 핵심 변경

- **서비스 테스트**: entity search → 자연어 reload → `load_web_search_record_id + user_text` follow-up에서 `active_context.source_paths`에 `pearlabyss.com` dual-probe URL 보존 assert
- **브라우저 smoke**: pre-seeded dual-probe record → click reload(세션 등록) → 자연어 reload → follow-up → `#context-box`에 dual-probe URL 포함 assert

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_follow_up_preserves_source_paths` — OK (0.061s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.8s)
- `make e2e-test` — 생략 (shared browser helper 미변경)

## 남은 리스크

- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
- **history-card reload family 전체 평가**: 이 세션에서 scenario 18-43 (26건) 추가. entity-card/latest-update × show-only/follow-up/noisy/source-path/verification-label/natural-reload의 주요 조합이 service+browser로 모두 잠김. 이 family의 remaining risk는 매우 낮으며, 다음 라운드에서는 다른 user-visible quality axis로의 전환을 권고함
