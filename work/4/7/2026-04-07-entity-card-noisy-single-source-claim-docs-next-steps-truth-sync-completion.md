# entity-card noisy single-source claim docs-next-steps truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 Playwright coverage 요약에서 entity-card noisy single-source claim family가 stale했습니다.
- history-card click-reload initial path가 generic `설명형 단일 출처`로 남아 있었고, entity-card 붉은사막 natural-reload도 generic smoke로만 서술되어 current truth와 불일치했습니다.

## 핵심 변경
1. history-card click-reload initial path: `설명형 단일 출처` → `설명형 다중 출처 합의`
2. history-card entity-card noisy single-source claim exclusion: `출시일`/`2025`/`blog.example.com` 본문/detail 미노출 + `blog.example.com` provenance in context box 명시
3. entity-card 붉은사막 natural-reload exact-field: generic smoke → noisy exclusion + provenance smoke 명시 (`설명형 다중 출처 합의`, `출시일`/`2025`/`blog.example.com` 미노출, context box provenance)

## 검증
- `rg` 검증: `설명형 단일 출처` 잔존 1건은 zero-strong-slot 정당한 사용
- `설명형 다중 출처 합의`, `blog.example.com` 1건씩 현재 truth 반영 확인
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
- entity-card noisy single-source claim family의 initial/follow-up/second-follow-up, natural-reload/click-reload 전체 경로가 service/browser/docs 모두에서 provenance truth-sync 완료 상태입니다.
