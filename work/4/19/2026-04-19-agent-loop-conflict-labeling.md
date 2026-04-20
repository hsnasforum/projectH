# 2026-04-19 agent loop conflict labeling

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- work-log-closeout: `/work` closeout 형식과 실제 검증 기록을 저장소 규약에 맞춰 정리했습니다.

## 변경 이유
- 직전 라운드에서 `CoverageStatus.CONFLICT`가 slot coverage contract에는 추가됐지만, `core/agent_loop.py` 안에서는 여전히 `WEAK`/`MISSING` fall-through처럼 취급되어 `"미확인"` 라벨, `0` rank, unresolved 누락, probe query 누락으로 납작해지고 있었습니다.
- 이번 라운드는 handoff 범위대로 agent loop 내부에서만 `CONFLICT`를 별도 의미로 통과시켜, trusted conflict가 재조사/라벨링 분기에서 약한 근거나 미확인과 섞이지 않도록 고정하는 데 목적이 있었습니다.

## 핵심 변경
- `core/agent_loop.py`의 `_claim_coverage_status_rank()`가 `STRONG=3`, `CONFLICT=2`, `WEAK=1`, 그 외 `0`을 반환하도록 바꿨습니다. 이로써 이전 `WEAK`였던 같은 슬롯이 현재 `CONFLICT`가 되어도 회귀로 계산되지 않습니다.
- `_claim_coverage_status_label()`에 `CoverageStatus.CONFLICT -> "정보 상충"`을 추가하고, 기존 `STRONG -> "교차 확인"`, `WEAK -> "단일 출처"`, fallback `-> "미확인"`은 유지했습니다.
- `_build_claim_coverage_progress_summary()`의 unresolved 집합에 `CoverageStatus.CONFLICT`를 포함해, focus slot이 계속 conflict일 때도 `"재조사했지만 ... 아직 정보 상충 상태입니다."` 경로로 남도록 했습니다.
- `_build_entity_slot_probe_queries()`는 compact primary claim이 있는 `CONFLICT` 슬롯에도 기존 `WEAK`와 같은 targeted probe query를 재사용하도록 넓혔습니다.
- 이번 라운드는 `WEAK`나 `MISSING` 상태를 새로 `CONFLICT`로 바꾸지 않았습니다. 이미 `CONFLICT`로 계산된 슬롯만 label/rank/unresolved/probe에서 더 이상 `WEAK/MISSING` 의미로 붕괴되지 않게 했고, 기존 `WEAK`/`MISSING` 표면은 유지됩니다.
- 문서 wording은 바꾸지 않았습니다. 현재 shipped 문장을 즉시 틀리게 만드는 범위는 아니었고, `app/serializers.py`의 `claim_coverage_summary` CONFLICT counter도 의도적으로 건드리지 않아 별도 후속 후보로 남겼습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k coverage` → `Ran 12 tests`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` → 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py` → 출력 없음, 통과

## 남은 리스크
- 이번 라운드는 handoff scope 제한 때문에 `app/serializers.py`의 `claim_coverage_summary` CONFLICT counter를 추가하지 않았습니다. 외부 payload summary는 아직 `CONFLICT`를 별도 카운트로 드러내지 않습니다.
- `core/agent_loop.py`의 wording surface는 기존 focus-slot 문장을 그대로 재사용했기 때문에, `CONFLICT` 전용 추가 문구나 stronger explanation은 아직 없습니다. 이번 라운드는 unresolved membership과 label/rank 구분만 우선 고정했습니다.
