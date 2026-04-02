# 2026-04-02 keyboard focus-visible feedback

**범위**: legacy shell의 chat textarea `outline: none` override 복구 + selector-local `:focus-visible` 명시
**근거**: subtle button hover family 닫힌 후 남은 가장 작은 user-visible polish

---

## 변경 파일

- `app/static/style.css` — 3곳에 `:focus-visible` 규칙 추가

---

## 사용 skill

- 없음

---

## 변경 이유

전역 `:focus-visible` 규칙(`style.css:52`)이 이미 존재하여 대부분의 interactive element에는 기본 focus ring이 작동하고 있었음. 그러나 채팅 입력 textarea(`.input-row textarea`)는 `:focus { outline: none }` 으로 명시적 제거되어 키보드 탐색 시 focus indicator가 보이지 않았음. 추가로, buttons와 form inputs에 selector-local `:focus-visible` 규칙을 명시하여 향후 전역 규칙이 바뀌더라도 accent 아웃라인이 유지되도록 함.

---

## 핵심 변경

1. `.input-row textarea:focus-visible` — chat textarea의 `outline: none` override 복구 (이번 라운드의 실질적 behavioral fix)
2. `button:focus-visible` — selector-local accent 아웃라인 명시 (전역 규칙에 의존하지 않도록)
3. `input/textarea/select:focus-visible` — form 요소에 selector-local accent 아웃라인 명시 (동일 목적)

---

## 검증

- `파일 요약 후 근거와 요약 구간이 보입니다` targeted e2e — **passed**
- CSS-only 변경이며 DOM 구조/testid 영향 없음
- dedicated keyboard-focus browser assertion은 이번 라운드에서 추가하지 않음

---

## 남은 리스크

- 없음. accessibility polish family는 이 라운드에서 닫음.
