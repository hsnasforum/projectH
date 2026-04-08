# history-card entity-card noisy single-source claim click-reload initial milestone exact-field provenance wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 52)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `docs/MILESTONES.md:52`는 `negative assertions for ... positive assertions for agreement-backed fact card retention`이라는 generic framing을 사용하고 있었음
- current TASK_BACKLOG:41, README:134, ACCEPTANCE:1343는 이미 `negative 출시일 / 2025 / blog.example.com in response body and origin detail, positive agreement-backed fact card, ... provenance in context box/source_paths` exact-field wording 사용 중
- MILESTONES line을 동일한 exact-field framing으로 정렬

## 핵심 변경

- `MILESTONES.md:52`: `negative assertions for ... positive assertions for agreement-backed fact card retention, and ...` → `negative 출시일 / 2025 / blog.example.com in response body and origin detail, positive agreement-backed fact card, ... provenance in context box/source_paths`

## 검증

- `nl -ba docs/MILESTONES.md | sed -n '52p'` → exact-field provenance wording 확인
- `nl -ba docs/TASK_BACKLOG.md | sed -n '41p'` → 기존 직접적 표현 유지 확인
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. 이번 라운드는 MILESTONES wording만 다루었으며 runtime/README/ACCEPTANCE/browser smoke에는 변경 없음.
