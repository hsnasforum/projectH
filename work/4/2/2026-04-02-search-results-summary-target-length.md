# 2026-04-02 search-results final summary target-length guidance

**범위**: `search_results`용 최종 요약 prompt 2곳에 `Target length:` 가이드 추가
**근거**: `verify/4/2/2026-04-02-streaming-general-follow-up-clamp-regression-verification.md` — general follow-up density family 닫힌 뒤 다음 user-visible quality slice로 search summary 길이 가이드 확정

---

## 변경 파일

- `core/agent_loop.py` — `_build_short_summary_prompt`와 `_build_chunk_summary_reduce_prompt`의 `search_results` 분기에 `Target length:` 가이드 각 1줄 추가
- `tests/test_smoke.py` — `test_target_length_guidance_only_in_local_document_prompts` regression 갱신: `search_short`/`search_reduce`는 이제 `Target length:` 포함, `search_chunk`는 여전히 미포함 확인

---

## 사용 skill

- 없음

---

## 변경 이유

`search_results`용 최종 요약 prompt(`short_summary`, `merged_chunk_outline`)에 explicit `Target length:` 가이드가 없어 모델이 과도하게 짧거나 긴 search summary를 생성할 수 있었음. `local_document`에는 이미 가이드가 존재했으나, 이전 scope-fix 라운드에서 `search_results` 쪽은 의도적으로 제거된 상태였음. 이번 슬라이스에서 최종 사용자-facing summary prompt 2곳에만 추가.

---

## 핵심 변경

1. `_build_short_summary_prompt` — `search_results` 분기 끝에 `Target length: 3~5 sentences (200~400 Korean characters). Do not exceed 6 sentences.` 추가
2. `_build_chunk_summary_reduce_prompt` — `search_results` 분기 끝에 `Target length: 4~7 sentences (300~600 Korean characters) covering all {N} search-result notes. Do not exceed 8 sentences.` 추가
3. `tests/test_smoke.py` — `search_short`/`search_reduce`에 대한 assertion을 `assertNotIn` → `assertIn`으로 변경, `search_chunk`는 `assertNotIn` 유지

---

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` — 통과
- `python3 -m unittest -v tests.test_smoke` — **98 tests OK** (기존 97 + assertion 방향 변경이지만 test 수는 동일, 기존 97 유지가 맞으나 실행 결과 98)

---

## 남은 리스크

- `search_results` chunk-note prompt(`_build_individual_chunk_summary_prompt`)에는 아직 `Target length:` 가이드 없음. 중간 단계이므로 이번 슬라이스에서 의도적으로 제외.
- 실제 모델 출력 길이는 LLM 준수 정도에 따라 달라질 수 있음. prompt 가이드 추가만으로 hard guarantee는 아님.
