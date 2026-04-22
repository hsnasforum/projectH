# 2026-04-22 content reason label chips

## 변경 파일
- `core/contracts.py`
- `app/frontend/src/components/MessageBubble.tsx`

## 사용 skill
- `finalize-lite`: 구현 종료 전 필수 검증, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크 기준으로 한국어 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 795가 Milestone 6 Axis 3 첫 슬라이스로 content reject reason label 상수 확장과 label chip UI 추가를 지정했습니다.
- Axis 4로 defer된 backend API endpoint, handler, session_store 메서드, 상위 frontend wire-up은 이번 라운드 범위에서 제외했습니다.

## 핵심 변경
- `ContentReasonLabel`에 `fact_error`, `tone_error`, `missing_info`를 추가하고 기존 `explicit_content_rejection` 문자열 값은 유지했습니다.
- `ALLOWED_CONTENT_REASON_LABELS`의 `CONTENT_REJECT` 허용 목록에 새 label 값을 포함했습니다.
- `MessageBubble`에 optional `onContentReasonLabel` prop을 추가했습니다.
- persistent rejected 블록의 "거절됨" 배지 아래에 label chip 행을 추가했습니다.
- parent wire-up 전에는 `onContentReasonLabel`이 없으므로 chip UI가 렌더되지 않게 유지했습니다.

## 검증
- `python3 -m py_compile core/contracts.py` → 통과
- `python3 -m unittest tests.test_smoke` → 통과, 150 tests OK
- `git diff --check -- core/contracts.py app/frontend/src/components/MessageBubble.tsx` → 통과

## 남은 리스크
- label 저장 API, handler, session_store 메서드, `ChatArea.tsx`/`App.tsx` 상위 wire-up은 handoff 지시에 따라 미구현 상태입니다.
- frontend typecheck/build는 이번 handoff 필수 검증에 포함되지 않아 실행하지 않았습니다.
