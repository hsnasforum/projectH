# 2026-04-03 search-results single-result chunk-note non-comparative wording

**범위**: long single-result search summary의 per-chunk chunk-note prompt에 non-comparative wording 분기 추가 + docs/README truth-sync

---

## 변경 파일

- `core/agent_loop.py` — `_build_individual_chunk_summary_prompt()`에 `selected_result_count` 파라미터 추가 및 single-result non-comparative wording 분기; `_summarize_text_with_chunking()`의 chunk-note 호출에 패스스루
- `tests/test_smoke.py` — `test_search_chunk_note_single_result_non_comparative` focused regression 1개 추가
- `docs/PRODUCT_SPEC.md` — line 41 general 설명에서 all three prompts split으로 갱신; line 136 chunk-note 상세 설명 추가
- `docs/ACCEPTANCE_CRITERIA.md` — line 25 all three prompts split으로 갱신
- `docs/NEXT_STEPS.md` — line 17 all three prompts split으로 갱신
- `README.md` — line 47 prompt 이름 정확화 및 multi/single-result 구분 명시

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

short-summary와 reduce는 이미 single-result non-comparative wording으로 분기되어 있었지만, long single-result search summary의 intermediate chunk-note prompt만 uniform `meaningful differences` wording을 유지해, 같은 single-result path 안에서 framing이 일관되지 않았음. same-family user-visible improvement으로 chunk-note에도 동일한 non-comparative 분기를 추가.

---

## 핵심 변경

1. `_build_individual_chunk_summary_prompt()` — `selected_result_count: int | None = None` 파라미터 추가. `search_results`이고 `selected_result_count == 1`일 때 `Prioritize the main facts, explicit actions or decisions, and the grounded takeaway visible in this excerpt. Do not invent cross-result agreement or differences.`로 교체.
2. `_summarize_text_with_chunking()` — chunk-note 호출에 `selected_result_count=selected_result_count` 패스스루 추가.
3. `tests/test_smoke.py` — single-result chunk-note에서 non-comparative wording 포함 + comparative wording 미포함 확인, multi-result에서 기존 comparative wording 유지 확인.
4. root docs 3개 + README — "chunk-note keeps uniform wording" → "all three prompts split by result count"로 갱신. PRODUCT_SPEC.md에 chunk-note 상세 설명 1줄 추가.

---

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` — 통과
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_search_chunk_note_single_result_non_comparative tests.test_smoke.SmokeTest.test_search_short_summary_single_result_non_comparative tests.test_smoke.SmokeTest.test_search_reduce_single_result_non_comparative tests.test_smoke.SmokeTest.test_long_search_summary_reduce_uses_search_result_synthesis_prompt` — 4 tests OK
- `python3 -m unittest tests.test_smoke` — **103 tests OK** (이전 102 → +1)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md` — 통과

---

## 남은 리스크

- search-result summary prompt family의 single-result non-comparative wording이 이제 short-summary, chunk-note, reduce 3개 모두에 적용됨. 코드/테스트/docs가 일관된 상태
- prompt-level wording은 soft constraint이므로 실제 LLM 출력의 hard guarantee는 아님
- same-family (search-result summary prompt wording) current-risk와 user-visible improvement은 이번 라운드로 닫힌 상태. 다음 슬라이스는 새 quality axis로 넘어갈 수 있음
