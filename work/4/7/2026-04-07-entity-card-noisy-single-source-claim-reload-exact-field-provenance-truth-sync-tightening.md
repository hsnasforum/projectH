# entity-card noisy single-source claim reload exact-field provenance truth-sync tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- entity-card noisy single-source claim의 initial reload(click/natural) exact path에서 provenance truth가 partial하거나 stale했습니다.
- service test에는 `response_origin` exact field, `blog.example.com` text 미노출, source_paths provenance가 빠져 있었습니다.
- browser click-reload noisy scenario는 `설명형 단일 출처` fixture를 사용하여 current runtime truth(`설명형 다중 출처 합의`)와 불일치했고, context-box provenance assertion이 없었습니다.

## 핵심 변경
1. **service test 2개 확장** (기존 initial reload test에 assertion 추가)
   - `test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload`: `blog.example.com` text 미노출, `response_origin` exact field(WEB/entity_card/설명형 다중 출처 합의/백과 기반), source_paths provenance(`blog.example.com` 포함) 추가
   - `test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload`: 동일 패턴 추가
2. **Playwright scenario 22 tighten** (click-reload noisy scenario)
   - fixture: `설명형 단일 출처` → `설명형 다중 출처 합의`
   - assertion: origin detail `설명형 다중 출처 합의`, 출시일/2025/blog.example.com 미노출, context-box provenance(`namu.wiki`, `ko.wikipedia.org`, `blog.example.com`) 추가
3. **docs truth-sync**: README 22번 rewording, ACCEPTANCE_CRITERIA 해당 항목 provenance 명시

## 검증
- `python3 -m unittest -v` 2 tests OK (0.082s)
- Playwright click-reload noisy scenario: 1 passed (7.8s)
- Playwright natural-reload badge scenario: 1 passed (7.3s)
- Playwright natural-reload source-path scenario: 1 passed (7.0s)
- `git diff --check`: clean

## 남은 리스크
- scenario count는 73 그대로 유지됩니다 (기존 scenario tighten, 신규 추가 없음).
- 자연어 reload의 generic 2-source fixture scenario(40, 46)는 noisy source를 포함하지 않으므로 provenance truth-sync 대상이 아닙니다.
