# 2026-04-02 community qualifier regression — vacuous→non-vacuous fix

**범위**: test-only — community weak-claim qualifier regression을 non-vacuous로 교체
**근거**: `verify/4/2/2026-04-02-entity-card-weak-claim-qualifier-regression-verification.md` — conditional guard로 no-op 통과 가능

---

## 변경 파일

- `tests/test_smoke.py` — `test_entity_card_community_weak_claim_shows_확정_금지_qualifier` → `test_entity_card_community_only_source_does_not_surface_weak_claim_section` 교체

---

## 사용 skill

- 없음

---

## 변경 이유

이전 테스트는 `if "단일 출처 정보" in response.text:` conditional guard 아래에 assertion을 넣어, community-only fixture에서 해당 섹션이 surfacing되지 않으면 no-op으로 통과했음.

분석 결과, runtime 변경 없이는 non-vacuous community qualifier fixture 구성이 **불가능**함:
- `weak_selected`에 들어가려면 `best.source_role in TRUSTED_CLAIM_SOURCE_ROLES` 필요
- `TRUSTED_CLAIM_SOURCE_ROLES` = `{WIKI, OFFICIAL, DATABASE, DESCRIPTIVE}`
- community 출처 (`보조 커뮤니티`, `보조 포털`, `보조 블로그`)는 포함되지 않음
- 따라서 "비공식 출처, 확정 금지" qualifier는 현재 **도달 불가능한 dead code**

---

## 핵심 변경

vacuous conditional test를 제거하고, community-only fixture가 "단일 출처 정보" 섹션을 surfacing하지 않는다는 현재 gating behavior를 **unconditional assertion**으로 잠금:
- `assertNotIn("단일 출처 정보", response.text)` — 섹션 자체 부재 확인
- `assertNotIn("비공식 출처, 확정 금지", response.text)` — dead code 도달 불가 확인
- `assertNotIn("확정 표현 주의", response.text)` — trusted qualifier 혼입 방지

---

## 검증

- `python3 -m unittest discover -s tests -p 'test_smoke*'` — **98 tests OK**
- `python3 -m unittest -v tests.test_web_app` — **187 tests OK**

---

## 남은 리스크

1. **"비공식 출처, 확정 금지" qualifier는 dead code**: community 출처는 현재 gating에서 `weak_selected`에 진입할 수 없어 해당 분기에 도달하지 못함. 이 dead code를 제거하거나 gating을 변경하려면 별도 runtime behavior 변경 slice 필요.
