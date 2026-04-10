# history-card simple entity-card load-record-id web-badge tightening

## 변경 파일
- `tests/test_web_app.py` — `test_handle_chat_load_web_search_record_id_entity_card_exact_fields` (`:8570`) 의 reload 단계 어서션 블록에 `reload_origin["badge"] == "WEB"` 한 줄을 추가. 기존 `assertIsNotNone(reload_origin)` / `answer_mode == "entity_card"` / `verification_label == "설명형 단일 출처"` / `source_roles == ["백과 기반"]` 네 어서션과 first → reload 흐름, `actions_taken == ["load_web_search_record"]`, `web_search_record_path == first_record_path` 어서션은 전혀 건드리지 않음.

## 사용 skill
- `round-handoff`

## 변경 이유
- CONTROL_SEQ 77 / 78 / 79 는 세 테스트 bundle (`:8570`, `:16545`, `:16641`) 을 지시했지만, `:16545` / `:16641` 은 dict-shaped `_FakeWebSearchTool` fixture (`"붉은사막 공식 플랫폼"` / `"붉은사막 서비스 공식"` probe + `pearlabyss.com/...boardNo=200` / `300` pages) 로 runtime 이 `설명형 다중 출처 합의` 를 방출함. 이는 `verify/4/10/2026-04-10-simple-entity-card-stored-origin-handoff-fixture-mismatch-verification.md` 에 세 라운드 재현으로 기록됨.
- CONTROL_SEQ 80 handoff 는 verify 노트를 읽고 triage 방향 (a) 를 선택 — 범위를 `:8570` 한 테스트로 축소하고 `badge == "WEB"` 한 줄만 추가.
- `:8570` 은 list-shaped `_FakeWebSearchTool([SimpleNamespace(title="붉은사막 - 나무위키", ...)])` 로 genuine simple single-source fixture 를 씀. runtime 은 `verification_label == "설명형 단일 출처"` + `source_roles == ["백과 기반"]` 을 방출하고 기존 세 literal 어서션이 이미 잠가둔 상태. 유일하게 missing 했던 것은 `badge == "WEB"` 필드 검사.
- browser 쪽은 `e2e/tests/web-smoke.spec.mjs:1379` / `:1645` 에서 simple entity-card UX 의 exact contract (`WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`) 를 이미 잠가둔 상태. 본 라운드는 그 browser 계약의 `WEB` 배지 필드를 service 층의 simple single-source anchor 에서도 literal exact 로 잠금.
- 본 라운드는 `:16545` / `:16641` 은 전혀 건드리지 않음 — verify 노트가 refuted 한 dual-probe fixture 재확장을 피함.

## 핵심 변경
1. **`tests/test_web_app.py:8570` in-place tightening**
   - 기존 `reload_origin = second["response"]["response_origin"]` + `assertIsNotNone(reload_origin)` 뒤, `assertEqual(reload_origin["answer_mode"], "entity_card")` 어서션 직전에 `self.assertEqual(reload_origin["badge"], "WEB")` 한 줄을 추가.
   - 기존 3 literal 어서션 (`answer_mode`, `verification_label`, `source_roles`) 은 그대로 유지.
   - first handle_chat → `load_web_search_record_id` reload 흐름, `first_record_path` / `record_id` 파생, `actions_taken == ["load_web_search_record"]`, `web_search_record_path == first_record_path` 어서션은 전혀 수정하지 않음.
2. **범위 밖 유지**
   - `:16545` / `:16641` (dual-probe fixture) 는 전혀 건드리지 않음 (handoff + verify 노트 명시)
   - browser 시나리오 (`e2e/tests/web-smoke.spec.mjs`) 는 이미 contract 를 잠가둔 상태로 그대로 유지
   - dual-probe / zero-strong / noisy / latest-update / store-seeded / general 가족 은 전혀 건드리지 않음
   - docs, pipeline/config, 신규 테스트 생성 은 전혀 건드리지 않음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_entity_card_exact_fields` → `ok` (신규 `badge == "WEB"` 어서션이 실제 simple single-source runtime 의 `reload_origin` 과 정확히 일치)
- `git diff --check -- tests/test_web_app.py work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — handoff 가 focused 한 anchor 만 재실행을 요구했음
- Playwright 스위트 또는 `make e2e-test` — browser 측은 건드리지 않았고 browser smoke 는 이미 simple entity-card contract 를 잠가둠
- dual-probe / 다른 가족 anchor 들 — 본 슬라이스는 single test 하나만 targets 함

## 남은 리스크
- 신규 `reload_origin["badge"] == "WEB"` 어서션은 simple single-source runtime 이 `load_web_search_record_id` reload 경로에서도 `badge == "WEB"` 를 방출한다는 가정에 의존. drift 시 본 어서션이 먼저 깨져 browser smoke 와 silent 어긋남을 방지함.
- verify 노트 (`verify/4/10/2026-04-10-simple-entity-card-stored-origin-handoff-fixture-mismatch-verification.md`) 가 refuted 한 `:16545` / `:16641` 의 dual-probe fixture 재확장은 본 라운드에서 건드리지 않음. 해당 두 테스트는 여전히 baseline-derived 비교 상태로 남아 있고, triage 가 방향 (b) / (c) 중 하나를 별도 slice 로 지시하면 그때 tighten 가능.
- CONTROL_SEQ 56-76 루프에 이어 본 CONTROL_SEQ 80 은 simple single-source load-record-id 경로의 `badge == "WEB"` missing gap 을 한 줄로 닫는 minimal slice. entity-card 가족 네 주요 분기 + actual-search / dual-probe / zero-strong 의 모든 reload stage 가 browser + service 양쪽에서 정합화된 상태에서, simple single-source load-record-id anchor 가 마지막 missing badge 필드를 보완함.
- 본 라운드는 commit / push / PR / branch publish / next slice 선택 을 수행하지 않음. handoff 지시대로 한 슬라이스 종료 후 즉시 stop.
