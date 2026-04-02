STATUS: implement

완료 슬라이스: `document summary length control only`

근거 pair:
- latest `/work`: `work/4/2/2026-04-02-document-summary-length-control.md`
- latest same-day `/verify`: (아직 없음)

이번 slice 범위:
- `core/agent_loop.py` — 3개 local document summary 프롬프트에 Target length 지시 추가
- mock adapter 동작 변경 없음, Ollama 런타임에서만 실제 효과

operator 결정 기록:
- React frontend → parked
- parallel stress hardening → current shipped 바깥
- accessibility polish family → 닫힘

검증:
- `python3 -m unittest -v tests.test_web_app` — 187 tests OK
- `python3 -m unittest discover -s tests -p 'test_smoke*'` — 96 tests OK
