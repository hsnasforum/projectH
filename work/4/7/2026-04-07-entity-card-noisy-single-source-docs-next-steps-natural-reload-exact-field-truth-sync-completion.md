# entity-card noisy-single-source docs-next-steps natural-reload exact-field truth-sync completion

날짜: 2026-04-07

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (docs-only truth-sync correction)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 `entity-card 붉은사막 검색 결과 browser natural-reload exact-field + noisy exclusion` clause가 `설명형 다중 출처 합의`, negative assertions, `blog.example.com` provenance, chain truth-sync만 적고 있어 root docs (`README.md:152`, `docs/MILESTONES.md:70`, `docs/ACCEPTANCE_CRITERIA.md:1361`)에서 이미 적고 있는 `방금 검색한 결과 다시 보여줘` path, `WEB` badge, `설명 카드` answer-mode badge, `백과 기반` source role, `namu.wiki`, `ko.wikipedia.org` source-path plurality가 빠져 있었습니다.

## 핵심 변경
- exact-field clause에 `방금 검색한 결과 다시 보여줘` path, `WEB` badge, `설명 카드` answer-mode badge, `백과 기반` source role retention, `namu.wiki`, `ko.wikipedia.org` source-path plurality 추가
- 기존 negative assertions (`출시일`, `2025`, `blog.example.com`)과 chain truth-sync wording 유지
- scenario count `73` 유지

## 검증
- `git diff --check -- docs/NEXT_STEPS.md`: clean
- grep 교차 확인: `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` 모두 해당 clause에서 확인됨
- README.md, MILESTONES.md, ACCEPTANCE_CRITERIA.md와의 cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (docs-only correction, 다른 clause 변경 없음)
