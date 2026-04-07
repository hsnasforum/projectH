# entity-card noisy-single-source docs-next-steps follow-up-chain provenance truth-sync completion

날짜: 2026-04-07

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (docs-only truth-sync correction)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 history-card entity-card noisy single-source combined follow-up/second-follow-up chain summary가 `백과 기반`, `namu.wiki`, `ko.wikipedia.org` positive retention만 적고 있어, root docs (`README.md:182-185`, `docs/MILESTONES.md:95`, `docs/ACCEPTANCE_CRITERIA.md:1391-1394`)에서 이미 적고 있는 `설명형 다중 출처 합의` 유지와 `blog.example.com` provenance in context box가 빠져 있었습니다.

## 핵심 변경
- combined chain summary에 `설명형 다중 출처 합의` positive retention과 `blog.example.com` provenance in context box를 추가하여 root/staged docs와 일치시킴
- scenario count `73` 유지
- 다른 clause (baseline click-reload, dual-probe, zero-strong-slot, latest-update family) 변경 없음

## 검증
- `git diff --check -- docs/NEXT_STEPS.md`: clean
- `rg` 교차 확인: `설명형 다중 출처 합의`, `blog.example.com`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 모두 NEXT_STEPS.md 내 해당 clause에서 확인됨
- README.md, MILESTONES.md, ACCEPTANCE_CRITERIA.md와의 cross-doc consistency 확인 완료

## 남은 리스크
- `docs/NEXT_STEPS.md:16`의 entity-card 붉은사막 natural-reload chain summary ("full natural-reload follow-up/second-follow-up chain provenance truth-sync")는 별도 follow-up clause에서 retention 항목이 이미 열거되어 있으므로 이번 라운드 범위 밖으로 유지
- code/test/runtime 변경 없음
