# 2026-05-08 M123 Axis 2 unresolved official boost

## 변경 파일

- `core/agent_loop.py`
- `tests/test_smoke.py`
- `work/5/8/2026-05-08-m123-axis2-unresolved-official-boost.md`

## 사용 skill

- `investigation-quality-audit`: entity-card second-pass source 선택과 UNRESOLVED probe 변경이 웹 조사 품질/불확실성 표시에 미치는 범위를 확인했습니다.
- `work-log-closeout`: 지정된 `/work` closeout 형식으로 변경 파일, 검증, 남은 리스크를 기록했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1586의 M123 Axis 2 지시를 실행했습니다.
- trusted 출처 0개인 UNRESOLVED 슬롯에서 값이 없을 때 공통 fallback보다 공식/나무위키 성격의 넓은 probe 쿼리를 먼저 사용해 second-pass 조사 품질을 높이기 위한 변경입니다.

## 핵심 변경

- `_build_entity_slot_probe_queries()`에서 `status == CoverageStatus.UNRESOLVED`이고 `primary_claim.value`가 비어 있을 때 슬롯별 공식/나무위키 probe 쿼리를 반환하도록 추가했습니다.
- UNRESOLVED에 값이 있는 경우의 기존 untrusted value 포함 쿼리, WEAK/CONFLICT/MISSING fallback 분기는 유지했습니다.
- entity-card second-pass 루프의 `_select_ranked_web_sources(..., max_items=3)`를 `max_items=5`로 확장했습니다.
- `tests/test_smoke.py`에 무값 UNRESOLVED probe 직접 테스트와 second-pass source 선택 인자 검사를 추가했습니다.

## 검증

- PASS: `python3 -m py_compile core/agent_loop.py`
- PASS: `python3 -m unittest -v tests.test_smoke.SmokeTest.test_unresolved_slot_no_value_produces_official_site_query tests.test_smoke.SmokeTest.test_second_pass_source_selection_uses_five_items`
- PASS: `python3 -m unittest -v tests.test_smoke` (160 tests)
- PASS: `git diff --check -- core/agent_loop.py tests/test_smoke.py`

## 남은 리스크

- 실제 live 웹 검색은 실행하지 않았고 fixture/unit smoke로 검증했습니다.
- UI, 저장 스키마, 사용자-facing 문구 변경이 없어 문서 동기화는 하지 않았습니다. handoff 금지 범위에 따라 `.pipeline/`, frontend, E2E, publish 작업은 건드리지 않았습니다.
