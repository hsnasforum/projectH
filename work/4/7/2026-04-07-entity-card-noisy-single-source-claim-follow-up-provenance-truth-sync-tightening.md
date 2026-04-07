# entity-card noisy single-source claim follow-up provenance truth-sync tightening

## 변경 파일
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- entity-card noisy single-source claim의 natural-reload/click-reload follow-up chain에서 noisy claim exclusion(본문/origin detail)과 noisy provenance visibility(source_paths/context box)가 분리되어야 합니다.
- 기존 테스트는 `namu.wiki`, `ko.wikipedia.org` 유지만 잠갔고, `blog.example.com`이 source_paths에 provenance로 남는 current truth를 explicit하게 잠그지 않았습니다.
- 또한 `blog.example.com`이 response text에 미노출되는 negative assertion도 빠져 있었습니다.

## 핵심 변경
1. **service test 4개 확장** (기존 테스트에 assertion 추가)
   - 4개 모두 `assertNotIn("blog.example.com", response.text)` negative assertion 추가
   - 4개 모두 `assertIn("https://blog.example.com/crimson-desert", source_paths)` provenance positive assertion 추가
2. **Playwright scenario 70-73 확장** (기존 4개 scenario에 assertion 추가)
   - 4개 모두 `expect(responseText).not.toContain("blog.example.com")` negative assertion 추가
   - 4개 모두 `await expect(contextBox).toContainText("blog.example.com")` provenance positive assertion 추가
3. **docs truth-sync**: README 70-73 rewording(provenance 포함 명시), ACCEPTANCE_CRITERIA, MILESTONES(합병), TASK_BACKLOG(provenance truth-sync 명시)

## 검증
- `python3 -m unittest -v` 4 tests OK (0.286s)
- Playwright scenario 70: 1 passed (7.9s)
- Playwright scenario 71: 1 passed (7.3s)
- Playwright scenario 72: 1 passed (7.3s)
- Playwright scenario 73: 1 passed (7.4s)
- `git diff --check`: clean

## 남은 리스크
- noisy source의 provenance는 current runtime에서 source_paths에 유지됩니다. 이것이 의도적 설계인지 향후 정리 대상인지는 별도 판단이 필요합니다.
- scenario count는 73 그대로 유지됩니다 (기존 scenario 확장, 신규 추가 없음).
