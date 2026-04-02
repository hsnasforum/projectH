# 2026-04-02 search-results short-summary sparse-input character-range alignment

**범위**: `search_results` short-summary prompt 1곳의 sparse/single-result escape hatch에 문자 수 가이드 추가
**근거**: `verify/4/2/2026-04-02-search-results-short-summary-sparse-escape-hatch-verification.md` — 문장 수만 완화하고 문자 수 가이드가 빠져 있어 padding 압력이 남아 있던 same-family current-risk 축소

---

## 변경 파일

- `core/agent_loop.py` — `_build_short_summary_prompt`의 `search_results` 분기 `Target length:` 줄에서 sparse/single-result 예외를 `2~3 sentences (120~250 Korean characters) are acceptable`로 보정
- `tests/test_smoke.py` — `test_search_short_summary_sparse_input_escape_hatch`의 assertion을 문자 수 가이드 포함 wording으로 갱신

---

## 사용 skill

- 없음

---

## 변경 이유

직전 슬라이스에서 sparse/single-result 입력용 `2~3 sentences` 문장 수 예외를 추가했으나, 기본 `200~400 Korean characters` 가이드는 유지된 채여서 얇은 결과 집합에서도 문자 수 하한이 padding을 유도할 수 있었음. 같은 family의 마지막 current-risk reduction으로 문자 수 가이드를 `120~250 Korean characters`로 정렬.

---

## 핵심 변경

1. `core/agent_loop.py:971` — `"For sparse or single-result input, 2~3 sentences are acceptable."` → `"For sparse or single-result input, 2~3 sentences (120~250 Korean characters) are acceptable."`
2. `tests/test_smoke.py` — `test_search_short_summary_sparse_input_escape_hatch`의 assertIn 문자열을 `"For sparse or single-result input, 2~3 sentences (120~250 Korean characters) are acceptable"`로 갱신

---

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` — 통과
- `python3 -m unittest -v tests.test_smoke` — **99 tests OK** (1.287s)

---

## 남은 리스크

- `search_results` short-summary prompt의 sparse/single-result escape hatch가 문장 수 + 문자 수 모두 완화되어 이 family의 current-risk는 닫힌 상태
- prompt-level 길이 가이드는 soft constraint이므로 실제 출력 길이의 hard guarantee는 아님
- 다음 슬라이스는 같은 family가 아닌 새 quality axis 또는 다른 current-risk reduction으로 넘어가야 함
