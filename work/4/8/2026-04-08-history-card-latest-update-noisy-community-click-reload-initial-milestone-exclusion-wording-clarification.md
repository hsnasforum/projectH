# history-card latest-update noisy-community click-reload initial milestone exclusion wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 51)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `docs/MILESTONES.md:51`는 `negative assertions for 보조 커뮤니티 and brunch`라는 generic framing을 사용하고 있었음
- current TASK_BACKLOG:40, README:133, ACCEPTANCE:1342는 이미 `negative 보조 커뮤니티 / brunch in response body, origin detail, and context box` direct exact-field wording 사용 중
- MILESTONES line을 동일한 exact-field framing으로 정렬

## 핵심 변경

- `MILESTONES.md:51`: `negative assertions for 보조 커뮤니티 and brunch` → `negative 보조 커뮤니티 / brunch`

## 검증

- `nl -ba docs/MILESTONES.md | sed -n '51p'` → exact-field exclusion wording 확인
- `nl -ba docs/TASK_BACKLOG.md | sed -n '40p'` → 기존 직접적 표현 유지 확인
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. 이번 라운드는 MILESTONES wording만 다루었으며 runtime/README/ACCEPTANCE/browser smoke에는 변경 없음.
