# 2026-04-03 document-search selected-source-path copy-action regression coverage

**범위**: `경로 복사` 버튼의 회귀 검증 추가 (e2e + unit HTML contract)

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에 `selected-copy` 버튼 노출/클릭/notice/clipboard 검증 추가
- `tests/test_web_app.py` — HTML contract assertion에 `selected-copy` 존재 확인 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

이전 라운드에서 `선택된 출처` 패널에 `경로 복사` 버튼이 추가되고 docs도 동기화되었지만, `selected-copy` 버튼이 실제로 보이고 동작하는지를 자동으로 잠그는 regression coverage가 없었음. 이 회귀 잠금 부재가 같은 family 내 마지막 current-risk였음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — 기존 "검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다" 시나리오 안에서:
   - `selected-copy` 버튼 `toBeVisible()` 확인
   - clipboard permission 부여 후 클릭
   - `#notice-box`에 "선택 경로를 복사했습니다." 텍스트 확인
   - clipboard 내용에 "budget-plan.md" 포함 확인
2. `tests/test_web_app.py` — `test_render_index_contains_demo_shell` HTML contract assertion에 `selected-copy` ID 존재 확인 1행 추가.

---

## 검증

- `python3 -m unittest -v tests.test_web_app` — 187 passed, OK
- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs tests/test_web_app.py` — 통과

---

## 남은 리스크

- smoke 시나리오 수는 17로 변동 없음 (기존 시나리오 안에 assertion만 추가). docs 동기화 불필요.
- `selected-copy` family의 code/docs/regression coverage가 모두 정합한 상태. same-family current-risk 닫힘.
