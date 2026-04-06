# entity-card dual-probe natural-reload follow-up response-origin continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_dual_probe_natural_reload_follow_up_preserves_response_origin` 추가
- `e2e/tests/web-smoke.spec.mjs` — entity-card dual-probe natural-reload follow-up response-origin continuity scenario 1건 추가 (scenario 44)
- `README.md` — scenario 44 추가
- `docs/ACCEPTANCE_CRITERIA.md` — dual-probe natural-reload follow-up response-origin continuity criteria 추가
- `docs/MILESTONES.md` — dual-probe natural-reload follow-up response-origin continuity smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 50 추가
- `docs/NEXT_STEPS.md` — scenario count 43→44 갱신

## 사용 skill

- 없음

## 변경 이유

- scenario 43에서 dual-probe natural-reload follow-up source-path continuity를 잠갔지만, response-origin exact field (WEB, 설명 카드, 설명형 단일 출처, 백과 기반)는 미검증

## 핵심 변경

- **서비스 테스트**: entity search → 자연어 reload → follow-up에서 `answer_mode`, `verification_label`, `source_roles` exact-field 유지 assert
- **브라우저 smoke**: pre-seeded dual-probe record → click reload(세션 등록) → 자연어 reload → follow-up → `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반` assert

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_follow_up_preserves_response_origin` — OK (0.073s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` — 1 passed (6.9s)

## 남은 리스크

- full suite 미실행

## Operator 참고사항

이 세션에서 history-card reload family smoke tightening을 scenario 18→44 (27건) 연속 수행했습니다. entity-card/latest-update × show-only/follow-up/noisy exclusion/source-path/verification-label/natural-reload의 주요 조합이 모두 service+browser로 잠겼습니다. **이 family의 marginal risk reduction은 이미 매우 낮은 수준이며, 다음 라운드에서는 다른 user-visible quality axis로의 전환을 강하게 권고합니다.** 예: reviewed-memory effect activation browser coverage, investigation quality / source-ranking browser coverage, PDF text-layer browser coverage 등.
