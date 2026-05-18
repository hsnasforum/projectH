# 2026-04-28 M49 Axis 3 요약 파이프라인 주입 중재 권고

## 상황 요약
- **현재 상태**: M49 Axis 2(신뢰도 필터) 구현 및 검증이 완료되어 PR #47로 번들링 및 발행되었습니다. 현재 `operator_request.md` CONTROL_SEQ 1156이 PR 머지 승인을 대기 중이나, 후속 자동화 레인이 다음 단계를 찾지 못하고 idle 상태로 종료되었습니다.
- **병목**: PR #47은 머지 경계(merge boundary)에 해당하여 운영자 개입을 기다리고 있으나, `GEMINI.md` 원칙에 따라 정체(stall)를 피하기 위해 병렬로 진행 가능한 다음 슬라이스를 확정해야 합니다.

## 분석
1. **M49 계약 정합성**: M49 Axis 1에서 정의한 계약에는 `document summary` 호출 시에도 선호도를 주입하도록 명시되어 있습니다.
2. **구현 갭(Gap)**: 현재 `core/agent_loop.py`는 일반 채팅(`_handle_general_response`)과 문서 Q&A(`stream_answer_with_context`)에는 선호도를 주입하고 있으나, 문서 요약 파이프라인(`_summarize_text_with_chunking`)에서는 이를 누락하고 있습니다.
3. **인터페이스 확장 필요**: `ModelAdapter` 및 `OllamaModelAdapter`의 `summarize`, `stream_summarize` 메서드 시그니처가 아직 `active_preferences`를 받도록 설계되지 않았습니다.
4. **결론**: PR #47의 머지 여부와 상관없이, 선호도 주입의 범위를 요약 파이프라인까지 확장하는 작업은 M49의 완성을 위해 필수적이며 독립적인 다음 구현 슬라이스입니다.

## 권고 사항
- **결정**: `RECOMMEND: implement M49 Axis 3 — preference injection for summarization pipeline`
- **사유**: M49의 서비스 범위를 계약대로 확장하여 "교차 세션 선호도 반영" 루프를 완성해야 합니다.
- **슬라이스 상세**:
    - `model_adapter/base.py`, `model_adapter/ollama.py`: `summarize`, `stream_summarize` 시그니처 및 프롬프트 주입 로직 추가.
    - `core/agent_loop.py`: `_summarize_text_with_chunking` 내부의 모델 호출 시 `active_preferences` 전달.
    - `tests/test_agent_loop.py`: 요약 시 선호도 주입 여부를 확인하는 단위 테스트 추가.
- **참고**: PR #47 머지는 운영자 가용 시점에 별도로 진행하되, 로컬 작업은 M49 Axis 3으로 즉시 전환할 것을 권장합니다.
