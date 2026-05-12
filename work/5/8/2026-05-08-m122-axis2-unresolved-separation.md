# 2026-05-08 M122 Axis 2 unresolved separation

## 변경 파일

- `core/contracts.py`
- `core/web_claims.py`
- `core/agent_loop.py`
- `tests/test_smoke.py`
- `work/5/8/2026-05-08-m122-axis2-unresolved-separation.md`

## 사용 skill

- `investigation-quality-audit`: entity-card claim coverage 상태 분리와 second-pass query 우선순위 변경이 web investigation의 불확실성 표면화, 신뢰 소스 기준, 재조사 동작에 미치는 영향을 점검했다.
- `work-log-closeout`: 구현 라운드 종료 기록의 필수 섹션, 실제 검증 결과, 남은 리스크 정리에 사용했다.

## 변경 이유

- M122 Axis 1 이후에도 신뢰 소스가 0개인 슬롯과 신뢰 소스 1개인 슬롯이 모두 `WEAK`로 묶여 있었다.
- 이번 Axis 2 backend 슬라이스에서는 `CoverageStatus.UNRESOLVED`를 추가해 완전 미해결 슬롯을 분리하고, 해당 슬롯이 second-pass에서 더 적극적인 probe 쿼리를 받도록 했다.

## 핵심 변경

- `CoverageStatus.UNRESOLVED = "unresolved"`를 추가하고 기존 `WEAK`는 신뢰 소스 1개 상태로 남겼다.
- `summarize_slot_coverage()`가 trusted supporter 0개인 primary claim을 `UNRESOLVED`, trusted supporter 1개를 `WEAK`, trusted supporter 2개 이상을 기존처럼 `STRONG`/`CONFLICT`로 판정하게 했다.
- reinvestigation suggestion priority에서 `UNRESOLVED`를 `MISSING`과 같은 최우선 그룹으로 취급하게 했다.
- `_build_entity_second_pass_queries()`에서 `UNRESOLVED` 슬롯을 zero-trusted workaround 대신 명시 상태로 정렬하고, probe-first 및 2-query boost 대상에 포함했다.
- `_build_entity_slot_probe_queries()`가 `UNRESOLVED` primary claim에도 compact value 기반 확인 쿼리를 만들게 했다.
- `tests/test_smoke.py`에 UNRESOLVED/WEAK/STRONG/CONFLICT 분리와 UNRESOLVED second-pass probe 동작 회귀 테스트를 추가했다.

## 검증

- `python3 -m py_compile core/contracts.py core/web_claims.py core/agent_loop.py`
  - PASS.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_summarize_slot_coverage_untrusted_only_agreement_is_unresolved tests.test_smoke.SmokeTest.test_summarize_slot_coverage_mixed_trust_requires_two_trusted_supporters tests.test_smoke.SmokeTest.test_summarize_slot_coverage_separates_unresolved_from_weak_without_breaking_strong_conflict tests.test_smoke.SmokeTest.test_second_pass_prioritizes_unresolved_over_positive_trusted_weak tests.test_smoke.SmokeTest.test_second_pass_unresolved_slot_prefers_probe_first_and_allows_two_queries tests.test_smoke.SmokeTest.test_entity_slot_probe_queries_include_primary_value_for_unresolved`
  - PASS: 6개 테스트 통과.
- `python3 -m unittest -v tests.test_smoke`
  - PASS: 155개 테스트 통과.
- `git diff --check -- core/contracts.py core/web_claims.py core/agent_loop.py tests/test_smoke.py`
  - PASS: 출력 없음.
- `git diff --check -- core/contracts.py core/web_claims.py core/agent_loop.py tests/test_smoke.py work/5/8/2026-05-08-m122-axis2-unresolved-separation.md`
  - PASS: 출력 없음.

## 남은 리스크

- 이번 라운드는 backend 상태 분리만 수행했다. 핸드오프 금지 범위에 따라 frontend/UI/E2E와 `docs/`는 수정하지 않았다.
- line 4374 이후 display/hint 함수는 수정하지 않았다. 따라서 `UNRESOLVED`의 사용자 표시 문구와 history/progress 표면은 다음 Axis 또는 doc-sync/UI 슬라이스에서 별도 정리가 필요할 수 있다.
- web investigation은 계속 secondary, read-only, permission-gated, locally logged 경계 안에 있으며 외부 fetch/search 권한 모델은 바꾸지 않았다.
