# latest-update noisy-community docs-next-steps family-closure truth-sync tightening

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 root summary가 latest-update noisy-community family를 initial-path exclusion만 적고 있었고, follow-up/second-follow-up chain closure가 later docs(README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG)와 불일치했습니다.

## 핵심 변경
1. latest-update noisy community exclusion wording에 `full natural-reload + click-reload follow-up/second-follow-up chain exclusion with 기사 교차 확인, 보조 기사, hankyung.com, mk.co.kr positive retention` 추가

## 검증
- `rg` 검증: `보조 커뮤니티`, `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`, `follow-up`, `second-follow-up` 모두 반영 확인
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
- latest-update noisy-community family와 entity-card noisy single-source claim family 모두 initial/follow-up/second-follow-up, natural-reload/click-reload 전체 경로에서 service/browser/docs(root summary 포함) 모두 truth-sync 완료 상태입니다.
