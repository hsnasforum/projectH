# 2026-04-03 document-search selected-source-path copy action

**범위**: `선택된 출처` 패널에 경로 목록 복사 버튼 추가

---

## 변경 파일

- `app/templates/index.html` — `#selected-box`에 `panel-header` wrapper와 `#selected-copy` 복사 버튼 추가
- `app/static/app.js` — `selectedCopyButton` 참조 + click handler (`selectedText.textContent` 복사, "선택 경로를 복사했습니다." 알림)

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-only preview-only 상태에서 `본문 복사`가 숨겨진 후, 사용자가 검색 결과 경로를 빠르게 복사할 explicit affordance가 없었음. `선택된 출처` 패널에 경로 목록 복사 버튼을 추가하여 search-only와 search+summary 모두에서 사용 가능하게 함.

---

## 핵심 변경

1. `app/templates/index.html` — `#selected-box` 내부를 `panel-header` div로 감싸고, `<button id="selected-copy" class="copy-button subtle">경로 복사</button>` 추가.
2. `app/static/app.js` — `selectedCopyButton` 요소 참조, click handler에서 `copyTextValue(selectedText.textContent, "선택 경로를 복사했습니다.")` 호출. 기존 `responseCopyPathButton`, `responseCopyTextButton` 패턴과 동일.

---

## 검증

- `make e2e-test` — **17 passed**
- `git diff --check -- app/templates/index.html app/static/app.js` — 통과

---

## 남은 리스크

- 복사 기능은 `navigator.clipboard.writeText` 기반이므로 HTTPS 또는 localhost에서만 동작 (기존 모든 copy 버튼과 동일한 제약)
- search-only와 search+summary 모두에서 `선택된 출처` 패널이 보이면 버튼도 보임 — 의도된 동작
- docs에 새 copy action 설명 추가는 다음 docs-sync 슬라이스에서 처리 가능 (현재 docs에 `선택된 출처` 패널 자체의 상세 설명이 없어 최소 추가 대상이 명확하지 않음)
