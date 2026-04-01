"""Eval scenario definitions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class EvalScenario:
    scenario_id: str
    description: str
    eval_mode: str  # "respond" | "answer_with_context"
    input: dict
    preferences: list[dict[str, str]] = field(default_factory=list)
    expected: dict = field(default_factory=dict)


# -- Built-in scenarios --

BUILTIN_SCENARIOS: list[EvalScenario] = [
    # 1. Mock: verify preference plumbing
    EvalScenario(
        scenario_id="mock-preference-plumbing",
        description="Mock 어댑터에서 preference 카운트가 응답에 반영되는지 확인",
        eval_mode="respond",
        input={"user_text": "안녕하세요"},
        preferences=[{"description": "교정 패턴: '문서 비서' → '로컬 퍼스트 문서 비서'", "fingerprint": "sha256:test1"}],
        expected={
            "should_contain": ["선호 1건 반영"],
            "should_not_contain": [],
        },
    ),
    # 2. Mock: no preferences baseline
    EvalScenario(
        scenario_id="mock-no-preference-baseline",
        description="Preference 없이 Mock 응답에 선호 표시가 없는지 확인",
        eval_mode="respond",
        input={"user_text": "안녕하세요"},
        preferences=[],
        expected={
            "should_contain": ["모의 응답"],
            "should_not_contain": ["선호"],
        },
    ),
    # 3. Mock: multiple preferences
    EvalScenario(
        scenario_id="mock-multiple-preferences",
        description="복수 preference가 카운트에 반영되는지 확인",
        eval_mode="respond",
        input={"user_text": "문서 요약해줘"},
        preferences=[
            {"description": "패턴 A", "fingerprint": "sha256:a"},
            {"description": "패턴 B", "fingerprint": "sha256:b"},
            {"description": "패턴 C", "fingerprint": "sha256:c"},
        ],
        expected={
            "should_contain": ["선호 3건 반영"],
            "should_not_contain": [],
        },
    ),
    # 4. Mock: context-grounded with preference
    EvalScenario(
        scenario_id="mock-context-preference",
        description="answer_with_context에서 preference가 전달되는지 확인",
        eval_mode="answer_with_context",
        input={
            "intent": "general",
            "user_request": "이 문서의 핵심이 뭔가요?",
            "context_label": "README.md",
            "source_paths": ["/tmp/README.md"],
            "context_excerpt": "프로젝트H는 로컬 퍼스트 문서 비서입니다.",
        },
        preferences=[{"description": "교정 패턴: 핵심 결론 먼저 배치", "fingerprint": "sha256:ctx1"}],
        expected={
            "should_contain": ["README.md"],
            "should_not_contain": [],
        },
    ),
    # 5. Ollama: terminology adherence (realistic, only meaningful with real model)
    EvalScenario(
        scenario_id="ollama-terminology-adherence",
        description="Ollama에서 '로컬 퍼스트' 용어가 preference에 의해 반영되는지 확인",
        eval_mode="respond",
        input={"user_text": "projectH가 뭔지 한 줄로 설명해줘"},
        preferences=[{"description": "교정 패턴: '문서 비서' → '로컬 퍼스트 문서 비서'", "fingerprint": "sha256:term1"}],
        expected={
            "should_contain": [],
            "should_not_contain": [],
            "expected_pattern": r"로컬|local",
        },
    ),
    # 6. Ollama: no preference baseline for A/B comparison
    EvalScenario(
        scenario_id="ollama-no-preference-baseline",
        description="Preference 없이 Ollama 기본 응답 확인 (A/B 비교용)",
        eval_mode="respond",
        input={"user_text": "projectH가 뭔지 한 줄로 설명해줘"},
        preferences=[],
        expected={
            "should_contain": [],
            "should_not_contain": [],
        },
    ),
]
