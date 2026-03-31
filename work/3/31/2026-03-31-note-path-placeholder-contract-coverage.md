# 2026-03-31 note-path placeholder contract coverage

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 구현 + docs sync 완료된 note-path placeholder contract를 focused regression으로 고정 필요

## 핵심 변경

### unit test 추가
- `test_get_config_includes_notes_dir`: `WebAppService.get_config()` 응답에 `notes_dir`가 설정된 notes 경로와 일치하는지 확인

### E2E smoke assertion 추가
- 시나리오 1에서 `prepareSession` 직후 `note-path` input의 placeholder에 `data/notes`가 포함되는지 확인
- config load → placeholder 업데이트가 올바르게 동작하는 contract 고정

## 검증
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_get_config_includes_notes_dir` — `1 test OK`
- `make e2e-test` — `12 passed (2.6m)`
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
