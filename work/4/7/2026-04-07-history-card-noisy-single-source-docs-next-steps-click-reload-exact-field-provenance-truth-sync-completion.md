# history-card noisy-single-source docs-next-steps click-reload exact-field provenance truth-sync completion

날짜: 2026-04-07

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (docs-only truth-sync correction)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 `history-card entity-card 다시 불러오기 noisy single-source claim exclusion` click-reload exact-field clause가 `설명형 다중 출처 합의`, negative assertions, agreement-backed fact card retention, `blog.example.com` provenance만 적고 있어, root docs (`README.md:134`, `docs/MILESTONES.md:52`, `docs/ACCEPTANCE_CRITERIA.md:1343`)에서 이미 적고 있는 `백과 기반` source role과 `namu.wiki`, `ko.wikipedia.org` provenance가 빠져 있었습니다.

## 핵심 변경
- click-reload exact-field clause에 `백과 기반` source role retention 추가
- context box provenance를 `blog.example.com`만에서 `namu.wiki`, `ko.wikipedia.org`, `blog.example.com`으로 확장
- 기존 `설명형 다중 출처 합의`, negative assertions, agreement-backed fact card retention wording 유지
- scenario count `73` 유지

## 검증
- `git diff --check -- docs/NEXT_STEPS.md`: clean
- README.md:134, MILESTONES.md:52, ACCEPTANCE_CRITERIA.md:1343과의 cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (docs-only correction, 다른 clause 변경 없음)
