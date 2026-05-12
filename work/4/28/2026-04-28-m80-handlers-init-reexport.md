# 2026-04-28 M80 handlers init re-export

## 변경 파일

- `app/handlers/__init__.py`
- `work/4/28/2026-04-28-m80-handlers-init-reexport.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록에 필요한 변경 파일, 실제 검증, 남은 리스크를 정리하기 위해 사용했습니다.

## 변경 이유

- M80 handoff가 비어 있던 `app/handlers/__init__.py`에 handler mixin package re-export를 추가하도록 지정했습니다.
- 이번 변경은 동작 변경이 없는 단일 파일 structural 정리입니다.

## 핵심 변경

- `app/handlers/__init__.py`에 handler mixin package docstring을 추가했습니다.
- `CandidateHandlerMixin`, `ChatHandlerMixin`, `CorrectionHandlerMixin`, `FeedbackHandlerMixin`, `PreferenceHandlerMixin`, `ReviewedMemoryHandlerMixin` 6개를 re-export했습니다.
- 동일 6개 이름을 `__all__`에 명시했습니다.
- handoff 경계에 따라 `app/web.py`와 다른 파일은 수정하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`: `d62261bb3c93eaaaef83e74e94c65c30261bd6f9551f44f7b12f857a7750ea1d` 일치 확인.
- `git switch -c feat/m80-axis1-handlers-init`: 실패. `.git/refs/heads/...` lock 생성이 read-only file system으로 거부되었습니다.
- `python3 -m py_compile app/handlers/__init__.py`: 통과.
- `python3 -m unittest tests.test_smoke 2>&1 | tail -3`: 통과. `Ran 150 tests in 2.049s`, `OK`.
- `git diff --check -- app/handlers/__init__.py`: 통과.

## 남은 리스크

- 브랜치 생성이 sandbox의 `.git/refs` read-only 제한으로 실패해 변경은 `feat/m79-doc-sync-m77-m78` dirty worktree에 남아 있습니다.
- dist 재빌드, E2E, broad unittest는 handoff 범위를 넘기지 않기 위해 실행하지 않았습니다.
- commit, push, PR 생성은 implement 역할 경계에 따라 수행하지 않았습니다.
