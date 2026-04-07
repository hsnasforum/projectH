# latest-update noisy-community initial click-reload staged-doc truth-sync completion

## 변경 파일
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- initial history-card latest-update noisy-community click-reload exclusion을 설명하는 staged docs 4곳이 context box exclusion을 빠뜨리거나 generic `noisy content` shorthand에 머물러 current truth와 불일치했습니다.

## 핵심 변경
1. README 21번: `본문과 origin detail` → `본문, origin detail, context box`
2. ACCEPTANCE_CRITERIA: `본문·origin detail 미노출` → `본문, origin detail, context box 미노출`
3. MILESTONES: `보조 커뮤니티 and noisy content in origin detail and response body` → `보조 커뮤니티 and brunch in response body, origin detail, and context box`
4. TASK_BACKLOG: `보조 커뮤니티 / noisy content` → `보조 커뮤니티 / brunch in response body, origin detail, and context box`

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
- latest-update noisy-community family의 initial/follow-up/second-follow-up 전체 경로가 staged docs + root summary 모두에서 exact negative anchor truth-sync 완료 상태입니다.
