# entity-card noisy single-source claim initial click-reload milestones-backlog truth-sync completion

## 변경 파일
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- MILESTONES와 TASK_BACKLOG의 entity-card noisy single-source claim initial click-reload 항목이 `출시일`/`2025` negative assertion과 agreement-backed fact card retention만 적고 있어, `blog.example.com` negative/provenance, `설명형 다중 출처 합의`, `백과 기반` 등 current truth보다 약했습니다.

## 핵심 변경
1. MILESTONES: `blog.example.com` negative + provenance, `설명형 다중 출처 합의`, `백과 기반` 추가
2. TASK_BACKLOG: 동일 패턴 추가

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
- entity-card noisy single-source claim family의 initial/follow-up/second-follow-up 전체 경로가 모든 docs에서 truth-sync 완료 상태입니다.
