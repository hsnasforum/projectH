# 2026-04-02 keyboard focus-visible feedback

**범위**: legacy shell의 buttons, inputs, textarea, select에 `:focus-visible` 아웃라인 추가
**근거**: subtle button hover family 닫힌 후 남은 가장 작은 user-visible polish — 키보드 탐색 시 focus 피드백 부재

---

## 변경 파일

- `app/static/style.css` — 3곳에 `:focus-visible` 규칙 추가

---

## 사용 skill

- 없음

---

## 변경 이유

legacy shell의 모든 interactive element(buttons, inputs, textarea, select)에 키보드 탐색 시 visible focus indicator가 없었음. `:hover` 효과만 있고 `:focus-visible` 아웃라인이 빠져 있어, 키보드 사용자가 현재 포커스 위치를 식별하기 어려웠음. 특히 채팅 입력 textarea는 `outline: none`으로 명시적 제거되어 있었음.

---

## 핵심 변경

1. `button:focus-visible` — 모든 버튼에 accent 아웃라인
2. `input/textarea/select:focus-visible` — 모든 form 요소에 accent 아웃라인
3. `.input-row textarea:focus-visible` — 채팅 입력란에 `outline: none` 오버라이드

---

## 검증

- `파일 요약 후 근거와 요약 구간이 보입니다` targeted e2e — **passed**
- CSS-only 변경이며 DOM 구조/testid 영향 없음

---

## 남은 리스크

- 없음. CSS `:focus-visible` 추가만.
