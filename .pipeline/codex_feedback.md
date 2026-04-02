STATUS: implement

완료 슬라이스: `legacy shell response-box / transcript duplication cleanup only`

근거 pair:
- latest `/work`: `work/4/2/2026-04-02-response-box-transcript-duplication-cleanup.md`
- latest same-day `/verify`: (아직 없음 — 이번 `/work`가 먼저 남겨짐)

이번 slice 범위:
- `app/static/style.css` — `#response-text` visually hidden 처리 (CSS-only, 1건)
- JS/backend 변경 없음

구현 이유:
- operator가 후보 C를 선택함: response-box / transcript 중복 UX 정리
- A(병렬 stress hardening)는 current shipped single-worker contract 바깥
- B(React 방향 확정)는 parked/remove/serve 결정 선행 필요

검증:
- `python3 -m unittest -v tests.test_web_app` — 187 tests OK
- `make e2e-test` — 16/16 passed
