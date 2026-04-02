# 2026-04-02 subtle button hover feedback

**범위**: legacy shell의 subtle 버튼(본문 복사, 패널 펼치기 등)에 hover 피드백 추가
**근거**: response-box wording family 닫힌 후 남은 가장 작은 user-visible polish

---

## 변경 파일

- `app/static/style.css` — `.icon-button.subtle`, `.copy-button.subtle`, `.toggle-button.subtle`에 hover 규칙 추가

---

## 사용 skill

- 없음

---

## 변경 이유

legacy shell의 subtle 버튼(본문 복사, 저장 경로 복사, 근거 펼치기/접기 등)은 generic `button:hover` opacity 전환만 적용되어, 사용자가 클릭 가능 여부를 직관적으로 알기 어려웠다. 배경색과 테두리 변화를 추가하여 hover 피드백을 명확히 함.

---

## 핵심 변경

```css
.icon-button.subtle:hover:not(:disabled),
.copy-button.subtle:hover:not(:disabled),
.toggle-button.subtle:hover:not(:disabled) {
  background: rgba(0,0,0,0.05);
  border-color: rgba(0,0,0,0.15);
}
```

---

## 검증

- `파일 요약 후 근거와 요약 구간이 보입니다` targeted e2e — **passed**
- CSS-only 변경이며 DOM 구조/testid 영향 없음

---

## 남은 리스크

- 없음. CSS hover 규칙 추가만.
