# 2026-04-03 document-search selected-source-path copy-action docs sync

**범위**: 새 `경로 복사` 버튼을 root docs copy-to-clipboard 목록에 반영

---

## 변경 파일

- `README.md` — copy-to-clipboard 버튼 목록에 `경로 복사` (selected source paths panel) 추가
- `docs/PRODUCT_SPEC.md` — 동일 반영
- `docs/ACCEPTANCE_CRITERIA.md` — 동일 반영

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

이전 라운드에서 `선택된 출처` 패널에 `경로 복사` 버튼이 추가됐지만, root docs 3개는 여전히 4개 버튼(`본문 복사`, `저장 경로 복사`, `승인 경로 복사`, `검색 기록 경로 복사`)만 나열해 current shipped truth와 code가 어긋남.

---

## 핵심 변경

1. 3개 docs 모두 copy-to-clipboard 버튼 목록에 `경로 복사` (selected source paths panel)을 5번째 항목으로 추가.

---

## 검증

- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` — 통과
- `rg -n "경로 복사" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` — 3개 파일 모두 반영 확인

---

## 남은 리스크

- docs-only 라운드이므로 코드/테스트 변경 없음
- `경로 복사` 버튼을 직접 잠그는 browser regression은 아직 없음 — 후속 슬라이스 가능
- search-only UI cleanup family의 docs truth-sync는 이번 라운드로 닫힌 상태
