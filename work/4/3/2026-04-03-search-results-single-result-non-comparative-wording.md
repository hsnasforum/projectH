# 2026-04-03 search-results single-result final-summary non-comparative wording

**범위**: `search_results` final-summary prompt에서 selected result가 1개일 때 cross-source comparison wording을 non-comparative wording으로 교체
**근거**: `verify/4/3/2026-04-03-search-results-merged-summary-two-note-escape-hatch-verification.md` — single-result local search summary에서 `shared facts`/`meaningful differences` 비교형 문구가 cross-source hallucination pressure를 유발하던 same-family current-risk reduction

---

## 변경 파일

- `core/agent_loop.py` — `_build_short_summary_prompt()`, `_build_chunk_summary_reduce_prompt()`, `_summarize_text_with_chunking()`, `_build_multi_file_summary()` 4개 함수에 `selected_result_count` 전달 경로 추가 및 single-result non-comparative wording 분기
- `tests/test_smoke.py` — `test_search_short_summary_single_result_non_comparative`, `test_search_reduce_single_result_non_comparative` focused regression 2개 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

`_build_multi_file_summary()`는 `selected_results` 개수를 알고 있었지만, 그 정보가 `_summarize_text_with_chunking()` → `_build_short_summary_prompt()` / `_build_chunk_summary_reduce_prompt()`로 전달되지 않아, selected result가 정확히 1개인 local search summary에서도 `shared facts`, `meaningful differences`, `selected results`라는 비교형 문구가 고정 사용되고 있었음. 이로 인해 single-result 요약에서 cross-source agreement/difference hallucination pressure가 남아 있었음.

---

## 핵심 변경

1. `_build_short_summary_prompt()` — `selected_result_count: int | None = None` 파라미터 추가. `search_results`이고 `selected_result_count == 1`일 때 비교형 guidance를 `Prioritize the main facts, explicit actions or decisions, and the grounded conclusion from the selected result. Do not invent cross-result agreement or differences.`로 교체.
2. `_build_chunk_summary_reduce_prompt()` — 동일 파라미터 추가. single-result일 때 `Prioritize the main facts, explicit actions or decisions, and the grounded conclusion across the notes from the selected result. Do not invent cross-result agreement or differences.`로 교체.
3. `_summarize_text_with_chunking()` — `selected_result_count` 파라미터 추가, short-summary 및 reduce prompt 호출에 패스스루.
4. `_build_multi_file_summary()` — `selected_result_count=len(selected_results)` 전달.
5. `tests/test_smoke.py` — focused regression 2개: single-result에서 non-comparative wording 포함 + comparative wording 미포함 확인, multi-result에서 기존 comparative wording 유지 확인.

---

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` — 통과
- `python3 -m unittest -v tests.test_smoke` — **102 tests OK** (1.144s, 이전 100 → +2)

---

## 남은 리스크

- `search_results` final-summary prompt의 single-result cross-source comparison pressure는 이번 라운드로 닫힌 상태
- multi-result wording, Target length 숫자, sparse/two-note escape hatch wording은 변경 없이 유지됨
- prompt-level wording은 soft constraint이므로 실제 출력의 hard guarantee는 아님
- chunk-note prompt wording은 이번 범위 밖이며 변경하지 않음
- 다음 슬라이스는 같은 family 안에 추가 current-risk가 남아있지 않다면 새 quality axis로 넘어가야 함
