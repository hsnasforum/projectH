# 2026-04-01 entity-card weak vs missing slot clarity

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, entity-card 본문에서 단일 출처(weak) slot과 미확인(missing) slot의 구분을 user-visible하게 명확히 하도록 지시.
- 기존 `불확실 정보:`는 단일 출처로 확인된 정보인데 "불확실"이라는 표현이 과하게 부정적.
- 기존 `추가 확인 필요:`는 적절하지만 "아직 확인되지 않은 항목"이 missing slot의 성격을 더 명확히 전달.

## 핵심 변경
- `core/agent_loop.py` entity-card 본문 생성:
  - `불확실 정보:` → `단일 출처 확인 정보:` (단일 출처로 확인은 됐지만 교차 확인은 아직)
  - `추가 확인 필요:` → `아직 확인되지 않은 항목:` (교차 확인 가능한 근거를 찾지 못한 slot)
  - `교차 확인 가능한 근거가 더 필요합니다.` → `교차 확인 가능한 근거를 찾지 못했습니다.` (미래형 → 현재 상태 서술)
- `tests/test_smoke.py`: 기존 weak/missing section assertion 3건을 새 문구로 업데이트
- `tests/test_web_app.py`: 기존 weak/missing section assertion을 새 문구로 업데이트 (첫 응답, reload, natural recall 3경로)

## 검증
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`: 277 tests, OK (4.597s)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`: 통과

## 남은 리스크
- 문구 변경만이므로 기능적 리스크 없음.
- `claim_coverage` status 값, `rendered_as`, ranking 로직은 변경하지 않음.
- dirty worktree가 여전히 넓음.
