# 2026-04-02 entity-card weak claim qualifier wording regression

**범위**: test-only — weak claim qualifier wording을 잠그는 focused regression 추가
**근거**: `verify/4/2/2026-04-02-entity-card-weak-claim-wording-verification.md` — exact surfaced qualifier를 잠그는 regression 부재

---

## 변경 파일

- `tests/test_smoke.py` — 기존 테스트 보강 + 새 regression 1건 추가

---

## 사용 skill

- 없음

---

## 변경 이유

shipped wording 변경(`확정 표현 주의`, `확정 금지`)이 landed했으나, exact qualifier를 잠그는 regression이 없었음. generic `개발: 펄어비스` assertion만 있어서 qualifier가 사라져도 테스트가 통과할 수 있었음.

---

## 핵심 변경

1. `test_web_search_entity_summary_marks_unresolved_slots_when_claim_support_is_weak` (line 1388):
   - `"개발: 펄어비스"` → `"개발: 펄어비스 (단일 출처, 백과 기반, 확정 표현 주의)"`
   - 중복 assertion 2줄 제거

2. `test_entity_card_community_weak_claim_shows_확정_금지_qualifier` (새 테스트):
   - community-only source(blog)에서 entity card를 생성했을 때 `"비공식 출처, 확정 금지"` qualifier 확인
   - trusted qualifier(`확정 표현 주의`)가 community claim에 혼입되지 않는지 확인

---

## 검증

- `python3 -m unittest discover -s tests -p 'test_smoke*'` — **98 tests OK** (기존 97 + 새 1)
- `python3 -m unittest -v tests.test_web_app` — **187 tests OK**

---

## 남은 리스크

- 없음. test-only slice.
