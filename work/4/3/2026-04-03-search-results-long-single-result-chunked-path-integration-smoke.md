# 2026-04-03 search-results long single-result chunked-path integration smoke

**범위**: `_build_multi_file_summary()` 경유 actual long single-result search summary path를 직접 잠그는 integration smoke 1건 추가

---

## 변경 파일

- `tests/test_smoke.py` — `test_long_search_summary_single_result_uses_non_comparative_chunk_note_prompt` integration smoke 1개 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

이전 라운드에서 `_build_individual_chunk_summary_prompt()` builder 단위의 single-result non-comparative wording regression은 추가했지만, `_build_multi_file_summary()` → `_summarize_text_with_chunking()` → chunk-note로 이어지는 actual long single-result flow는 직접 잠기지 않았음. 기존 long search integration smoke(`test_long_search_summary_reduce_uses_search_result_synthesis_prompt`)는 multi-result path만 검증. same-family current-risk reduction으로 single-result chunked path integration smoke 추가.

---

## 핵심 변경

1. `test_long_search_summary_single_result_uses_non_comparative_chunk_note_prompt` — selected result 1개 + 220줄 반복 입력으로 chunking을 유발하고:
   - `summary_chunks`가 실제 생성되는지 확인
   - 모든 `chunk_note` prompt에 non-comparative wording(`Do not invent cross-result agreement or differences`) 포함 확인
   - 모든 `chunk_note` prompt에 comparative wording(`meaningful differences`) 미포함 확인
   - reduce prompt에도 single-result non-comparative wording 포함 확인

---

## 검증

- `python3 -m py_compile tests/test_smoke.py` — 통과
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_long_search_summary_single_result_uses_non_comparative_chunk_note_prompt tests.test_smoke.SmokeTest.test_search_chunk_note_single_result_non_comparative tests.test_smoke.SmokeTest.test_search_short_summary_single_result_non_comparative tests.test_smoke.SmokeTest.test_search_reduce_single_result_non_comparative tests.test_smoke.SmokeTest.test_long_search_summary_reduce_uses_search_result_synthesis_prompt` — 5 tests OK
- `python3 -m unittest tests.test_smoke` — **104 tests OK** (이전 103 → +1)
- `git diff --check -- tests/test_smoke.py` — 통과

---

## 남은 리스크

- search-result summary prompt family의 single-result non-comparative wording이 builder level + integration level 모두에서 잠긴 상태
- 코드/문서 wording 변경 없는 coverage-only 라운드이므로 docs sync 불필요
- same-family current-risk reduction은 이번 라운드로 닫힌 상태. 다음 슬라이스는 새 quality axis로 넘어갈 수 있음
