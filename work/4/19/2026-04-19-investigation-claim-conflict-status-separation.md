# 2026-04-19 investigation claim conflict status separation

## 변경 파일
- core/contracts.py
- core/web_claims.py
- tests/test_smoke.py

## 사용 skill
- work-log-closeout: `/work` closeout 섹션 순서와 실제 실행 검증 기록을 저장소 규약에 맞춰 정리했습니다.

## 변경 이유
- `summarize_slot_coverage()`는 이미 `_has_competing_trusted_alternative(items, primary)`로 trusted conflict를 감지하고 있었지만, 결과 status는 계속 `WEAK`로 접혀서 "근거가 약함"과 "trusted 대안이 충돌함"을 구분하지 못했습니다.
- handoff 범위 안에서 slot coverage contract만 좁게 조정해, competing trusted alternatives가 있는 슬롯을 `CoverageStatus.CONFLICT`로 따로 표면화해야 했습니다.

## 핵심 변경
- `core/contracts.py`에 `CoverageStatus.CONFLICT = "conflict"`를 추가했습니다.
- `core/web_claims.py`의 `summarize_slot_coverage()`가 `has_trusted_agreement and not has_conflict`일 때만 `STRONG`를 반환하고, `has_conflict`가 참이면 `CONFLICT`, 그 외는 기존처럼 `WEAK`를 반환하도록 바꿨습니다.
- `tests/test_smoke.py`의 conflicting trusted alternative 회귀 테스트가 이제 `CoverageStatus.CONFLICT`를 고정하도록 수정했습니다.
- 같은 테스트 묶음에서 non-conflict `STRONG`, untrusted-only `WEAK`, 빈 슬롯 `MISSING`가 그대로 유지되는지도 같이 고정했습니다.
- 이번 라운드로 competing trusted alternatives가 있는 일부 기존 `WEAK` 슬롯은 `CONFLICT`로 바뀌고, `STRONG`/non-conflict `WEAK`/`MISSING` 표면은 유지됩니다.
- 문서 wording은 현재 shipped 문장을 즉시 틀리게 만들 정도의 계약 변경이 아니어서 수정하지 않았습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k summarize_slot_coverage` → `Ran 2 tests`, `OK`
- `python3 -m py_compile core/contracts.py core/web_claims.py tests/test_smoke.py` → 출력 없음, 통과
- `git diff --check -- core/contracts.py core/web_claims.py tests/test_smoke.py` → 출력 없음, 통과

## 남은 리스크
- 이번 라운드는 handoff scope 제한 때문에 `core/agent_loop.py`, serializer, UI label/counter는 건드리지 않았습니다. 따라서 downstream 경로는 새 `conflict` 값을 아직 `WEAK`와 별도 문구/카운트로 구분하지 않을 수 있습니다.
- `tests/test_contracts.py` 같은 broader enum assertion은 이번 라운드 검증 범위에 포함하지 않았습니다. verify/handoff owner가 필요 시 wider truth-sync 범위에서 다시 확인해야 합니다.
