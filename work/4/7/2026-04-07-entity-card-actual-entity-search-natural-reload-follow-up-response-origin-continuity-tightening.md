# entity-card actual-entity-search natural-reload follow-up response-origin continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin` 추가
- `e2e/tests/web-smoke.spec.mjs` — entity-card 붉은사막 자연어 reload follow-up response-origin continuity scenario 1건 추가 (scenario 45)
- `README.md` — scenario 45 추가
- `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md` — count 44→45

## 사용 skill

- 없음

## 변경 이유

- actual entity-search natural-reload follow-up response-origin continuity가 service/browser 모두 미검증

## 핵심 변경

- 서비스: entity search → 자연어 reload → follow-up에서 answer_mode, verification_label, source_roles drift 없음 assert
- 브라우저: pre-seeded record → click reload(세션 등록) → 자연어 reload → follow-up → WEB, 설명 카드, 설명형 단일 출처, 백과 기반 assert

## 검증

- `python3 -m unittest` — OK (0.043s)
- Playwright — 1 passed (7.1s)
- `git diff --check` — 통과

## 남은 리스크

- full suite 미실행

## OPERATOR 권고: history-card reload family 종결 선언

**이 세션에서 history-card reload family smoke tightening을 scenario 18→45 (28건) 연속 수행했습니다.**

닫힌 조합:
- entity-card / latest-update × show-only / follow-up / noisy exclusion / source-path / verification-label
- mixed-source / single-source / news-only × reload / follow-up / source-path
- zero-strong-slot × click reload / follow-up / natural reload / natural reload follow-up
- dual-probe × click reload / follow-up / natural reload / natural reload follow-up (source-path + exact-field)
- actual entity-search × natural reload / natural reload follow-up

**이 family는 실질적으로 닫혔습니다. 추가 micro-variant는 marginal risk reduction이 극히 낮습니다.**

다음 라운드에서 전환 가능한 user-visible axis:
1. reviewed-memory effect activation / stop-apply / reversal browser coverage
2. investigation quality / source-ranking browser coverage
3. PDF text-layer browser coverage
4. `make e2e-test` full suite 통합 확인 (현재 45 scenarios isolated rerun만 확인)
