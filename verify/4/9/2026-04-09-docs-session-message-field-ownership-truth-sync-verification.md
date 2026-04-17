# Docs session message field ownership truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-session-message-field-ownership-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 지정된 `/work`가 `docs/PRODUCT_SPEC.md` / `docs/ACCEPTANCE_CRITERIA.md`의 session message field ownership drift를 실제로 어디까지 닫았는지 다시 확인하고, `/verify`를 먼저 갱신한 뒤 `CONTROL_SEQ: 277`의 단일 다음 제어를 확정할 필요가 있었습니다.
- 현재 저장소에는 같은 날의 후속 bundle `work/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync.md`와 그 `/verify`가 이미 존재하므로, 대상 `/work` 자체의 판정과 그 직후 필요한 다음 슬라이스를 분리해서 기록합니다.

## 핵심 변경
- 대상 `/work`는 부분적으로만 truthful합니다.
  - `original_response_snapshot`, `corrected_text`, `corrected_outcome`, `content_reason_record`를 grounded-brief source message ownership으로 좁힌 점과 `approval_reason_record`를 reject/reissue approval trace ownership으로 분리한 점은 현재 코드/문서 truth와 맞습니다.
  - 하지만 closeout의 `세션 메시지 필드 소유권 진실 동기화 완료`는 과합니다. `save_content_source`와 `source_message_id`는 save/approval trace messages뿐 아니라 direct approved save 뒤의 grounded-brief source message에도 나타납니다.
- 현재 코드/테스트 근거:
  - `storage/session_store.py:644-650`은 grounded-brief source message에 `source_message_id`를 채웁니다.
  - `tests/test_smoke.py:3376-3378`, `tests/test_smoke.py:3472-3474`, `tests/test_smoke.py:5049-5050`은 session message surface에서 source message / saved message가 `source_message_id`, `save_content_source`를 가진다고 확인합니다.
  - `tests/test_web_app.py:813-837`도 corrected-save approval/saved message 경로에서 같은 ownership을 확인합니다.
- 현재 문서는 같은 날 후속 bundle 덕분에 이 잔여 drift를 이미 닫았습니다 (`docs/PRODUCT_SPEC.md:280-286`, `docs/ACCEPTANCE_CRITERIA.md:106-109`). 따라서 이 `/work`의 truthful 판정은 여전히 "부분 완료"이고, `seq 277`의 정확한 다음 제어는 그 잔여 두 필드를 묶어 닫는 bounded docs bundle이어야 합니다.
- 다음 제어는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ACCEPTANCE_CRITERIA session message save_content_source source_message_id ownership truth sync`로 고정했습니다.
  - 같은 날 same-family docs-only truth-sync가 이미 3회 이상 반복됐으므로, 또 다른 더 작은 micro-slice 대신 `save_content_source` + `source_message_id`를 두 문서에서 함께 닫는 한 번의 bundle이 맞습니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,240p' work/README.md`
- `sed -n '1,240p' verify/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-session-message-field-ownership-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-session-message-field-ownership-truth-sync-verification.md`
- `sed -n '1,220p' work/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync-verification.md`
- `ls -1 work/4/9`
- `ls -1 verify/4/9`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '247,290p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '92,110p'`
- `nl -ba app/serializers.py | sed -n '96,135p'`
- `nl -ba storage/session_store.py | sed -n '628,700p'`
- `nl -ba core/agent_loop.py | sed -n '7336,7387p'`
- `rg -n "save_content_source|source_message_id" tests/test_web_app.py tests/test_smoke.py -S`
- `nl -ba tests/test_web_app.py | sed -n '770,782p'`
- `nl -ba tests/test_web_app.py | sed -n '804,840p'`
- `nl -ba tests/test_smoke.py | sed -n '3344,3490p'`
- `nl -ba tests/test_smoke.py | sed -n '5036,5065p'`
- `git diff --check`

## 남은 리스크
- 이번 검수는 docs/code truth 대조와 `git diff --check`만 재실행했습니다. unit test와 Playwright는 다시 돌리지 않았습니다.
- 현재 저장소가 이미 후속 same-family bundle까지 포함하고 있어 2026-04-09 당시의 정확한 중간 문구 상태를 그대로 재현하지는 못합니다. 대신 대상 `/work`, 후속 `/work`·`/verify`, 현재 코드/문서의 교집합으로 truthful 판정을 남겼습니다.
