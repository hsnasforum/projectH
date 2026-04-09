# docs: remaining claim-coverage rendering wording truth sync

## 변경 파일
- `README.md` — 1곳(line 137): "focus-slot reinvestigation explanation" → "dedicated plain-language ..."
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 1365): 동일 패턴
- `docs/MILESTONES.md` — 1곳(line 41): "focus-slot reinvestigation explanation including" → "dedicated plain-language ... including"
- `docs/NEXT_STEPS.md` — 1곳(line 22): "focus-slot reinvestigation explanation" → "dedicated plain-language ..."
- `docs/TASK_BACKLOG.md` — 1곳(line 26): "focus-slot reinvestigation explanation including" → "dedicated plain-language ... including"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- smoke/rendering description 5곳에서 "dedicated plain-language" qualifier 누락
- 이전 라운드에서 instruction docs 및 current-product summary 동기화 완료
- 근거 앵커: `README.md:79`, `docs/PRODUCT_SPEC.md:107`, `docs/PRODUCT_SPEC.md:361`

## 핵심 변경
- 5개 파일에서 "focus-slot reinvestigation explanation" 앞에 "dedicated plain-language" 추가
- 기존 smoke scenario detail (tag names, particle normalization 등) 유지

## 검증
- `git diff --stat` — 5 files changed, 5 insertions(+), 5 deletions(-)
- non-qualified "focus-slot reinvestigation explanation" — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 claim-coverage rendering wording 동기화 완료
