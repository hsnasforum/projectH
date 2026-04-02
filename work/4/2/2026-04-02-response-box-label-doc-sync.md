# 2026-04-02 response-box label root-doc truth sync

**범위**: root docs의 `응답 복사` 라벨을 현재 shipped label `본문 복사`로 동기화
**근거**: `verify/4/2/2026-04-02-response-box-header-semantics-cleanup-verification.md`

---

## 변경 파일

- `README.md` — `응답 복사` → `본문 복사`
- `docs/PRODUCT_SPEC.md` — `응답 복사` → `본문 복사`
- `docs/ACCEPTANCE_CRITERIA.md` — `응답 복사` → `본문 복사`

---

## 사용 skill

- 없음

---

## 변경 이유

이전 라운드에서 `app/templates/index.html`의 copy 버튼 라벨이 "응답 복사"에서 "본문 복사"로 변경되었으나, root docs 3개 파일은 여전히 "응답 복사"를 current label로 적고 있었음.

---

## 핵심 변경

3개 파일에서 `응답 복사` → `본문 복사` 문자열 교체 (각 1건).

---

## 검증

- `git diff --check` — 통과
- `grep` — 4개 파일(README, PRODUCT_SPEC, ACCEPTANCE_CRITERIA, index.html) 모두 `본문 복사` / `응답 도구` 일관성 확인

---

## 남은 리스크

- 없음. 텍스트-only 동기화.
