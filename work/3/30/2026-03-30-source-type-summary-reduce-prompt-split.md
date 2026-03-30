# 2026-03-30 source-type-aware summary reduce prompt split

## 변경 파일
- `core/agent_loop.py`
- `model_adapter/ollama.py`
- `model_adapter/mock.py`
- `tests/test_smoke.py`
- `tests/test_ollama_adapter.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- `doc-sync`
  - source-type-aware summary reduce split을 현재 shipped 동작 문서에 맞춰 좁게 반영하기 위해 사용했습니다.
- `release-check`
  - summary reduce 변경이 기존 summary contract, 서비스 회귀, 브라우저 스모크와 함께 정직하게 맞는지 끝에서 확인하기 위해 사용했습니다.
- `work-log-closeout`
  - 이번 라운드의 실제 변경, 실제 검증, 남은 리스크를 `/work`에 남기기 위해 사용했습니다.

## 변경 이유
- 직전 closeout 기준으로 long summary reduce는 이미 chunk notes를 다시 모델에 넣어 하나의 final summary로 합쳤지만, file-summary와 search-summary는 여전히 같은 reduce prompt shape를 공유했습니다.
- narrative-friendly guidance가 summary prompt에 추가된 뒤에는, local file summary와 selected search-result summary를 current repo가 이미 알고 있는 경계로만 truthfully 분리해 줄 필요가 있었습니다.
- 이번 라운드의 가장 작은 truthful slice는 existing call site boundary만 이용해 reduce prompt를 split하고, UI / schema / approval / memory surface는 그대로 두는 것이었습니다.

## 핵심 변경
- `core/agent_loop.py`
  - `_build_chunk_summary_reduce_prompt(...)`와 `_summarize_text_with_chunking(...)`에 `reduce_source_type`를 추가했습니다.
  - local file / uploaded document summary는 `local_document` reduce prompt를 사용해 기존 narrative-friendly document-flow guidance를 유지합니다.
  - selected local search-result summary는 `search_results` reduce prompt를 사용해 shared facts, meaningful differences, key actions or decisions, grounded conclusion 쪽으로 guidance를 좁힙니다.
  - truthful split boundary는 새 classifier가 아니라 existing call site 차이입니다:
    - file / uploaded-file summary path
    - selected local search-result summary path
- `model_adapter/ollama.py`
  - summary system prompt가 `Summary source type: search_results | local_document` marker를 해석할 수 있게 보강했습니다.
  - 기존 Korean plain-text / no heading / no bullet label contract는 그대로 유지했습니다.
- `model_adapter/mock.py`
  - merged chunk outline prompt에 `search_results` marker가 들어오면 search-synthesis 성격의 mock reduce를 따르도록 맞췄습니다.
- `tests/test_smoke.py`, `tests/test_ollama_adapter.py`
  - long narrative reduce가 계속 `local_document` 경계에서 흐름 중심 summary를 유지하는지 고정했습니다.
  - long search summary reduce가 `search_results` 경계에서 search/information synthesis prompt를 쓰는지 새 회귀를 추가했습니다.
  - Ollama summary system prompt가 기존 Korean-only plain-text constraints를 유지하면서 source-type marker도 이해하는지 고정했습니다.

## 검증
- 실행:
  - `python3 -m py_compile core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py`
  - `python3 -m unittest -v tests.test_ollama_adapter tests.test_smoke`
  - `python3 -m unittest -v tests.test_ollama_adapter tests.test_smoke tests.test_web_app`
  - `make e2e-test`
  - `rg -n "merged_chunk_outline|stream_summarize|summarize\\(|summary_chunks|narrative|fiction|informational|argumentative|search result|검색 결과" core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
  - `git diff --check`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - long summary reduce는 좋아졌지만, file-summary와 search-summary reduce가 여전히 같은 prompt shape를 공유해 search summary가 narrative guidance의 영향을 같이 받을 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - current repo가 이미 truthfully 아는 boundary인 file/uploaded-document summary path와 selected local search-result summary path를 기준으로 reduce prompt를 분리했습니다.
  - search-summary와 file-summary reduce는 현재 call site boundary로 truthfully split됩니다. 별도 classifier나 user-facing mode는 없습니다.
- 여전히 남은 리스크:
  - explicit narrative classifier는 여전히 없고, file path가 narrative인지 informational인지도 별도로 분류하지 않습니다.
  - split은 reduce 단계에만 적용됩니다. per-chunk individual summary는 기존 shared summary prompt를 계속 사용합니다.
  - `summary_chunks` contract, session schema, approval flow, evidence panel, summary UI는 그대로라서 summary quality 개선은 prompt 범위 안에서만 이뤄집니다.
