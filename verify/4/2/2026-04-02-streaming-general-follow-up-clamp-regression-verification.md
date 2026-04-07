## 변경 파일
- `verify/4/2/2026-04-02-streaming-general-follow-up-clamp-regression-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/2/2026-04-02-streaming-general-follow-up-clamp-regression.md`를 기준으로 이번 라운드 주장만 다시 검수해야 했습니다.
- 같은 날짜 최신 `/verify`인 `verify/4/2/2026-04-02-general-follow-up-runtime-density-clamp-verification.md`를 먼저 읽고, 그 후속 current-risk reduction이 실제로 닫혔는지 확인해야 했습니다.

## 핵심 변경
- `/work`가 주장한 변경 범위는 현재 트리와 커밋 `480437d` 기준으로 사실이었습니다.
  - `tests/test_ollama_adapter.py`에 `test_stream_general_follow_up_clamps_via_text_replace` 1건이 실제로 추가돼 있습니다.
  - `git show --stat --summary 480437d -- tests/test_ollama_adapter.py model_adapter/ollama.py` 기준으로 이번 커밋은 `tests/test_ollama_adapter.py`만 변경했고, `/work`의 파일 범위 주장과 일치했습니다.
- 새 regression의 내용도 `/work` 설명과 일치했습니다.
  - `model_adapter/ollama.py`의 `stream_answer_with_context()`는 누적 raw 스트림을 `raw_answer`로 모은 뒤 `_postprocess_answer()`를 호출하고, 결과가 다르면 최종 `text_replace` event를 내보냅니다.
  - 같은 파일의 `_postprocess_general()`은 metadata성 문장을 제거하고 최대 4문장으로 clamp합니다.
  - 새 테스트는 `_iter_generate_raw` mock으로 metadata 첫 문장 + 5문장 일반 답변을 두 chunk로 흘려보낸 뒤, 최종 누적 텍스트에서 `작성일` 제거와 2~4문장 유지, `text_replace` 발생을 모두 확인합니다.
- 이번 라운드는 test-only regression 1건이라 현재 projectH의 document-first MVP 범위를 벗어나지 않았습니다.
  - approval flow, session schema, storage, UI, web investigation, reviewed-memory surface는 건드리지 않았습니다.
  - 문서 sync가 필요한 UI / payload / schema 변경도 없었습니다.
- same-family current-risk는 이번 라운드 기준으로 truthfully 닫혔습니다.
  - full/compact follow-up density 문자열 regression, non-stream general runtime clamp, streaming `text_replace` clamp regression이 모두 존재합니다.
  - 직전 `/verify`가 남겼던 streaming 경로 공백은 이번 `/work`로 해소됐습니다.

## 검증
- `git show --stat --summary 480437d -- tests/test_ollama_adapter.py model_adapter/ollama.py`
  - `tests/test_ollama_adapter.py` 1파일만 변경된 커밋임을 확인했습니다.
- `git diff --check 480437d^ 480437d -- model_adapter/ollama.py tests/test_ollama_adapter.py`
  - 통과
- `python3 -m py_compile model_adapter/ollama.py tests/test_ollama_adapter.py`
  - 통과
- `python3 -m unittest -v tests.test_ollama_adapter`
  - `Ran 29 tests in 0.558s`
  - `OK`
- 재실행하지 않은 검증
  - browser-visible UI, approval payload, session schema 변경이 아니라 adapter-level regression 추가라 `make e2e-test`는 이번 라운드에 필요하지 않아 재실행하지 않았습니다.

## 남은 리스크
- 최신 `/work`의 코드/테스트 주장과 검증 명령 결과는 모두 사실이었고, 이번 follow-up density family의 current-risk는 현재 범위에서 닫힌 상태입니다.
- 다음 자동 handoff는 같은 family를 더 파기보다, document-first 흐름에서 바로 체감되는 다음 user-visible slice로 옮기는 편이 맞습니다.
- 따라서 다음 단일 슬라이스는 `search_results` 최종 요약 프롬프트에만 길이 가이드를 추가하는 좁은 개선으로 확정합니다.
  - 대상은 `core/agent_loop.py`의 `search_results`용 `_build_short_summary_prompt()`와 `_build_chunk_summary_reduce_prompt()`만으로 제한합니다.
  - 내부 중간 단계인 `search_results` chunk-note prompt는 이번 slice에서 건드리지 않습니다.
  - regression은 `tests/test_smoke.py`의 target-length prompt contract만 focused하게 갱신하는 편이 맞습니다.
