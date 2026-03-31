# 2026-03-31 narrative faithfulness prompt-family focused regression

## 변경 파일
- `tests/test_smoke.py`

## 사용 skill
- 없음

## 변경 이유
- local-document summary prompt에 추가한 strict source-anchored faithfulness 규칙이 regression으로 고정되지 않았음
- search-results branch에 규칙이 잘못 들어가지 않았는지도 확인 필요

## 핵심 변경

### 기존 테스트 보강
- `test_short_local_document_summary_uses_local_document_prompt`: local document short summary prompt에 `STRICT:` 와 `Do not add events that did not happen` 포함 assertion 추가

### 신규 focused test
- `test_local_document_prompt_strict_rule_absent_in_search_results`:
  - 3개 prompt builder(`_build_individual_chunk_summary_prompt`, `_build_short_summary_prompt`, `_build_chunk_summary_reduce_prompt`)를 local_document와 search_results 양쪽으로 호출
  - local_document: `STRICT:` + `Do not add events that did not happen` 포함 확인
  - search_results: `STRICT:` 미포함 확인
  - 6개 prompt(local 3 + search 3)을 직접 비교하여 source-type split 정합성 검증

### 변경하지 않은 것
- `core/agent_loop.py`: 코드 변경 없음
- browser UI / e2e: 변경 없음
- docs: test contract 설명이 바뀌지 않았으므로 docs 변경 불필요

## 검증
- `python3 -m unittest tests.test_smoke.SmokeTest.test_local_document_prompt_strict_rule_absent_in_search_results` — `1 test OK`
- `python3 -m unittest tests.test_smoke.SmokeTest.test_short_local_document_summary_uses_local_document_prompt` — `1 test OK`
- `python3 -m unittest -v tests.test_smoke` — `87 tests OK`
- `git diff --check` (변경 파일) — 통과

## 남은 리스크
- prompt 규칙의 실제 효과는 real model(Ollama 등)에서만 확인 가능. mock adapter는 prompt를 해석하지 않음.
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
