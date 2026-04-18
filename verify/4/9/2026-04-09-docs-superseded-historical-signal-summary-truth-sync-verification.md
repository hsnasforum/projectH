# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA superseded historical signal summary truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-superseded-historical-signal-summary-truth-sync-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- `work/4/9/2026-04-09-docs-superseded-historical-signal-summary-truth-sync.md`가 `docs/PRODUCT_SPEC.md`와 `docs/ACCEPTANCE_CRITERIA.md`의 `superseded_reject_signal` / `historical_save_identity_signal` summary wording을 현재 구현 truth와 맞췄다고 기록해, 현재 문서/코드/회귀 테스트 기준으로 다시 대조해야 했습니다.
- 기존 verification note는 바로 다음 docs micro-slice를 handoff로 고정했지만, 같은 날 same-family docs-only truth-sync가 이미 그 뒤로 더 이어졌으므로 지금 다시 한 줄 handoff를 고정하는 것이 아직 truthful한지도 함께 판단해야 했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/PRODUCT_SPEC.md:270-272`는 `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`에 각각 `original_response_snapshot`, same source-message anchor, `save_signal` 조건을 적고 있습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:112`도 같은 세 memory-signal summary를 same source-message anchor 기준으로 묶어 적고 있습니다.
  - `docs/ARCHITECTURE.md:228-230` 역시 같은 조건을 유지하고 있어 3개 권위 문서 사이에 현재 불일치는 보이지 않았습니다.
- 이 문구는 현재 serializer 조건과 맞습니다.
  - `app/serializers.py:144-160`은 두 시그널을 각각 `_resolve_superseded_reject_signal_for_message`, `_resolve_historical_save_identity_signal_for_message` 경유로만 직렬화합니다.
  - `app/serializers.py:4907-4968`은 둘 다 현재 `session_local_memory_signal`과 normalized source-message anchor를 요구하고, `historical_save_identity_signal`에는 추가로 현재 `save_signal`이 있어야만 task-log replay를 허용합니다.
- 회귀 테스트도 같은 anchored replay semantics를 잠그고 있습니다.
  - `tests/test_web_app.py:6971-7230`, `tests/test_web_app.py:9310-9656`
  - `tests/test_smoke.py:5838-5844`
- 다만 이 verification note가 예전에 고정했던 다음 micro-slice는 지금 그대로 되살리지 않았습니다.
  - 같은 날 후속 same-family `/work`와 `/verify`가 이미 `docs-acceptance-candidate-sibling-join-truth-sync`, `docs-save-content-source-message-id-ownership-truth-sync`까지 이어졌고, 현재 문서도 그 later fixes를 반영하고 있습니다.
  - 4월 9일 same-family docs-only truth-sync가 이미 3회를 훨씬 넘겼으므로, 이 오래된 `/work`에서 또 하나의 docs micro-slice를 직접 handoff로 고정하는 것은 저신뢰 우선순위 판단에 가깝습니다.
- 그래서 `.pipeline/gemini_request.md`에 `CONTROL_SEQ: 278`로 arbitration을 열었습니다. 이번 막힘은 operator-only blocker가 아니라, 이 오래된 docs family를 닫고 다른 exact slice로 넘어갈지 아니면 아직 남은 bounded bundle이 있는지에 대한 next-slice ambiguity입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-superseded-historical-signal-summary-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-superseded-historical-signal-summary-truth-sync-verification.md`
- `ls -1 work/4/9`
- `ls -1 verify/4/9`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '262,276p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '100,114p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '222,232p'`
- `nl -ba app/serializers.py | sed -n '132,188p'`
- `nl -ba app/serializers.py | sed -n '4907,4968p'`
- `rg -n "superseded_reject_signal|historical_save_identity_signal" tests/test_web_app.py tests/test_smoke.py`
- `nl -ba tests/test_web_app.py | sed -n '6968,7238p'`
- `nl -ba tests/test_web_app.py | sed -n '9308,9660p'`
- `nl -ba tests/test_smoke.py | sed -n '5828,5850p'`
- `sed -n '1,220p' work/4/9/2026-04-09-docs-acceptance-candidate-sibling-join-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-acceptance-candidate-sibling-join-truth-sync-verification.md`
- `sed -n '1,220p' work/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-save-content-source-message-id-ownership-truth-sync-verification.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '244,282p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '88,118p'`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `sed -n '1,260p' .pipeline/gemini_request.md`
- `sed -n '1,260p' .pipeline/operator_request.md`
- `git diff --check`

## 남은 리스크
- 이번 라운드는 docs/code/test-source reading과 `git diff --check`까지만 다시 확인했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- 남은 불확실성은 이 `/work`의 truth가 아니라 다음 exact slice 우선순위입니다. 따라서 operator stop이 아니라 Gemini arbitration으로 넘기는 편이 현재 규칙과 더 맞습니다.
