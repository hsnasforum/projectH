# 2026-04-28 M78 candidate handler

## 변경 파일

- `app/handlers/candidates.py`
- `app/handlers/aggregate.py` 삭제
- `app/web.py`
- `work/4/28/2026-04-28-m78-candidate-handler.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록에 필요한 변경 파일, 실제 검증, 남은 리스크를 정리하기 위해 사용했습니다.

## 변경 이유

- M78 handoff가 `AggregateHandlerMixin`에 남은 candidate confirmation/review 메서드 2개를 별도 handler mixin으로 분리하고 `aggregate.py`를 완전히 제거하도록 지정했습니다.
- 이번 변경은 동작 변경이 없는 순수 extract-and-move 구조 정리입니다.

## 핵심 변경

- `app/handlers/candidates.py`를 새로 만들고 `CandidateHandlerMixin`에 `submit_candidate_confirmation`, `submit_candidate_review`를 이동했습니다.
- `app/handlers/aggregate.py`를 삭제했습니다.
- `app/web.py`에서 `AggregateHandlerMixin` import와 상속을 `CandidateHandlerMixin`으로 대체했습니다.
- 기존 테스트 파일과 dist 산출물은 handoff 지시에 따라 수정하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`: `85bbb72f81b87e95ccea87b587874998296b8e335491b969f499e20e03d90f51` 일치 확인.
- `git switch -c feat/m78-axis1-candidate-handler`: 실패. `.git/refs/heads/...` lock 생성이 read-only file system으로 거부되었습니다.
- `python3 -m py_compile app/handlers/candidates.py app/web.py`: 통과.
- `python3 -m unittest tests.test_smoke 2>&1 | tail -3`: 통과. `Ran 150 tests in 1.971s`, `OK`.
- `git diff --check -- app/handlers/candidates.py app/web.py`: 통과.
- `ls app/handlers/aggregate.py 2>/dev/null && echo "FAIL: aggregate.py still exists" || echo "OK: aggregate.py deleted"`: 통과. `OK: aggregate.py deleted`.

## 남은 리스크

- 브랜치 생성이 sandbox의 `.git/refs` read-only 제한으로 실패해 변경은 `feat/m77-reviewed-memory-handler` dirty worktree에 남아 있습니다.
- `tests.test_web_app`, E2E, dist 재빌드는 handoff 검증 범위를 넘기지 않기 위해 실행하지 않았습니다.
- commit, push, PR 생성은 implement 역할 경계에 따라 수행하지 않았습니다.
