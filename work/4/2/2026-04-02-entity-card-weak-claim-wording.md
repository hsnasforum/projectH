# 2026-04-02 entity-card weak claim wording honesty

**범위**: entity card의 단일 출처 claim 섹션 wording을 더 정직하게 조정
**근거**: `work/4/2/2026-04-02-uncertainty-honesty-hedging-instruction.md`의 남은 리스크 #2

---

## 변경 파일

- `core/agent_loop.py` — weak claim 섹션 헤더와 개별 claim qualifier 강화
- `tests/test_smoke.py` — 변경된 헤더 wording에 맞춰 assertion 3건 업데이트
- `tests/test_web_app.py` — 변경된 헤더 wording에 맞춰 assertion 6건 업데이트

---

## 사용 skill

- 없음

---

## 변경 이유

entity card의 "단일 출처 정보 (교차 확인 필요):" 섹션이 단일 출처 claim을 "확인 필요"로만 표기하여, 사용자가 해당 정보를 사실에 가깝게 받아들일 수 있었음. 더 명확한 불확실성 표현으로 조정.

초기 접근으로 `support_count >= 2` gating을 시도했으나 7건의 cascade test failure가 발생하여, claim 제거 대신 wording 강화로 전환.

---

## 핵심 변경

| 위치 | 이전 | 이후 |
|------|------|------|
| 섹션 헤더 | "단일 출처 정보 (교차 확인 필요):" | "단일 출처 정보 (교차 확인 부족, 추가 확인 필요):" |
| trusted 출처 qualifier | "(단일 출처, {role})" | "(단일 출처, {role}, 확정 표현 주의)" |
| community 출처 qualifier | "(비공식 출처)" | "(비공식 출처, 확정 금지)" |

---

## 검증

- `python3 -m unittest discover -s tests -p 'test_smoke*'` — **97 tests OK**
- `python3 -m unittest -v tests.test_web_app` — **187 tests OK**

---

## 남은 리스크

1. **support_count gating은 미적용**: 단일 출처 claim을 완전히 제거하지 않고 wording만 강화. broader gating은 별도 판단 필요.
