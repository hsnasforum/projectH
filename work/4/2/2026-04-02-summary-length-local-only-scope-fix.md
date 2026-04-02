# 2026-04-02 summary Target length — local_document only scope fix

**범위**: `Target length:` 가이드를 `local_document` 프롬프트에만 적용, `search_results` 프롬프트에서 제거
**근거**: `verify/4/2/2026-04-02-document-summary-length-control-verification.md` — `/work`의 "search_results 분기에는 미적용" 주장이 현재 코드와 불일치

---

## 변경 파일

- `core/agent_loop.py` — 3곳에서 `Target length:` 줄을 공통 `lines.extend` → `else` (local_document) 분기 안으로 이동
- `tests/test_smoke.py` — `test_target_length_guidance_only_in_local_document_prompts` regression 추가

---

## 사용 skill

- 없음

---

## 변경 이유

이전 라운드에서 `Target length:` 지시를 `if/else` 분기 바깥 공통 블록에 넣어서 `search_results` 프롬프트에도 적용되었음. `/work`는 "local document summary only, search_results 미적용"이라고 적었으나 실제 코드는 양쪽 모두 적용 상태였음. verify가 이 scope mismatch를 지적.

---

## 핵심 변경

3개 프롬프트(`chunk_note`, `short_summary`, `merged_chunk_outline`)에서 `Target length:` 줄을 `else` (local_document) 분기의 마지막 항목으로 이동. `search_results` 분기에는 기존 "concise" 지시만 유지.

---

## 검증

- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` — 통과
- `python3 -m unittest -v tests.test_smoke` — **97 tests OK** (기존 96 + 새 regression 1)

---

## 남은 리스크

- 없음. scope mismatch 해소 완료.
