# entity-card noisy single-source claim natural-reload + click-reload follow-up-second-follow-up milestone exact-field provenance wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 97)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `docs/MILESTONES.md:97`는 `exclusion + provenance truth-sync: 본문/origin detail에 ... 미노출`이라는 compressed framing을 사용하고 있었음
- current TASK_BACKLOG:91-94, README:184-187, ACCEPTANCE:1393-1396는 이미 `본문/detail 미노출` + `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지 + `source_paths/context box에 ... provenance 포함` exact-field retention contract를 직접 드러내는 wording 사용 중
- MILESTONES combined line을 동일한 exact-field retention framing으로 정렬
- TASK_BACKLOG:91-94는 이미 직접적 표현을 사용 중이므로 수정하지 않음

## 핵심 변경

- `MILESTONES.md:97`: `exclusion + provenance truth-sync: 본문/origin detail에 ... 미노출, source_paths/context box에 ... provenance 포함, ...` → `exclusion + provenance exact-field retention: ... 본문/detail 미노출, ... 유지, source_paths/context box에 ... provenance 포함`

## 검증

- `nl -ba docs/MILESTONES.md | sed -n '97p'` → exact-field provenance retention wording 확인
- `nl -ba docs/TASK_BACKLOG.md | sed -n '91,94p'` → 기존 직접적 표현 유지 확인
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. 이번 라운드는 MILESTONES wording만 다루었으며 runtime/README/ACCEPTANCE/browser smoke에는 변경 없음.
