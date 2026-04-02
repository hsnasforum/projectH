# 2026-04-02 search-results short-summary sparse-input escape hatch

**범위**: `search_results` short-summary prompt 1곳에 sparse/single-result 입력용 `2~3 sentences` 허용 문구 추가
**근거**: `verify/4/2/2026-04-02-search-results-chunk-note-target-length-verification.md` — same-family current-risk reduction으로, short-summary의 sparse 입력 시 불필요한 padding 유도 리스크 축소

---

## 변경 파일

- `core/agent_loop.py` — `_build_short_summary_prompt`의 `search_results` 분기 `Target length:` 줄에 `For sparse or single-result input, 2~3 sentences are acceptable.` 추가
- `tests/test_smoke.py` — `test_search_short_summary_sparse_input_escape_hatch` regression 1개 추가

---

## 사용 skill

- 없음

---

## 변경 이유

이전 슬라이스에서 `search_results` summary family 세 prompt 모두에 `Target length:` 가이드를 추가하여 "길이 가이드 없음" 리스크를 닫았으나, short-summary prompt의 기본 목표가 `3~5 sentences`로만 되어 있어 선택 결과가 한두 개뿐인 sparse 입력에서도 하한을 맞추려는 불필요한 padding이 유도될 수 있었음. 같은 family의 가장 작은 current-risk reduction으로 이 escape hatch를 추가.

---

## 핵심 변경

1. `core/agent_loop.py:971` — `search_results` short-summary `Target length:` 줄을 `"Target length: 3~5 sentences (200~400 Korean characters). For sparse or single-result input, 2~3 sentences are acceptable. Do not exceed 6 sentences."`로 변경
2. `tests/test_smoke.py` — `test_search_short_summary_sparse_input_escape_hatch` 추가: `search_results` short-summary prompt가 `"For sparse or single-result input, 2~3 sentences are acceptable"` 문구를 포함하는지 확인

---

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` — 통과
- `python3 -m unittest -v tests.test_smoke` — **99 tests OK** (1.148s)

---

## 남은 리스크

- `search_results` summary family(chunk-note, short-summary, merged-chunk-outline) 전체에 `Target length:` 가이드가 적용되고, short-summary에는 sparse-input escape hatch까지 추가되어 이 family의 current-risk는 닫힌 상태
- prompt-level 길이 가이드는 soft constraint이므로 실제 출력 길이의 hard guarantee는 아님
- 다음 슬라이스는 같은 family가 아닌 새 quality axis 또는 다른 current-risk reduction으로 넘어가야 함
