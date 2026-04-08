# browser file picker readable text-layer PDF extracted-text summary assertion tightening

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 6601 부근, 기존 readable PDF scenario에 assertion 1줄 추가)

## 사용 skill

- 없음

## 변경 이유

- 기존 readable PDF scenario는 OCR 안내 미노출과 파일명 metadata만 검증하고, 실제 text-layer가 읽혔는지는 검증하지 않았음
- fixture에 포함된 고유 문구 `local-first approval-based document assistant`가 response body에 나타나는지 직접 확인하여, PDF text-layer가 실제로 읽혀서 요약에 반영되었음을 보장

## 핵심 변경

- `expect(responseText).toContain("local-first approval-based document assistant")` assertion 추가

## 검증

- `npx playwright test -g "readable text-layer PDF"` → 1 passed (6.9s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean

## 남은 리스크

- 없음. same scenario tightening만, docs/runtime 무변경.
