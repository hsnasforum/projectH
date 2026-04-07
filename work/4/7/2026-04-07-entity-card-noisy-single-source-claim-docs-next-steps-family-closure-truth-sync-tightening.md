# entity-card noisy single-source claim docs-next-steps family-closure truth-sync tightening

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 root summary가 entity-card noisy single-source claim family를 initial path만 noisy-specific으로 적고 있었고, follow-up/second-follow-up provenance closure가 later docs(README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG)와 불일치했습니다.

## 핵심 변경
1. history-card entity-card noisy exclusion wording에 `full follow-up/second-follow-up chain provenance truth-sync for both click-reload and natural-reload paths` 추가
2. entity-card 붉은사막 natural-reload noisy exclusion wording에 `full natural-reload follow-up/second-follow-up chain provenance truth-sync` 추가

## 검증
- `rg` 검증: `설명형 다중 출처 합의`, `blog.example.com`, `follow-up`, `second-follow-up` 모두 반영 확인
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
- entity-card noisy single-source claim family의 initial/follow-up/second-follow-up, natural-reload/click-reload 전체 경로가 service/browser/docs(root summary 포함) 모두에서 provenance truth-sync 완료 상태입니다.
