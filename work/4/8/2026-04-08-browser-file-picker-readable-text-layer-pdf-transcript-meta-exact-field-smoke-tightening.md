# browser file picker readable text-layer PDF transcript-meta exact-field smoke tightening

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (readable PDF scenario에 transcript meta assertion 2줄 추가)

## 사용 skill

- 없음

## 변경 이유

- 기존 readable PDF scenario는 quick meta만 검증하고 transcript meta는 검증하지 않았음
- generic file picker summary flow (line 199-202)는 transcript meta에서도 filename + `문서 요약` label을 직접 고정하는 패턴 사용
- same scenario에 동일한 transcript meta assertions 추가

## 핵심 변경

- `#transcript [data-testid="transcript-meta"]` last에 `readable-text-layer.pdf` 포함 확인
- `#transcript [data-testid="transcript-meta"]` last에 `문서 요약` 포함 확인

## 검증

- `npx playwright test -g "readable text-layer PDF"` → 1 passed (7.0s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` → clean

## 남은 리스크

- 없음. same scenario tightening만, docs/runtime 무변경.
