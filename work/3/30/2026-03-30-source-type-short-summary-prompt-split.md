# 2026-03-30 source-type-aware short-summary prompt split

## 변경 파일
- `core/agent_loop.py`
- `model_adapter/mock.py`
- `tests/test_smoke.py`
- `tests/test_ollama_adapter.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- `doc-sync`
  - short-summary non-chunk prompt 변경을 현재 shipped truth에 맞춰 문서에 좁게 반영하기 위해 사용했습니다.
- `release-check`
  - short-summary split 구현 뒤 기존 long-summary 회귀, 웹 스모크, 문서 동기화가 실제로 맞는지 끝에서 정직하게 확인하기 위해 사용했습니다.
- `work-log-closeout`
  - 이번 라운드의 실제 변경, 실제 검증, 남은 리스크를 `/work`에 남기기 위해 사용했습니다.

## 변경 이유
- 직전 closeout 기준으로 long-summary path는 per-chunk와 final reduce가 모두 truthful source boundary로 split되었지만, chunking이 일어나지 않는 short-summary path는 여전히 shared summarize call을 그대로 사용하고 있었습니다.
- 그 상태에서는 selected local search-result short summary도 shared summary guidance를 같이 받아 search-synthesis 관점이 약해질 수 있었습니다.
- 이번 라운드의 가장 작은 truthful slice는 새 classifier를 만들지 않고 current call site가 이미 알고 있는 boundary만 재사용해서 short-summary non-chunk prompt를 split하는 것이었습니다.

## 핵심 변경
- `core/agent_loop.py`
  - `_build_short_summary_prompt(...)`를 추가했습니다.
  - `_summarize_text_with_chunking(...)`의 non-chunk 두 경로:
    - `len(text) <= chunk_threshold`
    - `len(chunks) <= 1`
    에서 shared summarize call 대신 source-type-aware short-summary prompt를 사용하도록 바꿨습니다.
  - local file / uploaded-document short summary는 `Summary source type: local_document`로 들어가며 document-flow / narrative-friendly guidance를 유지합니다.
  - selected local search-result short summary는 `Summary source type: search_results`로 들어가며 shared facts, differences, actions or decisions, grounded conclusion 중심 guidance를 받습니다.
  - same `reduce_source_type` boundary를 short path에도 재사용했기 때문에 no new UI, no new mode toggle, no new classifier, no schema change를 유지했습니다.
  - long per-chunk split, final reduce split, `summary_chunks` contract는 그대로 유지했습니다.
- `model_adapter/mock.py`
  - `Summary mode: short_summary` 프롬프트를 local-document / search-results로 좁게 해석하도록 추가해 mock short-summary path가 프롬프트 서두를 그대로 요약하지 않게 맞췄습니다.
- `tests/test_smoke.py`
  - short local-document summary path에서 `short_summary` prompt가 `local_document` marker와 document-friendly guidance를 유지하는지 고정했습니다.
  - short search-result summary path에서 `short_summary` prompt가 `search_results` marker와 search-synthesis guidance를 쓰고, narrative wording을 다시 끌어오지 않는지 고정했습니다.
  - 기존 long per-chunk split, long reduce split, middle chunk signal preservation 회귀는 계속 유지됩니다.
- `tests/test_ollama_adapter.py`
  - Ollama summary system prompt가 기존 Korean-only plain-text constraints와 함께 `search_results`, `local_document` marker 모두를 여전히 이해하는지 고정했습니다.
- 문서
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/NEXT_STEPS.md`에 short-summary와 long-summary가 모두 same truthful source boundary를 쓴다는 현재 구현 truth를 반영했습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py`
  - 통과
- `python3 -m unittest -v tests.test_ollama_adapter tests.test_smoke tests.test_web_app`
  - 통과 (`Ran 197 tests in 2.523s`)
- `make e2e-test`
  - 통과 (`12 passed (3.2m)`)
- `git diff --check`
  - 통과
- `rg -n "chunk_note|merged_chunk_outline|Summary source type|search_results|local_document|summary_chunks|narrative|fiction" core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
  - 실행

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - long-summary path는 split되었지만 short-summary non-chunk path는 shared summarize call이라 search-summary short path도 shared guidance를 같이 받을 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - current repo가 이미 truthfully 아는 boundary인 local file / uploaded-document summary path와 selected local search-result summary path를 short-summary non-chunk에도 그대로 연결했습니다.
  - 현재 truthful split boundary는 short-summary와 long-summary 모두 동일합니다:
    - `local_document`
    - `search_results`
- 여전히 남은 리스크:
  - explicit narrative classifier는 여전히 없고, local document 내부에서 narrative vs informational을 따로 분기하지는 않습니다.
  - split은 current call-site boundary까지만 열려 있으며, fake source-type inference는 여전히 없습니다.
  - `summary_chunks`, approval flow, session schema, memory chain, review queue, aggregate surface, evidence panel, summary UI는 unchanged라 품질 개선 범위는 prompt split 안에만 머뭅니다.
