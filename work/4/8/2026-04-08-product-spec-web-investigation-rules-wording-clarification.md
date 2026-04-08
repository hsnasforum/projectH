# PRODUCT_SPEC Web Investigation Rules wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (lines 307-313, Web Investigation Rules Implemented section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 6줄 모두 generic wording이었음
- README:68-69/128, ACCEPTANCE:37/53/1337-1341, PRODUCT_SPEC:281-288는 이미 badge surfaces, answer-mode distinction, claim coverage, history reload truth를 직접 고정
- Web Investigation Rules summary를 same truth에 맞게 정렬

## 핵심 변경

- read-only search + permission: enabled/disabled/ask per session 명시
- local JSON: in-session history reload + history-card badges 명시
- response origin: `WEB` badge, answer-mode badge, color-coded verification/source-role badges 명시
- entity-card/latest-update: separate verification labels, strong-badge downgrade truth 명시
- claim coverage: status tags, actionable hints, fact-strength summary bar, reinvestigation scaffolding 명시

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
