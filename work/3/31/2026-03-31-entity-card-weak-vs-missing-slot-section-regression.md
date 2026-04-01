# 2026-03-31 entity-card weak-slot vs missing-slot section regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, entity-card 응답 본문에서 `불확실 정보:`(단일 출처 weak slot)와 `추가 확인 필요:`(근거 없는 missing slot)가 분리되어 유지되는지 regression을 지시.
- 현재 production copy는 두 섹션을 명확히 분리하고 있으나, 이를 직접 고정하는 web-app 계약 regression이 없었음.
- 이 섹션이 합쳐지면 사용자가 단일 출처 사실과 아직 근거가 없는 슬롯을 같은 종류의 불확실성으로 오해할 수 있음.

## 핵심 변경
- `test_handle_chat_entity_card_separates_weak_and_missing_slot_sections` 추가 (`tests/test_web_app.py`)
  - fixture: namu.wiki 단일 소스 entity-card (weak slot과 missing slot 모두 생성)
  - 검증:
    - `"불확실 정보:"` 섹션 존재
    - `"추가 확인 필요:"` 섹션 존재
    - 불확실 정보 섹션에 `"단일 출처"` 문구 포함
    - 추가 확인 필요 섹션에 `"교차 확인 가능한 근거가 더 필요합니다"` 문구 포함
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 120 tests, OK (2.098s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음

## 남은 리스크
- dirty worktree가 여전히 넓음.
