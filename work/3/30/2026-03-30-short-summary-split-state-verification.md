# 2026-03-30 short-summary split state verification

## 변경 파일
- `work/3/30/2026-03-30-short-summary-split-state-verification.md`

## 사용 skill
- `release-check`
  - 최신 구현 상태와 실제 실행 검증 결과를 과장 없이 정리하기 위해 사용했습니다.
- `work-log-closeout`
  - 이번 라운드의 확인 범위, 실행한 검증, 남은 리스크를 `/work`에 남기기 위해 사용했습니다.

## 변경 이유
- 이번 라운드 요청은 short-summary non-chunk prompt를 truthful source boundary로 split하는 구현 작업이었습니다.
- 다만 2026-03-30 기준 오늘 폴더의 최신 closeout은 사용자가 지정한 `2026-03-30-source-type-per-chunk-summary-prompt-split.md`가 아니라 `2026-03-30-source-type-short-summary-prompt-split.md`였고, 요청한 slice는 이미 그 라운드에서 구현된 상태였습니다.
- 따라서 이번 라운드는 같은 기능을 다시 열지 않고, 현재 repo가 실제로 그 상태를 유지하는지 코드/문서/테스트 기준으로 재확인하는 것이 가장 작은 truthful 작업이었습니다.

## 핵심 변경
- 추가 코드 변경은 하지 않았습니다.
- 최신 구현 기준이 이미 `work/3/30/2026-03-30-source-type-short-summary-prompt-split.md`로 넘어가 있음을 확인했습니다.
- `core/agent_loop.py`에서 short-summary non-chunk path가 `_build_short_summary_prompt(...)`를 사용하고, same truthful boundary만 재사용한다는 점을 다시 확인했습니다.
- 현재 truthful split boundary는 short-summary와 long-summary 모두 동일하게 유지됩니다:
  - `local_document`
  - `search_results`
- no new UI, no new classifier, no new schema, unchanged `summary_chunks` contract 상태도 그대로 유지됨을 확인했습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py`
  - 통과
- `python3 -m unittest -v tests.test_ollama_adapter tests.test_smoke tests.test_web_app`
  - 통과 (`Ran 197 tests in 2.761s`)
- `make e2e-test`
  - 통과 (`12 passed (3.2m)`)
- `git diff --check`
  - 통과
- `rg -n "_build_short_summary_prompt|_build_individual_chunk_summary_prompt|_build_chunk_summary_reduce_prompt|stream_summarize\\(|reduce_source_type|search_results|local_document|Summary mode: short_summary" core/agent_loop.py model_adapter/ollama.py model_adapter/mock.py tests/test_smoke.py tests/test_web_app.py tests/test_ollama_adapter.py`
  - 실행

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - short-summary non-chunk path가 shared summarize call을 쓰던 상태는 이미 `2026-03-30-source-type-short-summary-prompt-split.md` 라운드에서 해소되었습니다.
- 이번 라운드에서 확인한 해소 상태:
  - short-summary path와 long-summary path는 모두 existing truthful boundary만 사용해 split됩니다.
  - current repo에는 추가 classifier나 fake source-type inference가 없습니다.
- 여전히 남은 리스크:
  - local document 내부 narrative vs informational 분기는 explicit classifier 없이 prompt guidance 수준에 머뭅니다.
  - current truthful split boundary는 여전히 `local_document` / `search_results` 두 가지뿐입니다.
  - `summary_chunks`, approval flow, session schema, memory chain, review queue, aggregate surface는 이번 라운드에서도 unchanged입니다.
