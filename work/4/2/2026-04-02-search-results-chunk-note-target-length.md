# 2026-04-02 search-results chunk-note target-length guidance

**범위**: `search_results` chunk-note prompt 1곳에 `Target length:` 가이드 추가
**근거**: `verify/4/2/2026-04-02-search-results-summary-target-length-verification.md` — 최종 short/reduce prompt에는 이미 가이드 추가 완료, 같은 family의 마지막 남은 gap인 chunk-note prompt를 닫음

---

## 변경 파일

- `core/agent_loop.py` — `_build_individual_chunk_summary_prompt`의 `search_results` 분기에 `Target length:` 가이드 1줄 추가
- `tests/test_smoke.py` — `test_target_length_guidance_only_in_local_document_prompts` → `test_target_length_guidance_in_all_summary_prompts`로 rename, `search_chunk`도 `assertIn`으로 변경

---

## 사용 skill

- 없음

---

## 변경 이유

이전 슬라이스에서 `search_results`용 최종 요약 prompt 2곳(`short_summary`, `merged_chunk_outline`)에 `Target length:` 가이드를 추가했으나, 중간 단계인 chunk-note prompt는 의도적으로 제외했음. 이번 슬라이스에서 같은 family의 마지막 남은 gap을 닫아 search-result 요약 파이프라인 전체에 일관된 길이 가이드를 적용.

---

## 핵심 변경

1. `_build_individual_chunk_summary_prompt` — `search_results` 분기 끝에 `Target length: 1~2 sentences (50~150 Korean characters). Do not exceed 3 sentences.` 추가 (local_document와 동일한 길이 기준)
2. `tests/test_smoke.py` — 테스트 이름을 `test_target_length_guidance_in_all_summary_prompts`로 rename하여 현재 계약을 정확히 반영. `search_chunk`/`search_short`/`search_reduce` 모두 `assertIn("Target length:", ...)` 확인으로 통일

---

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` — 통과
- `python3 -m unittest -v tests.test_smoke` — **98 tests OK**

---

## 남은 리스크

- `search_results` 요약 파이프라인(chunk-note, short_summary, merged_chunk_outline) 전체에 `Target length:` 가이드가 적용되어 이 family의 current-risk는 닫힌 상태.
- prompt-level 길이 가이드는 soft constraint라 실제 출력 길이의 hard guarantee는 아님.
- 다음 슬라이스는 같은 family가 아닌 새 quality axis 또는 다른 current-risk reduction으로 넘어가야 함.
