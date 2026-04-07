# entity-card noisy single-source claim natural-reload exact-field provenance truth-sync completion

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- click-reload half는 이전 라운드에서 noisy provenance truth-sync가 완료되었으나, natural-reload exact path의 browser/docs half가 generic 2-source fixture와 stale wording에 머물러 있었습니다.
- scenario 40은 noisy claim negative assertion이 없었고, scenario 46은 `설명형 단일 출처` fixture를 사용하여 current truth와 불일치했습니다.

## 핵심 변경
1. **Playwright scenario 40 tighten** (붉은사막 자연어 reload badge scenario)
   - fixture: generic 2-source → noisy 3-source (blog.example.com 포함)
   - assertion: origin detail/response text에 `출시일`/`2025`/`blog.example.com` 미노출, `확인된 사실:`/`교차 확인` 유지, context box에 `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance 포함
2. **Playwright scenario 46 tighten** (붉은사막 자연어 reload source-path scenario)
   - fixture: `설명형 단일 출처` → `설명형 다중 출처 합의`, 2-source → noisy 3-source
   - assertion: context box에 `blog.example.com` provenance 포함 추가
3. **docs truth-sync**: README 40/46, ACCEPTANCE_CRITERIA 1361/1367, MILESTONES 70/76, TASK_BACKLOG 59/65 — provenance 포함 명시

## 검증
- Playwright scenario 40: 1 passed (7.8s)
- Playwright scenario 46: 1 passed (7.3s)
- `git diff --check`: clean

## 남은 리스크
- scenario count는 73 그대로 유지됩니다.
- entity-card noisy single-source claim의 natural-reload + click-reload initial/follow-up/second-follow-up 전체 경로가 이제 provenance truth-sync 완료 상태입니다.
