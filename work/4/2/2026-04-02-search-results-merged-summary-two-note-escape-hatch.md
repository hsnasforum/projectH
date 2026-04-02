# 2026-04-02 search-results merged-summary two-note target-length escape hatch

**범위**: `search_results` merged-summary reduce prompt 1곳에 two-note 입력용 짧은 target-length escape hatch 추가
**근거**: `verify/4/2/2026-04-02-search-results-short-summary-sparse-character-range-verification.md` — `chunk_summaries == 2`인 얇은 merged 입력에서 고정 `4~7 sentences (300~600 Korean characters)`가 불필요하게 장황한 결과를 유도하던 same-family user-visible improvement

---

## 변경 파일

- `core/agent_loop.py` — `_build_chunk_summary_reduce_prompt`의 `search_results` 분기에서 `len(chunk_summaries) == 2`일 때 `For two-note input, 3~5 sentences (220~420 Korean characters) are acceptable.` escape hatch 1줄 추가
- `tests/test_smoke.py` — `test_search_reduce_two_note_target_length_escape_hatch` focused regression 1개 추가 (2-note 포함 확인 + 3-note 미포함 확인)

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 슬라이스에서 `_build_short_summary_prompt`의 sparse/single-result escape hatch는 문장 수 + 문자 수 모두 완화됐으나, `_build_chunk_summary_reduce_prompt`는 `chunk_summaries == 2`인 최소 merged 입력에도 고정 `4~7 sentences (300~600 Korean characters)`를 요구해 얇은 search-result 합산에서 padding 압력이 남아 있었음. 같은 family의 same-family user-visible improvement로 two-note escape hatch 1건 추가.

---

## 핵심 변경

1. `core/agent_loop.py:1020-1021` — `search_results` reduce prompt의 `lines.extend(...)` 직후, `len(chunk_summaries) == 2`이면 `"For two-note input, 3~5 sentences (220~420 Korean characters) are acceptable."` 1줄 append
2. `tests/test_smoke.py` — `test_search_reduce_two_note_target_length_escape_hatch`: chunk 2개 입력에서 escape hatch wording 포함 assertIn + chunk 3개 입력에서 미포함 assertNotIn

---

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` — 통과
- `python3 -m unittest -v tests.test_smoke` — **100 tests OK** (1.374s, 이전 99 → +1)

---

## 남은 리스크

- `search_results` merged-summary reduce prompt의 two-note current-risk는 이번 라운드로 닫힌 상태
- prompt-level 길이 가이드는 soft constraint이므로 실제 출력 길이의 hard guarantee는 아님
- 3개 이상 chunk에서는 기존 `4~7 sentences` 고정이 유지되며, 이것은 의도된 동작
- 다음 슬라이스는 같은 family의 또 다른 current-risk가 남아있지 않다면 새 quality axis로 넘어가야 함
