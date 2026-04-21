# 2026-04-20 seq 524 singleton-fallback removal implement_blocked verify note

## 변경 파일
- `verify/4/20/2026-04-20-seq-524-singleton-fallback-implement-blocked.md` (본 파일)

## 사용 skill
- `round-handoff`: implement_blocked sentinel(`BLOCK_REASON_CODE: existing_test_fixture_depends_on_removed_fallback`, `BLOCK_ID: 226bbcc643defd5e90103f39994f53740f57f6ba749826a7360586c917c6c4cb:existing_test_fixture_depends_on_removed_fallback`, `NEXT_CONTROL_SEQ: 525`) 처리 절차를 따라, 실제 repo 상태 대조 + `LatestVerifyNoteForWorkTest` 6 focused rerun + next-control 분기 판정을 수행했습니다.

## 변경 이유
- seq 524 `.pipeline/claude_handoff.md` (STATUS: implement, G7-dispatcher-repoint singleton-fallback removal, Gemini 523 advice 기반)가 구현 시도 중 sentinel block을 낸 상태로 도착했습니다.
- handoff 본문은 line 128에서 "`test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule` fixture는 `same_day_verify.write_text("# verify\n")` (no reference to work)이므로 새 계약에서는 `None`을 반환해야 하며, 이 5번째 기존 테스트를 조용히 수정하지 말고 STOP + implement_blocked with BLOCK_REASON_CODE: existing_test_fixture_depends_on_removed_fallback으로 escalate"하라고 이미 가드레일을 박아두었습니다.
- BLOCK_SOURCE=sentinel / BLOCK_REASON_CODE=existing_test_fixture_depends_on_removed_fallback는 그 가드레일이 실제로 발동했음을 뜻합니다. verify lane은 `.pipeline/claude_handoff.md` seq 524의 `HANDOFF_SHA` 226bbcc...를 이미 closed로 판정하고 seq 525 next control 하나만 작성해야 합니다.

## 핵심 변경
- `pipeline_runtime/schema.py` `latest_verify_note_for_work` (`:358-417`): HEAD 대비 byte-for-byte unchanged. 싱글턴 fallback 블록 `:373-378` (`latest_any`/`latest_any_mtime`/`candidate_count`/`latest_any_refs` 초기화) + `:387-392` (same-day loop 안 increment/update) + `:415-416` (`if candidate_count == 1 and not latest_any_refs: return latest_any`) 모두 그대로 남아 있습니다. 즉 Codex는 해당 2파일에 커밋/남겨진 edit이 없습니다.
  - 확인: `git diff --stat HEAD -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py` 결과 schema.py 8 lines / 4+/4- (그러나 `git diff HEAD -- pipeline_runtime/schema.py | head -40`로 확인하니 해당 diff는 `CONTROL_SLOT_LABELS` (`:22-25`) 한국어→영어 label rename 뿐이며 `:358-417` matching-verify dispatch 로직은 untouched).
- `tests/test_pipeline_runtime_schema.py` `LatestVerifyNoteForWorkTest` (`:337-495`): HEAD 대비 unchanged. 6 methods 그대로 (`test_prefers_explicit_work_reference_over_newer_unrelated_verify` :338, `test_accepts_cross_day_verify_when_note_explicitly_references_work` :371, `test_falls_back_to_single_same_day_verify_without_reference` :402 — 아직 old name + `self.assertEqual(resolved, verify_path)`, `test_returns_none_when_multiple_same_day_verifies_do_not_reference_work` :423, `test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule` :446 — 아직 `self.assertEqual(resolved, same_day_verify)`, `test_returns_none_when_single_same_day_verify_references_other_work` :473). 새 `test_returns_none_when_lone_unrelated_same_day_verify_mimics_manual_cleanup` 미추가.
- Block 원인 구조 (이번 verify가 Gemini 525로 routing할 때 pin해 줄 핵심):
  - seq 524 TASK 1이 `:415-416`의 `if candidate_count == 1 and not latest_any_refs: return latest_any` branch를 제거하면, `:446-471` `test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule`의 fixture — same-day verify가 `"# verify\n"`로 work reference 없이 작성되고 cross-day verify는 unrelated work를 reference — 는 새 계약에서 `None`을 반환해야 하지만 기존 assertion은 `self.assertEqual(resolved, same_day_verify)`입니다. handoff 자체가 이 5번째 기존 테스트를 slice 범위 안에서 수정하지 말라고 고정해 두었기 때문에 implement lane은 구조적으로 진행 불가.
  - 이 테스트는 seq 524 TASK 2.3 "5 methods stay byte-for-byte" 리스트(`test_returns_none_when_multiple_same_day_verifies_do_not_reference_work`, `test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule`, `test_returns_none_when_single_same_day_verify_references_other_work` 등)에 명시적으로 포함되어 있어, 같은 slice에서 flip도 delete도 불가능한 상태.
- implement lane 가능 분기 (Gemini가 그 중 하나를 pin해야 다음 seq 526이 열립니다):
  - **분기 A (test delete)**: `:446-471` `test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule`을 제거. 이 테스트가 보호하던 계약("same-day unreferenced fallback이 cross-day unrelated verify보다 우선")이 새 계약에서는 존재하지 않는 행동이기 때문. 장점: 새 계약이 원래 제거하려 한 behavior와 clean하게 맞물림. 단점: "cross-day unrelated verify가 same-day unreferenced note를 대체하지 않는다"는 2차 방어 계약이 함께 증발 — 다만 새 계약에서는 둘 다 `None`이 되므로 2차 방어는 불필요.
  - **분기 B (assertion flip to `assertIsNone`)**: `:471`을 `self.assertEqual(resolved, same_day_verify)` → `self.assertIsNone(resolved)`로 뒤집고, 메서드 이름을 `test_returns_none_when_same_day_unreferenced_and_cross_day_unrelated_both_present` (또는 동일 의미의 짧은 이름)로 개명. 장점: 6-test class가 6-test로 유지되어 grep/count 기대치 변화 최소. fixture가 여전히 의미 있는 negative case를 설명함. 단점: 메서드 이름이 원래 fallback 규칙을 지칭하기 때문에 개명 없이 assertion만 뒤집으면 독자에게 misleading.
  - **분기 C (singleton-fallback 제거 자체를 철회)**: seq 524 slice를 abandon하고 `:415-416` branch를 그대로 둠. 장점: 기존 6-test byte-for-byte 유지. 단점: Gemini 523이 판정한 dispatcher-repoint defect-vector (`VERIFY single-path lock-in` at `latest_verify_note_for_work`)는 여전히 열려 있어 다른 접근(call-site guard 등)이 필요하며, 오늘의 4라운드 재현된 repoint 버그의 1번째 vector가 닫히지 않음.
  - **분기 D (call-site guard without function-body change)**: `pipeline_runtime/schema.py`의 `latest_verify_note_for_work` 내부는 건드리지 않고, `watcher_core.py` (`:2221/2224/2249/2510`) 호출 측에서 반환된 verify note가 work-path를 명시적으로 reference하는지 한 번 더 검사해서 아닐 경우 `None`처럼 취급. 장점: 기존 schema 테스트 6개 byte-for-byte 유지. 단점: 책임이 dispatcher owner boundary(schema)에서 caller로 빠져 CLAUDE.md "Recursive Improvement" 가이드("조건문을 하나 더 얹기보다, 그 incident의 owner인 boundary/helper/module을 먼저 고칩니다")에 반함.
- canonical rolling slot 상태 (seq 525 작성 전):
  - `.pipeline/claude_handoff.md`: STATUS `implement` / CONTROL_SEQ `524` — sentinel block 상태, HANDOFF_SHA 226bbcc... closed. seq 525에서 next control로 rewrite.
  - `.pipeline/gemini_request.md`: STATUS `request_open` / CONTROL_SEQ `522` — Gemini 523 advice로 이미 응답됨, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready` / CONTROL_SEQ `523` — seq 524 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator` / CONTROL_SEQ `521` — canonical literals 유지.

## 검증
- 직접 코드 대조
  - `pipeline_runtime/schema.py:358-417` 읽음: singleton fallback 블록 `:415-416` 포함 전 구간 unchanged. Read 결과 본 verify 노트 `## 핵심 변경`에 그대로 인용.
  - `tests/test_pipeline_runtime_schema.py:337-495` 읽음: 6 methods / 467 line count / 기존 assertion 그대로. `test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule` fixture는 `:458 same_day_verify.write_text("# verify\n", encoding="utf-8")` + `:471 self.assertEqual(resolved, same_day_verify)` 그대로.
- `python3 -m unittest tests.test_pipeline_runtime_schema.LatestVerifyNoteForWorkTest -v`
  - 결과: `Ran 6 tests in 0.028s`, `OK`. 6 methods 전부 green. 즉 HEAD 계약 기준으로 fallback 포함 6 tests가 여전히 유효. seq 524 edit가 실제로 적용되지 않았음을 독립적으로 확인.
- `git diff --stat HEAD -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
  - 결과: `pipeline_runtime/schema.py | 8 ++++----` (unrelated label rename만), `tests/test_pipeline_runtime_schema.py` 변화 없음.
- `git diff HEAD -- pipeline_runtime/schema.py | head -40`
  - 결과: `CONTROL_SLOT_LABELS` (`:22-25`) 한국어 label → 영어 label rename만. `latest_verify_note_for_work` 근처 diff 0건.
- `tests.test_watcher_core`, `tests.test_pipeline_runtime_supervisor`, `tests.test_operator_request_schema`, `tests.test_pipeline_gui_backend`, `tests.test_smoke` subset는 이번 블록이 schema fallback 미편집이라 계약 변화가 없으므로 재실행 생략. 다음 seq (525 → 526) implement 라운드가 fallback을 실제로 제거한 다음에 full regression chain을 다시 돌리는 편이 자연스럽습니다.
- `tests.test_web_app`, Playwright, `make e2e-test`: browser / web 계약 미변경이라 생략.

## 남은 리스크
- **Dispatcher-repoint 버그 1번째 vector 미해결**: Gemini 523 advice가 지정한 `latest_verify_note_for_work`의 `candidate_count == 1` 싱글턴 fallback은 여전히 남아 있어, `VERIFY single-path lock-in` 증상은 이 block이 풀리기 전까지 재발 가능. 오늘의 4연속 dispatcher-repoint 재현(seq 517→518→519→520 manual-cleanup VERIFY 재사용 + 4/18 WORK backwards walk)은 여전히 열린 incident family. 다만 현재 repo의 `verify/4/18/` folder 내용은 `candidate_count > 1`이라 실제 call-site에서는 아직 fallback을 트리거하지 않을 가능성이 높으며 — 계약 hazard로 남아 있을 뿐이라는 Gemini 523의 정의와 일치.
- **Dispatcher-repoint 버그 2번째 vector (`4/18 WORK reverse-walk`) 별도 slice 대기**: seq 522 gemini_request / seq 521 operator_request에서 분리된 두 번째 defect-vector. 싱글턴 fallback 제거와 상관없이 WORK enumerator의 reverse-walk은 여전히 열려 있음. 이번 block 해결 후 별도 라운드에서 다뤄야 합니다.
- **test 계약 결정 필요**: 분기 A(delete) / 분기 B(rename + flip to assertIsNone) / 분기 C(fallback 제거 철회) / 분기 D(call-site guard) 네 선택지가 명확하지만, 어느 쪽이 "`latest_verify_note_for_work` 계약의 dispatcher-repoint hazard를 boundary level에서 닫으면서도 기존 테스트 의도를 잃지 않는가"에 대해 verify lane이 독자 판단으로 pin을 좁히기에는 confidence가 낮음. 이에 해당 분기 결정을 `.pipeline/gemini_request.md` seq 525로 escalate하고, operator는 Gemini 응답 후 seq 526에서 implement를 다시 dispatch하는 흐름을 권장.
- **Slice 범위 안정성**: 이번 block에서 verify lane은 2개 target file 어디에도 edit을 하지 않았고, 오직 verification note(본 파일) + `.pipeline/gemini_request.md` seq 525 두 파일만 작성할 예정. dirty worktree의 `pipeline_runtime/schema.py` 기존 label-rename diff는 이번 라운드와 무관하게 이미 존재.
- **오늘 docs-only round count 영향**: 이번 verify + gemini_request 한 묶음은 production Python/test 편집이 없지만 rolling control slot + verification note이므로 `/verify` README가 말하는 "same-family docs-only micro-slice 3회 이상" 룰에는 해당하지 않습니다 (docs가 아니라 control/verification layer). 오늘의 docs-only round count는 여전히 0.
- **`LatestVerifyNoteForWorkTest` 6 green 베이스라인 유지**: seq 524가 2파일 모두 미편집 상태로 종료됐으므로, HEAD 기준 6 tests green 보장. seq 526 implement가 들어가면 분기 A/B/C/D에 따라 count가 5 또는 6 또는 7로 결정될 예정.
- `normalize_decision_class` / `normalize_reason_code` 여전히 pass-through. 세 literal runtime gating은 별도 슬라이스.
- unrelated `tests.test_web_app` 10 `LocalOnlyHTTPServer` PermissionError 그대로.
