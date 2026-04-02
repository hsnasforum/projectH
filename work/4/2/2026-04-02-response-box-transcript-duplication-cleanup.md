# 2026-04-02 response-box / transcript duplication cleanup

**범위**: legacy shell에서 응답 텍스트가 transcript card와 response-box 양쪽에 중복 표시되는 UX 정리
**근거**: `work/4/2/2026-04-02-legacy-web-shell-contract-recovery.md`의 남은 리스크 #1

---

## 변경 파일

- `app/static/style.css` — `#response-text`를 visually hidden (sr-only 패턴)으로 처리

---

## 사용 skill

- 없음

---

## 변경 이유

commit `0ee8e6a`에서 response-box visibility를 복구한 결과, 최신 assistant 응답 텍스트가 transcript card(채팅 이력)와 response-box(`#response-text`) 양쪽에 동일하게 표시되는 UX 중복이 발생했다. 사용자에게 같은 텍스트가 두 번 보이는 것은 혼란을 줄 수 있다.

---

## 핵심 변경

`#response-text`에 sr-only(screen-reader-only) 패턴 CSS를 적용하여 시각적으로 숨김:
```css
.response-detail-card > #response-text {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}
```

- **JS 변경 없음**: `responseText.textContent` 설정은 그대로 유지
- **copy 버튼 동작 유지**: `responseCopyTextButton` 클릭 시 `responseText.textContent`에서 텍스트를 읽음
- **e2e 테스트 호환**: Playwright의 `toContainText`는 DOM textContent를 읽으므로 visually hidden 상태에서도 통과
- **response-box는 "컨트롤 패널"로 기능**: origin badge, copy 버튼, quick-meta, feedback, correction editor, candidate confirmation 등 유용한 컨트롤만 표시

---

## 검증

- `python3 -m unittest -v tests.test_web_app` — **187 tests OK**
- `python3 -m unittest discover -s tests -p 'test_smoke*'` — **96 tests OK**
- `make e2e-test` — **16/16 passed** (1.6m)

---

## 남은 리스크

1. **response-box "응답" 섹션 타이틀**: 텍스트가 숨겨진 상태에서 "응답" 타이틀이 다소 모호할 수 있으나, origin badge와 copy 버튼이 같은 헤더에 있어 맥락은 유지됨.
2. **React frontend 미연결**: 이번 slice 범위 밖.
3. **병렬 stress hardening**: 이번 slice 범위 밖.
