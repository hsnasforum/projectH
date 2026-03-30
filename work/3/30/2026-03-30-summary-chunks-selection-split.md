# 2026-03-30 summary_chunks selection split

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/NEXT_STEPS.md`
- `work/3/30/2026-03-30-summary-chunks-selection-split.md`

## 사용 skill
- `doc-sync`
  - `summary_chunks` selection heuristic 변경을 현재 shipped truth에 맞춰 문서에 좁게 반영하기 위해 사용했습니다.
- `release-check`
  - selection heuristic 변경 뒤 기존 prompt split 회귀, 웹 스모크, 문서 동기화가 실제로 맞는지 끝에서 정직하게 확인하기 위해 사용했습니다.
- `work-log-closeout`
  - 이번 라운드의 실제 변경, 실제 검증, 남은 리스크를 `/work`에 남기기 위해 사용했습니다.

## 변경 이유
- 오늘 최신 verification note인 `work/3/30/2026-03-30-short-summary-split-state-verification.md`와 실제 최신 implementation note인 `work/3/30/2026-03-30-source-type-short-summary-prompt-split.md`를 둘 다 읽고 이어받았습니다.
- 그 기준에서 short-summary, per-chunk chunk-note, final reduce prompt는 이미 truthful source boundary로 split되었지만, `summary_chunks`를 고르는 내부 selection heuristic은 여전히 shared keyword set과 shared line-priority logic을 쓰고 있었습니다.
- 이번 라운드의 가장 작은 truthful slice는 새 classifier를 만들지 않고 current call site가 이미 알고 있는 `local_document | search_results` boundary만 `summary_chunks` selection 단계까지 연결하는 것이었습니다.

## 핵심 변경
- `core/agent_loop.py`
  - `_select_summary_chunk_entries(...)`에 `summary_source_type`를 추가했습니다.
  - local-document selection은 기존 generic/document 흐름을 유지하면서 narrative/state-change 계열 키워드(`갈등`, `관계`, `변화`, `마지막`, `끝`, `신호`)를 더 우선하도록 좁게 보강했습니다.
  - search-results selection은 search-synthesis 계열 키워드(`공통`, `종합`, `차이`, `다르`, `우선`, `조정`, `강조`)를 더 우선하고 narrative-like 계열 키워드는 약하게 감점하도록 좁게 분기했습니다.
  - `_build_chunk_summary_reduce_prompt(...)`의 fallback selection, `_merge_chunk_summaries(...)`, `_build_summary_chunk_refs(...)`가 모두 same truthful boundary를 재사용하도록 맞췄습니다.
  - `_summarize_text_with_chunking(...)`에서 이미 존재하던 `reduce_source_type`를 final summary fallback과 `summary_chunks` 생성 단계까지 그대로 전달했습니다.
- `tests/test_smoke.py`
  - 같은 `chunk_summaries` 입력을 두고 `local_document`와 `search_results`가 서로 다른 `selected_line`을 고르는 focused regression을 추가했습니다.
  - `summary_chunks` payload key shape는 그대로 유지된다는 점도 함께 고정했습니다.
  - 기존 middle chunk signal preservation, short-summary split, per-chunk split, final reduce split 회귀는 그대로 유지됩니다.
- 문서
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/NEXT_STEPS.md`에 prompt split뿐 아니라 internal `summary_chunks` selection heuristic도 same truthful source boundary를 재사용한다는 현재 구현 truth를 반영했습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py`
  - 통과
- `python3 -m unittest -v tests.test_ollama_adapter tests.test_smoke tests.test_web_app`
  - 통과 (`Ran 198 tests in 2.568s`)
- `make e2e-test`
  - 통과 (`12 passed (3.2m)`)
- `git diff --check`
  - 통과
- `rg -n "_build_short_summary_prompt|_build_individual_chunk_summary_prompt|_build_chunk_summary_reduce_prompt|_select_summary_chunk_entries|_build_summary_chunk_refs|summary_chunks|short_summary|chunk_note|merged_chunk_outline|search_results|local_document" core/agent_loop.py tests/test_smoke.py tests/test_web_app.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
  - 실행

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - prompt split은 이미 truthful boundary로 나뉘었지만 `summary_chunks` selection heuristic은 여전히 shared shape라 local-document와 search-results anchor selection이 같은 line-priority logic에 묶여 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - current repo가 이미 truthfully 아는 boundary인 `local_document` / `search_results`를 `summary_chunks` selection 단계까지 그대로 연결했습니다.
  - current truthful split boundary는 이제 prompt stages와 `summary_chunks` selection 모두 동일합니다:
    - `local_document`
    - `search_results`
- 여전히 남은 리스크:
  - explicit narrative classifier는 여전히 없고, local document 내부에서 narrative vs informational을 별도로 판정하지는 않습니다.
  - `summary_chunks`는 여전히 heuristic anchor metadata이며 payload shape, max-items semantics, UI meaning 자체를 바꾼 것은 아닙니다.
  - approval flow, session schema, memory chain, review queue, aggregate surface, evidence panel, summary UI는 이번 라운드에서도 unchanged입니다.
