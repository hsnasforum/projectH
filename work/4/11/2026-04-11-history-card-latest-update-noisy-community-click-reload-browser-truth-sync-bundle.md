# history-card latest-update noisy-community click-reload browser truth-sync bundle

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill

- 없음

## 변경 이유

직전 `/work` (`2026-04-11-history-card-latest-update-noisy-community-initial-response-exact-service-bundle.md`)와 대응 `/verify` (`verify/4/11/2026-04-11-history-card-latest-update-noisy-community-initial-response-verification.md`)는 noisy-community latest-update family의 service-level 계약을 initial 응답, natural-reload reload-only, natural-reload first/second follow-up, click-reload show-only, click-reload first/second follow-up까지 전부 latest-update exact-field surface + stored 두 층으로 잠갔습니다. 즉, 서비스 쪽에서 이 family는 이미 닫힌 상태입니다.

남은 same-family current-risk는 브라우저 smoke 쪽 truth drift였습니다. `e2e/tests/web-smoke.spec.mjs`의 기존 noisy-community click-reload show-only 시나리오는 프리-시드된 `response_origin` 과 history item이 여전히 mixed-source 쪽 stale truth (`label: "웹 검색"`, `verification_label: "공식+기사 교차 확인"`, `source_roles: ["보조 기사", "공식 기반"]`) 를 쓰고 있었고, 시나리오가 assert 하는 origin detail도 `공식+기사 교차 확인` / `공식 기반` 을 요구하고 있어, 현재 shipped service truth (`기사 교차 확인` / `보조 기사`) 와 어긋나고 있었습니다. 이 슬라이스는 그 단일 시나리오만 현재 shipped truth로 정렬합니다. 새 browser helper나 새 시나리오를 만들지 않고, 동일한 negative 제외 / positive retention / zero-count empty-meta 계약 위에서 fixture와 visible assertion만 현재 truth로 바꿉니다.

## 핵심 변경

`e2e/tests/web-smoke.spec.mjs`의 `history-card latest-update 다시 불러오기 후 noisy community source가 본문, origin detail, context box에 보조 커뮤니티/brunch 미노출 + 기사 교차 확인, 보조 기사, hankyung.com · mk.co.kr 유지됩니다` 시나리오에서:

1. 프리-시드 레코드 `record.response_origin` 을 현재 shipped truth로 정렬:
   - `label: "외부 웹 최신 확인"` (기존 `"웹 검색"`)
   - `kind: "assistant"` 및 `model: null` 필드 추가 (service가 직렬화하는 형태에 맞춤)
   - `verification_label: "기사 교차 확인"` (기존 `"공식+기사 교차 확인"`)
   - `source_roles: ["보조 기사"]` (기존 `["보조 기사", "공식 기반"]`)
2. `renderSearchHistory(items)` 에 전달되는 history item 도 같은 방향으로 정렬:
   - `verification_label: "기사 교차 확인"`
   - `source_roles: ["보조 기사"]`
3. 시나리오의 origin detail visible assertion 을 새 truth에 맞춰 강화:
   - `toContainText("기사 교차 확인")` 및 `toContainText("보조 기사")` 유지
   - 기존 `toContainText("공식 기반")` 및 `toContainText("공식+기사 교차 확인")` positive expect 제거
   - negative 쪽에 `expect(originDetailText).not.toContain("공식 기반")` / `expect(originDetailText).not.toContain("공식+기사 교차 확인")` 추가 → stale label leak 도 명시적으로 금지
4. 기존 negative 제외 계약 (`보조 커뮤니티`, `brunch`) 과 positive retention (`hankyung.com`, `mk.co.kr`), zero-count `.meta` no-leak (`toHaveCount(0)`, `not.toContainText("사실 검증")`) 및 컨텍스트 박스 검증 블록은 전부 그대로 유지했습니다.

noisy-community natural-reload 시나리오, 다른 follow-up 시나리오, non-noisy latest-update family, entity-card / dual-probe / zero-strong / actual-search family, service test 파일, serializer, doc 파일은 건드리지 않았습니다. 가시 시나리오 wording 자체는 바뀌지 않았고, README / ACCEPTANCE_CRITERIA / MILESTONES / TASK_BACKLOG 문구는 이미 현재 truth (`기사 교차 확인` / `보조 기사`) 를 반영하고 있어 문서 동기화 추가 편집은 필요하지 않았습니다.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source" --reporter=line` → `1 passed (7.5s)`
  - 원본 handoff 의 full-title -g 패턴은 `·` 및 `/` 등 특수 문자 때문에 Playwright regex parser가 매칭을 실패했습니다. 현 파일에는 해당 제목의 시나리오가 단 1개이므로 앞부분 고정 prefix 만으로도 정확히 동일 시나리오를 지정할 수 있고, 실행 결과 그 시나리오 하나만 선택되어 통과했습니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/11` → whitespace 경고 없음
- service 계약은 이 슬라이스에서 건드리지 않았으므로 `tests/test_web_app.py` 재실행은 불필요합니다.

## 남은 리스크

- noisy-community latest-update 쪽 natural-reload (`"방금 검색한 결과 다시 보여줘"`) browser 시나리오 및 first/second follow-up browser 시나리오는 이 라운드에서 검토하지 않았습니다. 현 smoke 파일에 그런 시나리오가 이미 있다면 같은 truth-sync가 필요한지는 별도 라운드에서 확인할 여지가 있습니다.
- entity-card family 외 다른 family (dual-probe / zero-strong / actual-search) 의 noisy browser 시나리오도 이 라운드 범위 밖입니다.
- 저장소는 여전히 dirty 상태입니다 (`tests/test_web_app.py`, `verify/4/10/...`, `verify/4/11/...`, 기존 `work/4/11/` 항목, untracked `docs/projectH_pipeline_runtime_docs/`). 이 슬라이스는 그 pending 파일들을 되돌리거나 커밋하지 않았습니다.
