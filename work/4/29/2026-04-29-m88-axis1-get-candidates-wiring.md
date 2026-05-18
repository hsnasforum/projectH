# 2026-04-29 M88 Axis 1 후보 선호 payload wiring

## 변경 파일
- `app/handlers/preferences.py`
- `tests/test_preference_handler.py`
- `work/4/29/2026-04-29-m88-axis1-get-candidates-wiring.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드의 변경 파일, 실제 실행 검증, 남은 리스크를 한국어 closeout으로 정리했다.

## 변경 이유
- M86 Axis 1에서 JSON/SQLite preference store 양쪽에 `get_candidates()`가 준비됐지만, `list_preferences_payload()`는 아직 후보 전용 조회 API를 사용하지 않았다.
- 기존 응답에는 `candidate_count`만 있고 candidate 전용 목록이 없어 app layer에서 후보 선호를 별도 정렬/조회 뷰로 전달할 수 없었다.

## 핵심 변경
- `PreferenceHandlerMixin.list_preferences_payload()`에서 `preference_store.get_candidates()`를 feature-detect해 호출하도록 추가했다.
- `get_candidates()`가 없는 store에서는 기존 `all_prefs`에서 `status == "candidate"`만 필터링하는 fallback을 유지했다.
- 반환 payload에 `candidate_preferences` 키를 추가하고, 각 후보에도 `enrich_preference_reliability()`를 적용해 reliability/quality 필드를 포함하게 했다.
- 기존 `candidate_count`와 전체 `preferences` 응답은 그대로 유지했다.
- `tests/test_preference_handler.py`에 `get_candidates()` 없는 mock store fallback 테스트와 `get_candidates()` 호출 경로 테스트를 추가했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: 요청된 `31a4c6fa61e1f75697749470b1495376ebb318851c0c6a641180fc3544b1c369`와 일치.
- `git branch --show-current && git rev-parse --short HEAD` 확인: `feat/m87-bundle`, `bddd1de`.
- `git switch -c feat/m88-axis1-get-candidates-wiring` 실패: `.git/refs/...lock` 생성이 읽기 전용 파일 시스템으로 차단됨.
- `python3 -m py_compile app/handlers/preferences.py tests/test_preference_handler.py` 통과.
- `python3 -m unittest -v tests.test_preference_handler` 통과: 22 tests OK.
- `git diff --check -- app/handlers/preferences.py tests/test_preference_handler.py` 통과.
- `git status --short -- app/frontend app/static/dist e2e` 출력 없음.
- `git status --short -- storage app/frontend app/static/dist e2e` 출력 없음.

## 남은 리스크
- 이번 변경은 backend payload에 `candidate_preferences` 키를 추가하지만 frontend/dist/E2E는 handoff 경계에 따라 수정하지 않았다.
- `candidate_preferences`는 기존 `preferences`와 별도 후보 전용 목록이며, 기존 `candidate_count`는 backward compatibility를 위해 유지했다.
- 로컬 브랜치 생성은 `.git/refs` 쓰기 제한으로 수행하지 못했다. commit, push, branch/PR publish는 하지 않았다.
