"""Eval scenario definitions.

Categories:
  doc_summary      — single document summarization
  doc_followup     — single document follow-up Q&A
  doc_compare      — multi-document comparison
  web_latest       — freshness-sensitive web query
  web_entity       — entity card web investigation
  web_conflict     — conflicting sources resolution
  correction       — correction-applied response
  preference       — preference-applied response
  uncertainty      — should say "모른다" / hedging required
  routing          — verify correct model tier assignment
  format           — short rewrite / formatting task
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class EvalScenario:
    scenario_id: str
    description: str
    eval_mode: str  # "respond" | "answer_with_context" | "summarize" | "routing"
    input: dict
    preferences: list[dict[str, str]] = field(default_factory=list)
    expected: dict = field(default_factory=dict)
    category: str = "general"           # doc_summary, web_entity, uncertainty, etc.
    expected_tier: str = ""             # "light" | "medium" | "heavy" | "" (any)
    tags: tuple[str, ...] = ()         # for filtering: ("mock", "ollama", "release-gate")


# ── Mock adapter scenarios (plumbing verification) ────────────────

MOCK_SCENARIOS: list[EvalScenario] = [
    EvalScenario(
        scenario_id="mock-preference-plumbing",
        description="Mock 어댑터에서 preference 카운트가 응답에 반영되는지 확인",
        eval_mode="respond",
        category="preference",
        input={"user_text": "안녕하세요"},
        preferences=[{"description": "교정 패턴: '문서 비서' → '로컬 퍼스트 문서 비서'", "fingerprint": "sha256:test1"}],
        expected={"should_contain": ["선호 1건 반영"]},
        tags=("mock",),
    ),
    EvalScenario(
        scenario_id="mock-no-preference-baseline",
        description="Preference 없이 Mock 응답에 선호 표시가 없는지 확인",
        eval_mode="respond",
        category="preference",
        input={"user_text": "안녕하세요"},
        preferences=[],
        expected={"should_contain": ["모의 응답"], "should_not_contain": ["선호"]},
        tags=("mock",),
    ),
    EvalScenario(
        scenario_id="mock-multiple-preferences",
        description="복수 preference가 카운트에 반영되는지 확인",
        eval_mode="respond",
        category="preference",
        input={"user_text": "문서 요약해줘"},
        preferences=[
            {"description": "패턴 A", "fingerprint": "sha256:a"},
            {"description": "패턴 B", "fingerprint": "sha256:b"},
            {"description": "패턴 C", "fingerprint": "sha256:c"},
        ],
        expected={"should_contain": ["선호 3건 반영"]},
        tags=("mock",),
    ),
    EvalScenario(
        scenario_id="mock-context-preference",
        description="answer_with_context에서 preference가 전달되는지 확인",
        eval_mode="answer_with_context",
        category="preference",
        input={
            "intent": "general",
            "user_request": "이 문서의 핵심이 뭔가요?",
            "context_label": "README.md",
            "source_paths": ["/tmp/README.md"],
            "context_excerpt": "프로젝트H는 로컬 퍼스트 문서 비서입니다.",
        },
        preferences=[{"description": "교정 패턴: 핵심 결론 먼저 배치", "fingerprint": "sha256:ctx1"}],
        expected={"should_contain": ["README.md"]},
        tags=("mock",),
    ),
]

# ── Document scenarios ────────────────────────────────────────────

DOC_SCENARIOS: list[EvalScenario] = [
    # Doc summary
    EvalScenario(
        scenario_id="doc-summary-basic",
        description="단일 문서 요약 — 핵심 내용이 포함되는지",
        eval_mode="answer_with_context",
        category="doc_summary",
        expected_tier="medium",
        input={
            "intent": "general",
            "user_request": "이 문서를 요약해주세요",
            "context_label": "project-brief.md",
            "source_paths": ["/tmp/project-brief.md"],
            "context_excerpt": (
                "# 프로젝트 개요\n"
                "본 프로젝트는 로컬 파일 기반 문서 어시스턴트를 목표로 합니다.\n"
                "핵심 원칙: 로컬 퍼스트, 승인 기반 안전, 근거 투명성.\n"
                "현재 단계: MVP 기능 완성, 구조 리팩터링 완료."
            ),
        },
        expected={
            "should_contain": [],
            "expected_pattern": r"로컬|문서|어시스턴트",
        },
        tags=("ollama", "release-gate"),
    ),
    # Doc follow-up: key_points
    EvalScenario(
        scenario_id="doc-followup-keypoints",
        description="핵심 포인트 추출 — 3개 bullet point",
        eval_mode="answer_with_context",
        category="doc_followup",
        expected_tier="medium",
        input={
            "intent": "key_points",
            "user_request": "핵심 3줄로 정리해주세요",
            "context_label": "spec.md",
            "source_paths": ["/tmp/spec.md"],
            "context_excerpt": (
                "## 핵심 목표\n"
                "- 로컬 파일 기반 생산성 도구를 안전하게 제공한다.\n"
                "- 향후 독자 모델로 확장 가능한 구조를 선행 확보한다.\n"
                "- 상업화 시 브랜드 리스크를 줄인다.\n"
                "## 제약\n"
                "- 외부 네트워크 접근은 승인 필요\n"
                "- 쓰기 작업은 사용자 승인 게이트"
            ),
        },
        expected={
            "expected_pattern": r"[-•].*[-•].*[-•]",
            "should_not_contain": ["확인되지 않습니다"],
        },
        tags=("ollama", "release-gate"),
    ),
    # Doc follow-up: action_items
    EvalScenario(
        scenario_id="doc-followup-actions",
        description="실행 항목 추출 — 번호 목록",
        eval_mode="answer_with_context",
        category="doc_followup",
        expected_tier="medium",
        input={
            "intent": "action_items",
            "user_request": "실행할 일만 뽑아주세요",
            "context_label": "plan.md",
            "source_paths": ["/tmp/plan.md"],
            "context_excerpt": (
                "## 다음 단계\n"
                "1. eval 시나리오를 30개로 확대한다.\n"
                "2. 모델 라우팅 품질을 검증한다.\n"
                "3. preference 루프를 완성한다."
            ),
        },
        expected={
            "expected_pattern": r"1\.",
            "should_not_contain": ["확인되지 않습니다"],
        },
        tags=("ollama", "release-gate"),
    ),
    # Doc follow-up: memo
    EvalScenario(
        scenario_id="doc-followup-memo",
        description="메모 형식 — 제목/핵심/다음 행동",
        eval_mode="answer_with_context",
        category="doc_followup",
        expected_tier="medium",
        input={
            "intent": "memo",
            "user_request": "메모 형식으로 써주세요",
            "context_label": "meeting.md",
            "source_paths": ["/tmp/meeting.md"],
            "context_excerpt": (
                "회의 결과: eval 하니스 확대를 1순위로 합의.\n"
                "참석: 개발팀 전원.\n"
                "다음 행동: 시나리오 설계 후 PR 리뷰."
            ),
        },
        expected={
            "should_contain": ["제목:", "핵심:", "다음 행동:"],
        },
        tags=("ollama", "release-gate"),
    ),
    # Doc: evidence-grounded answer
    EvalScenario(
        scenario_id="doc-grounded-answer",
        description="근거 기반 답변 — 근거에 있는 사실만 사용",
        eval_mode="answer_with_context",
        category="doc_followup",
        expected_tier="medium",
        input={
            "intent": "general",
            "user_request": "이 프로젝트의 개발 언어가 뭔가요?",
            "context_label": "readme.md",
            "source_paths": ["/tmp/readme.md"],
            "context_excerpt": "프로젝트는 Python 3.11 이상에서 동작합니다. Flask 기반 웹 서버.",
            "evidence_items": [
                {"source_name": "readme.md", "label": "기술 스택", "snippet": "Python 3.11, Flask"},
            ],
        },
        expected={
            "expected_pattern": r"[Pp]ython|파이썬",
            "should_not_contain": ["Java", "TypeScript"],
        },
        tags=("ollama", "release-gate"),
    ),
]

# ── Uncertainty scenarios (should hedge or say "모른다") ──────────

UNCERTAINTY_SCENARIOS: list[EvalScenario] = [
    EvalScenario(
        scenario_id="uncertainty-no-evidence",
        description="근거 없을 때 확인 불가 표시",
        eval_mode="answer_with_context",
        category="uncertainty",
        expected_tier="medium",
        input={
            "intent": "general",
            "user_request": "이 회사의 2025년 매출이 얼마인가요?",
            "context_label": "company.md",
            "source_paths": ["/tmp/company.md"],
            "context_excerpt": "주식회사 ABC는 2020년 설립된 스타트업입니다.",
        },
        expected={
            "expected_pattern": r"확인|없|모르|불가|부족",
            "should_not_contain": ["매출은 100"],
        },
        tags=("ollama", "release-gate"),
    ),
    EvalScenario(
        scenario_id="uncertainty-personal-experience",
        description="직접 경험 질문에 시스템 한계 표시",
        eval_mode="respond",
        category="uncertainty",
        input={"user_text": "너도 원피스 본 적 있어?"},
        expected={
            "expected_pattern": r"경험|직접|수 없|아닙니다|AI",
            "should_not_contain": ["네, 봤습니다", "재밌었어요"],
        },
        tags=("ollama", "release-gate"),
    ),
    EvalScenario(
        scenario_id="uncertainty-unverifiable-claim",
        description="검증 불가능한 외부 사실에 유보적 표현 사용",
        eval_mode="respond",
        category="uncertainty",
        input={"user_text": "김철수라는 유튜버에 대해 알려줘"},
        expected={
            "expected_pattern": r"확인|찾지 못|로컬|문서|출처",
            "should_not_contain": ["김철수는 유명한"],
        },
        tags=("ollama", "release-gate"),
    ),
]

# ── Preference scenarios (with real model) ────────────────────────

PREFERENCE_SCENARIOS: list[EvalScenario] = [
    EvalScenario(
        scenario_id="pref-terminology-adherence",
        description="용어 교정 선호가 실제 반영되는지",
        eval_mode="respond",
        category="preference",
        input={"user_text": "projectH가 뭔지 한 줄로 설명해줘"},
        preferences=[{"description": "교정 패턴: '문서 비서' → '로컬 퍼스트 문서 비서'", "fingerprint": "sha256:term1"}],
        expected={"expected_pattern": r"로컬|local"},
        tags=("ollama", "release-gate"),
    ),
    EvalScenario(
        scenario_id="pref-no-preference-baseline",
        description="Preference 없이 기본 응답 (A/B 비교용)",
        eval_mode="respond",
        category="preference",
        input={"user_text": "projectH가 뭔지 한 줄로 설명해줘"},
        preferences=[],
        expected={},
        tags=("ollama",),
    ),
    EvalScenario(
        scenario_id="pref-style-honorific",
        description="존댓말 스타일 선호 반영",
        eval_mode="respond",
        category="preference",
        input={"user_text": "인사해줘"},
        preferences=[{"description": "모든 응답을 '~입니다/~합니다' 존댓말로 쓰세요", "fingerprint": "sha256:honor1"}],
        expected={"expected_pattern": r"입니다|합니다|습니다"},
        tags=("ollama", "release-gate"),
    ),
    EvalScenario(
        scenario_id="pref-context-conclusion-first",
        description="결론 먼저 배치 선호가 문서 답변에 반영되는지",
        eval_mode="answer_with_context",
        category="preference",
        input={
            "intent": "general",
            "user_request": "이 문서의 결론이 뭔가요?",
            "context_label": "report.md",
            "source_paths": ["/tmp/report.md"],
            "context_excerpt": (
                "분석 배경: 시장 변화 심화.\n"
                "방법론: 정량+정성 혼합.\n"
                "결론: 로컬 퍼스트 전략이 가장 유리하다."
            ),
        },
        preferences=[{"description": "결론을 응답 첫 문장에 배치", "fingerprint": "sha256:concl1"}],
        expected={"expected_pattern": r"^.*로컬|^.*유리"},
        tags=("ollama", "release-gate"),
    ),
]

# ── Routing verification scenarios ────────────────────────────────

ROUTING_SCENARIOS: list[EvalScenario] = [
    EvalScenario(
        scenario_id="route-rewrite-to-light",
        description="리라이트 작업은 light (3B) 티어로 라우팅",
        eval_mode="routing",
        category="routing",
        expected_tier="light",
        input={"task": "rewrite"},
        tags=("mock", "release-gate"),
    ),
    EvalScenario(
        scenario_id="route-respond-to-medium",
        description="일반 채팅은 medium (7B) 티어로 라우팅",
        eval_mode="routing",
        category="routing",
        expected_tier="medium",
        input={"task": "respond"},
        tags=("mock", "release-gate"),
    ),
    EvalScenario(
        scenario_id="route-summarize-to-medium",
        description="문서 요약은 medium (7B) 티어로 라우팅",
        eval_mode="routing",
        category="routing",
        expected_tier="medium",
        input={"task": "summarize"},
        tags=("mock", "release-gate"),
    ),
    EvalScenario(
        scenario_id="route-web-entity-to-heavy",
        description="웹 엔티티 카드는 heavy (14B) 티어로 라우팅",
        eval_mode="routing",
        category="routing",
        expected_tier="heavy",
        input={"task": "answer_context", "answer_mode": "entity_card", "has_web_sources": True, "source_count": 3},
        tags=("mock", "release-gate"),
    ),
    EvalScenario(
        scenario_id="route-freshness-to-heavy",
        description="최신성 민감 질의는 heavy (14B) 티어로 라우팅",
        eval_mode="routing",
        category="routing",
        expected_tier="heavy",
        input={"task": "answer_context", "freshness_sensitive": True},
        tags=("mock", "release-gate"),
    ),
    EvalScenario(
        scenario_id="route-conflicting-to-heavy",
        description="상충 출처는 heavy (14B) 티어로 라우팅",
        eval_mode="routing",
        category="routing",
        expected_tier="heavy",
        input={"task": "answer_context", "has_conflicting_sources": True},
        tags=("mock", "release-gate"),
    ),
    EvalScenario(
        scenario_id="route-save-candidate-to-heavy",
        description="저장 후보 답변은 heavy (14B) 티어로 라우팅",
        eval_mode="routing",
        category="routing",
        expected_tier="heavy",
        input={"task": "answer_context", "is_save_candidate": True},
        tags=("mock", "release-gate"),
    ),
    EvalScenario(
        scenario_id="route-format-to-light",
        description="형식 맞추기는 light (3B) 티어로 라우팅",
        eval_mode="routing",
        category="routing",
        expected_tier="light",
        input={"task": "format"},
        tags=("mock", "release-gate"),
    ),
]

# ── Format / rewrite scenarios ────────────────────────────────────

FORMAT_SCENARIOS: list[EvalScenario] = [
    EvalScenario(
        scenario_id="format-korean-rewrite",
        description="한국어 리라이트 — 간결한 한국어로 변환",
        eval_mode="respond",
        category="format",
        expected_tier="light",
        input={"user_text": "다음을 한국어로 간결하게 다시 써줘: The project is a local-first document assistant."},
        expected={"expected_pattern": r"[가-힣]"},
        tags=("ollama",),
    ),
]

# ── Aggregate all scenarios ───────────────────────────────────────

BUILTIN_SCENARIOS: list[EvalScenario] = [
    *MOCK_SCENARIOS,
    *DOC_SCENARIOS,
    *UNCERTAINTY_SCENARIOS,
    *PREFERENCE_SCENARIOS,
    *ROUTING_SCENARIOS,
    *FORMAT_SCENARIOS,
]

# Category → scenario count for reference
CATEGORY_COUNTS = {}
for _s in BUILTIN_SCENARIOS:
    CATEGORY_COUNTS[_s.category] = CATEGORY_COUNTS.get(_s.category, 0) + 1
