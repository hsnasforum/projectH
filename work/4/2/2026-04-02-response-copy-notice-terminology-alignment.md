# 2026-04-02 response-copy success notice terminology alignment

**범위**: copy 성공 notice를 버튼 라벨 "본문 복사" terminology에 맞게 조정
**근거**: `verify/4/2/2026-04-02-response-box-label-doc-sync-verification.md`

---

## 변경 파일

- `app/static/app.js` — copy 성공 notice "응답 텍스트를 복사했습니다." → "본문을 복사했습니다."
- `e2e/tests/web-smoke.spec.mjs` — 해당 notice assertion 동기화

---

## 사용 skill

- 없음

---

## 변경 이유

버튼 라벨이 "본문 복사"로 변경되었으나, 클릭 시 표시되는 성공 notice는 여전히 "응답 텍스트를 복사했습니다."로 되어 있어 용어 불일치.

---

## 핵심 변경

- `app/static/app.js:3389` — notice 문구 변경
- `e2e/tests/web-smoke.spec.mjs:162` — assertion 문구 동기화

---

## 검증

- targeted: `파일 요약 후 근거와 요약 구간이 보입니다` — **passed**
- `make e2e-test` — **16/16 passed**

---

## 남은 리스크

- 없음.
