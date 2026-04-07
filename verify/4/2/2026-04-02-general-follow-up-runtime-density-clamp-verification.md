## 변경 파일
- `verify/4/2/2026-04-02-general-follow-up-runtime-density-clamp-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/2/2026-04-02-general-follow-up-runtime-density-clamp.md`를 기준으로 이번 라운드 주장만 검수해야 했습니다.
- 오늘 같은 날짜의 `/verify` 메모는 아직 없어 `/work` 단독 기준으로 current truth를 다시 대조했습니다.

## 핵심 변경
- `/work`가 주장한 round-local 코드 변경은 현재 source tree와 커밋 `60d9b64` 기준으로 사실이었습니다.
  - `model_adapter/ollama.py`에서 `_postprocess_answer()`의 `general` fallback이 더 이상 `raw_answer.strip()`으로 끝나지 않고 `_postprocess_general()`을 호출합니다.
  - 새 `_postprocess_general()`은 `_split_sentences()`로 문장을 나눈 뒤 `_looks_like_metadata()`로 메타데이터성 문장을 걸러내고, 남은 문장을 최대 4개까지 clamp한 뒤 다시 한 문단으로 합칩니다.
  - `tests/test_ollama_adapter.py`에는 `/work`가 적은 두 regression, `test_general_postprocess_filters_metadata_and_clamps_sentences`와 `test_general_postprocess_preserves_short_answer`가 실제로 추가돼 있습니다.
- 이번 변경은 local document follow-up Q&A의 runtime 후처리 1건에만 머물러 현재 document-first MVP 범위를 벗어나지 않았습니다. approval flow, session schema, storage, web investigation, UI surface는 건드리지 않았습니다.
- 문서 sync 누락도 현재 기준으로는 보이지 않았습니다.
  - 저장소 문서는 general follow-up의 exact sentence clamp를 별도 shipped contract로 선언하지 않고 있어, 이번 라운드가 문서 truth를 새로 깨지는 않았습니다.
  - 따라서 README나 제품 문서를 같은 라운드에서 반드시 갱신해야 하는 종류의 UI / payload / schema 변경은 아니었습니다.
- 다만 `/work`의 note-level 근거 표기는 현재 truth와 어긋납니다.
  - 메모 상단의 근거로 적힌 `verify/4/2/2026-04-02-compact-density-output-contract-regression-verification.md`는 현재 트리와 git history 어디에도 없습니다.
  - 즉, 코드/테스트 변경 자체는 맞지만 이번 `/work`의 근거 경로 1건은 실제 존재하는 verification note를 가리키지 않습니다.

## 검증
- `python3 -m py_compile model_adapter/ollama.py tests/test_ollama_adapter.py`
  - 통과
- `python3 -m unittest -v tests.test_ollama_adapter`
  - `Ran 28 tests in 0.555s`
  - `OK`
- `git diff --check 60d9b64^ 60d9b64 -- model_adapter/ollama.py tests/test_ollama_adapter.py`
  - 통과
- 코드 대조
  - `git show --stat --summary 60d9b64 -- model_adapter/ollama.py tests/test_ollama_adapter.py`로 이번 라운드 커밋이 claimed 2개 파일만 바꿨는지 확인했습니다.
  - 현재 `model_adapter/ollama.py`의 `stream_answer_with_context()`도 같은 `_postprocess_answer()`를 재사용한다는 점까지 확인했습니다.
- 재실행하지 않은 검증
  - browser-visible UI 계약, schema, approval flow 변경이 아니라 adapter-level runtime 후처리라 `make e2e-test`는 이번 라운드에 필요하지 않아 재실행하지 않았습니다.

## 남은 리스크
- 이번 `/work`의 핵심 코드 주장과 테스트 주장은 사실이었지만, 근거로 적은 same-day `/verify` 경로는 존재하지 않아 note-level truth mismatch가 1건 남아 있습니다.
- current runtime fix는 non-stream `answer_with_context()` 경로에서 직접 regression으로 잠겼지만, shipped streaming follow-up 경로의 최종 `text_replace` clamp 동작은 아직 전용 regression이 없습니다.
- 따라서 다음 자동 handoff는 같은 family의 smallest current-risk reduction으로, `stream_answer_with_context(intent="general")`가 metadata 필터와 최대 4문장 clamp를 final `text_replace` event까지 유지하는지 잠그는 focused regression 1건으로 좁히는 편이 맞습니다.
