# docs: AGENTS ARCHITECTURE top-level mission-purpose reviewed-memory truth sync

## 변경 파일
- `AGENTS.md` — 1곳(line 5): Mission에 reviewed-memory slice 추가
- `docs/ARCHITECTURE.md` — 1곳(line 5): Purpose에 reviewed-memory slice 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- AGENTS.md Mission과 ARCHITECTURE.md Purpose가 "local-first document assistant web MVP"로만 기술하여 shipped reviewed-memory first slice 누락
- 이전 라운드에서 전체 repo docs의 one-line identity, current-contract, current-surface 요약 동기화 완료
- 이 2곳이 같은 family의 마지막 잔여

## 핵심 변경
- AGENTS:5 — "for personal document work" → "for personal document work, with the first reviewed-memory slice shipped (review queue, aggregate apply trigger, and active-effect path)"
- ARCHITECTURE:5 — "transparent evidence handling" → "transparent evidence handling, and the first reviewed-memory slice (review queue, aggregate apply trigger, and active-effect path)"

## 검증
- `git diff --stat` — 2 files changed, 2 insertions(+), 2 deletions(-)
- `rg 'reviewed-memory slice|review queue.*aggregate apply'` — 양쪽 파일 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 top-level mission/purpose reviewed-memory 동기화 완료
