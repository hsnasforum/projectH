# 2026-04-29 M81 promote pattern auto activate

## 변경 파일

- `app/handlers/corrections.py`
- `work/4/29/2026-04-29-m81-promote-pattern-auto-activate.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록에 필요한 변경 파일, 실제 검증, 남은 리스크를 정리하기 위해 사용했습니다.

## 변경 이유

- M81 수정판 handoff가 `promote_correction_pattern`에서 명시적으로 승격한 correction pattern의 reviewed-candidate preference를 CANDIDATE 상태로 남기지 말고 즉시 ACTIVE로 전환하도록 지정했습니다.
- 이전 handoff의 테스트 파일 수정 요구와 단일 파일 경계 충돌은 CONTROL_SEQ 1291에서 해소되어, 이번 라운드는 `app/handlers/corrections.py` 한 파일만 변경했습니다.

## 핵심 변경

- `PreferenceStatus` import를 추가했습니다.
- `record_reviewed_candidate_preference()` 반환값을 `pref`로 캡처하도록 바꿨습니다.
- 반환된 preference가 `PreferenceStatus.CANDIDATE`이면 `activate_preference(pref["preference_id"])`를 호출해 즉시 ACTIVE로 전환합니다.
- 기존 `record_reviewed_candidate_preference` 계약과 cross-session `promote_from_corrections` 경로는 변경하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`: `7ae2337ccf6fd2a753d103f51c3438aa330e7c71a812528a5e86289270800f85` 일치 확인.
- `git switch -c feat/m81-axis1-promote-auto-activate`: 실패. `.git/refs/heads/...` lock 생성이 read-only file system으로 거부되었습니다.
- `python3 -m py_compile app/handlers/corrections.py`: 통과.
- `python3 -m unittest tests.test_smoke 2>&1 | tail -3`: 통과. `Ran 150 tests in 2.190s`, `OK`.
- `git diff --check -- app/handlers/corrections.py`: 통과.

## 남은 리스크

- 브랜치 생성이 sandbox의 `.git/refs` read-only 제한으로 실패해 변경은 `feat/m80-handlers-init` dirty worktree에 남아 있습니다.
- handoff 경계가 테스트 파일 수정을 금지했으므로 신규 단위 테스트는 추가하지 않았습니다. 기존 `tests.test_smoke` 150개로 회귀 확인했습니다.
- dist 재빌드, E2E, broad unittest는 handoff 범위를 넘기지 않기 위해 실행하지 않았습니다.
- commit, push, PR 생성은 implement 역할 경계에 따라 수행하지 않았습니다.
