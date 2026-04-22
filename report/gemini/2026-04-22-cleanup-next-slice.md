# 2026-04-22 cleanup next slice advisory

## 개요
CONTROL_SEQ 736에서 수행된 role-based runtime migration의 잔여 항목(REMAINING_RISKS) 처리 방향에 대한 조언입니다.

## 분석
- **현황:** 오늘(2026-04-22) role-neutral 런타임 인프라(implement/verify/advisory)가 성공적으로 구축되었습니다. 인스턴스 이름(Claude, Codex, Gemini)에 의존하던 dispatch 및 label 체계가 역할 기반으로 전환되었습니다.
- **리스크:** 하지만 `watcher_core.py` 내의 legacy config key alias, `.pipeline/` 내의 물리 legacy 파일들이 여전히 존재하여 "이름 드리프트(name drift)"와 관리 혼선이 발생할 수 있는 상태입니다.
- **우선순위:** `GEMINI.md`의 판단 우선순위에 따라 "same-family current-risk reduction"을 1순위로 둡니다. 현재 진행 중인 인프라 개선 가족(family)을 완결 짓는 것이 다음 product milestone(예: Milestone 4 structured correction memory)으로 넘어가기 전의 필수 선결 과제입니다.

## 권고 사항
**RECOMMEND: implement pipeline_runtime_legacy_cleanup_completion**

- **목표:** role-based migration의 마지막 5%를 닫고 리포지토리의 truth를 canonical naming으로 일치시킴.
- **상세 슬라이스 범위:**
    1. **A (Config Key):** `watcher_core.py` 내의 `codex_blocked_triage_prompt`를 `verify_blocked_triage_prompt`로 canonicalize (alias 제거 또는 migration).
    2. **B (Physical Files):** `.pipeline/` 내의 `claude_handoff.md`, `gemini_request.md`, `gemini_advice.md`를 `state-archive/`로 이동하거나 정리하여 canonical `implement_handoff.md` 등이 유일한 control plane이 되도록 함.
    3. **C (Internal State):** `watcher_core.py` 내부의 `_last_claude_handoff_sig`와 같은 vendor-name leak 변수들을 role-based 이름으로 변경.
- **기대 효과:** 인프라의 "역할-기반" 추상화가 filesystem과 code 내부 변수 수준까지 완전해지며, 후속 product 작업에서 어댑터 이름 혼선으로 인한 리스크가 제거됨.

## 결론
Product milestone 복귀 이전에 이 cleanup 슬라이스를 먼저 닫음으로써 인프라 안정화 단계를 확정(finalize)할 것을 권고합니다.
