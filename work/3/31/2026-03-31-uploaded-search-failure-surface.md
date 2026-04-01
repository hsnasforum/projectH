# 2026-03-31 uploaded search failure surface

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 업로드 파일 검색 경로의 silent failure surface를 지시.
- 기존 `_search_uploaded_files`에서 `except Exception: continue`로 파일 읽기 실패를 완전히 삼켜, 사용자가 불완전한 검색 결과를 인지하지 못하는 current-risk가 있었음.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_search_uploaded_files` 반환 타입에 `failed_paths: list[str]`를 4번째 요소로 추가
   - `except Exception` 분기에서 `failed_paths.append(relative_path)` 추가
   - 기존 `skipped_ocr_paths` 패턴과 동일한 방식
2. 호출부에서 `failed_uploaded_paths`를 수신하고:
   - task_logger에 `failed_uploaded_paths` 기록
   - 실패 건수가 있으면 `search_notice`에 `"일부 파일(N건)을 읽지 못해 검색에서 제외되었습니다."` 추가
   - 기존 `_append_notice` / `search_notice` 패턴을 재활용하여 새 UI 패널 없이 기존 참고 문구로 표시

### 테스트 변경 (`tests/test_smoke.py`)
- `test_uploaded_folder_search_surfaces_failed_file_notice` 추가
  - `_FailingReaderTool`: `"corrupt"` 포함 파일명에서 `RuntimeError` 발생시키는 테스트용 서브클래스
  - 정상 파일 1개 + 실패 파일 1개로 검색 실행
  - 검증: 검색 결과에 정상 파일 포함, "1건" + "읽지 못해 검색에서 제외" 참고 문구 포함

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- OCR skip 경로(`OcrRequiredError`) 기존 동작 유지
- `UnicodeDecodeError` 전용 처리 미추가 (슬라이스 범위 외)

## 검증
- `python3 -m unittest -v tests.test_smoke`: 91 tests, OK (1.026s)
- `python3 -m unittest -v tests.test_web_app`: 106 tests, OK (1.764s)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`: 통과

## 남은 리스크
- 실패한 파일의 구체적 에러 원인(인코딩, 권한 등)은 사용자에게 노출하지 않음. 현재는 건수만 표시.
- `_search_uploaded_files`의 반환 타입이 4-tuple로 확장됨. 이 함수를 직접 호출하는 다른 곳은 현재 없으나, 향후 호출부 추가 시 4번째 요소 처리 필요.
- dirty worktree가 여전히 넓음.
