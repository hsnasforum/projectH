# history-card latest-update noisy-community click-reload initial docs exact-field wording clarification

## 변경 파일

- `README.md` (line 133)
- `docs/MILESTONES.md` (line 51)
- `docs/TASK_BACKLOG.md` (line 40)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1342)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- initial click-reload root docs 4곳은 negative `보조 커뮤니티`/`brunch` exclusion만 적고 있었음
- current initial smoke(e2e:1573)와 same-family follow-up/second-follow-up sibling docs(README:182-183, ACCEPTANCE:1391-1392, MILESTONES:96, TASK_BACKLOG:89-90)는 이미 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention까지 직접 드러냄
- initial root docs 4곳을 동일한 exact-field contract로 정렬

## 핵심 변경

- 4곳 모두: `보조 커뮤니티`/`brunch` exclusion only → exclusion + `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention 추가

## 검증

- `git diff --check -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 없음. initial root docs 4곳만 변경, smoke/runtime/follow-up/second-follow-up 무변경.
