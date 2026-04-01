# 2026-03-31 entity-card zero-strong-slot verification badge downgrade

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, entity-card에서 strong slot이 0개일 때 verification badge가 과장되는 current-risk를 수정하도록 지시.
- 기존 `_build_web_verification_label`은 entity-card에서 source type만 보고 `설명형 다중 출처 합의`(strong label)를 부여. strong-reference source가 2개여도 실제 claim_coverage에 strong slot이 0개이면 badge와 본문이 불일치.

## 핵심 변경

### production 변경 (`core/agent_loop.py`)
1. `_build_web_search_origin`에 `claim_coverage` optional parameter 추가
2. `_build_web_verification_label`에 `claim_coverage` optional parameter 추가
3. entity-card 분기에서 `strong_reference_count >= 2` 조건에 `has_strong_slot` 검사 추가:
   - claim_coverage에 `status == "strong"` 항목이 1개 이상 있을 때만 `"설명형 다중 출처 합의"` 반환
   - strong slot이 0개이면 기존 fallback label(`"공식 단일 출처"`, `"설명형 단일 출처"`, `"다중 출처 참고"`, `"단일 출처 참고"`)로 downgrade
4. initial search 경로와 reload 경로 모두에서 `claim_coverage`를 `_build_web_search_origin`에 전달

### 테스트 변경 (`tests/test_smoke.py`)
- `test_entity_card_zero_strong_slot_downgrades_verification_label` 추가
  - fixture: wiki 2개(namu.wiki + ko.wikipedia.org)이지만 fact bullet이 cross-verify되지 않는 텍스트
  - 검증: `answer_mode == "entity_card"`, `verification_label != "설명형 다중 출처 합의"`, claim_coverage에 strong 항목 0개

### docs 변경
- `README.md`: verification-strength badge 설명에 entity-card downgrade 규칙 추가
- `docs/PRODUCT_SPEC.md`: claim verification panel 설명에 entity-card badge downgrade 추가
- `docs/ACCEPTANCE_CRITERIA.md`: history card badge 기준에 zero-strong-slot downgrade 규칙 명시

## 검증
- `python3 -m unittest -v tests.test_smoke`: 94 tests, OK (1.062s)
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_web_search_serializes_claim_coverage`: OK
- `git diff --check -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`: 통과
- `python3 -m unittest -v tests.test_web_app`: 실행하지 않음 (focused claim_coverage test로 충분)

## 남은 리스크
- `claim_coverage`가 None이거나 빈 리스트일 때(non-entity 경로)는 `has_strong_slot = False`이므로 entity-card에서 claim_coverage 없이 `_build_web_search_origin`이 호출되면 항상 downgrade됨. 현재 entity-card 경로에서는 항상 claim_coverage를 계산하므로 실질 위험 없음.
- dirty worktree가 여전히 넓음.
