# 2026-03-30 source-type-aware per-chunk summary prompt split

## 변경 파일
- `core/agent_loop.py`
- `model_adapter/mock.py`
- `tests/test_smoke.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- `doc-sync`
  - per-chunk summary prompt 변경을 현재 shipped truth에 맞춰 문서에 좁게 반영하기 위해 사용했습니다.
- `release-check`
  - per-chunk split 구현 뒤 기존 reduce 회귀, 웹 스모크, 문서 동기화가 실제로 맞는지 끝에서 정직하게 확인하기 위해 사용했습니다.
- `work-log-closeout`
  - 이번 라운드의 실제 변경, 실제 검증, 남은 리스크를 `/work`에 남기기 위해 사용했습니다.

## 변경 이유
- 직전 closeout 기준으로 long-summary final reduce는 이미 truthful source boundary로 split되었지만, per-chunk individual summary는 여전히 shared prompt shape를 사용하고 있었습니다.
- 그 상태에서는 selected local search-result chunk summary도 narrative-friendly shared guidance의 영향을 함께 받을 수 있었습니다.
- 이번 라운드의 가장 작은 truthful slice는 새 classifier를 만들지 않고 current call site가 이미 알고 있는 boundary만 재사용해서 per-chunk prompt를 split하는 것이었습니다.

## 핵심 변경
- `core/agent_loop.py`
  - `_normalize_summary_source_type(...)`와 `_build_individual_chunk_summary_prompt(...)`를 추가했습니다.
  - long local file / uploaded-document chunk summary는 `Summary source type: local_document`로 들어가며 문서 흐름과 narrative-friendly guidance를 유지합니다.
  - selected local search-result chunk summary는 `Summary source type: search_results`로 들어가며 source-backed evidence chunk, shared facts, differences, actions or decisions 쪽 guidance를 받습니다.
  - same `reduce_source_type` boundary를 per-chunk에도 재사용했기 때문에 no new UI, no new mode toggle, no new classifier, no schema change를 유지했습니다.
  - final reduce split과 `summary_chunks` contract는 그대로 유지했습니다.
- `model_adapter/mock.py`
  - `Summary mode: chunk_note` 프롬프트를 좁게 해석하도록 추가해 long-summary mock path가 프롬프트 서두를 그대로 요약하지 않게 맞췄습니다.
- `tests/test_smoke.py`
  - long narrative summary path에서 per-chunk prompt가 `local_document` marker와 document-flow / narrative guidance를 유지하는지 고정했습니다.
  - long search summary path에서 per-chunk prompt가 `search_results` marker와 search-synthesis guidance를 쓰고, narrative wording을 다시 끌어오지 않는지 고정했습니다.
  - 기존 final reduce 회귀, middle chunk signal preservation, long narrative reduce, long search reduce는 계속 유지됩니다.
- 문서
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/NEXT_STEPS.md`에 per-chunk와 final reduce가 모두 same truthful source boundary를 쓴다는 현재 구현 truth를 반영했습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py`
  - 통과
- `python3 -m unittest -v tests.test_ollama_adapter tests.test_smoke tests.test_web_app`
  - 통과 (`Ran 195 tests in 2.265s`)
- `make e2e-test`
  - 통과 (`12 passed (3.1m)`)
- `git diff --check`
  - 통과
- `rg -n "merged_chunk_outline|reduce_source_type|Summary source type|summary_chunks|narrative|fiction|search_results|local_document" core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
  - 실행

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - final reduce는 split되었지만 per-chunk individual summary는 shared prompt라 search-summary chunk 단계가 narrative-friendly shared guidance를 같이 받을 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - current repo가 이미 truthfully 아는 boundary인 local file / uploaded-document summary path와 selected local search-result summary path를 per-chunk에도 그대로 연결했습니다.
  - 현재 truthful split boundary는 per-chunk와 final reduce 모두 동일합니다:
    - `local_document`
    - `search_results`
- 여전히 남은 리스크:
  - explicit narrative classifier는 여전히 없고, local document 내부에서 narrative vs informational을 따로 분기하지는 않습니다.
  - chunking이 일어나지 않는 짧은 summary path는 이번 라운드 범위 밖이라 기존 shared summarize call을 그대로 사용합니다.
  - `summary_chunks`, approval flow, session schema, memory chain, review queue, evidence panel, summary UI는 unchanged라 품질 개선 범위는 prompt split 안에만 머뭅니다.
