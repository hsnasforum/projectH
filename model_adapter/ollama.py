from __future__ import annotations

import json
from pathlib import Path
import re
import socket
from typing import Any
from urllib.parse import urlparse
from urllib import error, request

from model_adapter.base import (
    FOLLOW_UP_INTENT_ACTION_ITEMS,
    FOLLOW_UP_INTENT_GENERAL,
    FOLLOW_UP_INTENT_KEY_POINTS,
    FOLLOW_UP_INTENT_MEMO,
    ModelAdapter,
    ModelAdapterError,
    ModelStreamEvent,
    ModelRuntimeStatus,
    SummaryNoteDraft,
)


class OllamaModelAdapter(ModelAdapter):
    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        timeout_seconds: float = 180.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._active_model: str | None = None  # per-call override

    # Models at or below this parameter threshold get simplified Korean-first prompts.
    _COMPACT_MODEL_PATTERNS = re.compile(
        r"(?i)(?::(\d+(?:\.\d+)?)b)|(?:(\d+(?:\.\d+)?)b[-_])",
    )

    @property
    def _effective_model(self) -> str:
        return self._active_model or self.model

    def _is_compact(self, model_name: str | None = None) -> bool:
        """Return True for models ≤ 14B where Korean-first prompts help."""
        name = model_name or self._effective_model
        m = self._COMPACT_MODEL_PATTERNS.search(name)
        if m:
            size = float(m.group(1) or m.group(2))
            return size <= 14
        return True

    @property
    def _is_compact_model(self) -> bool:
        return self._is_compact()

    def use_model(self, model_name: str) -> "_ModelOverrideContext":
        """Context manager to temporarily override the model for a call."""
        return _ModelOverrideContext(self, model_name)

    @staticmethod
    def _format_preference_block(active_preferences: list[dict[str, str]] | None, *, korean: bool = False) -> str:
        if not active_preferences:
            return ""
        if korean:
            lines = ["\n\n[사용자 선호]\n다음 사항을 응답에 반영하세요:"]
        else:
            lines = ["\n\nUser correction preferences (apply these consistently to all responses):"]
        for pref in active_preferences[:10]:
            desc = pref.get("description", "").strip()
            if desc:
                lines.append(f"- {desc}")
        return "\n".join(lines) if len(lines) > 1 else ""

    # ── Compact (≤7B) Korean-first system prompts ──────────────────
    _COMPACT_SYSTEM_RESPOND = (
        "당신은 로컬 문서 어시스턴트입니다. 한국어로 답하세요.\n"
        "규칙:\n"
        "- 간결하고 정확하게 답하세요.\n"
        "- 확인할 수 없는 사실은 추측하지 말고 '확인할 수 없습니다'라고 하세요.\n"
        "- 직접 경험한 것처럼 말하지 마세요."
    )

    _FULL_SYSTEM_RESPOND = (
        "You are a local-first AI assistant. Answer in Korean by default unless the user explicitly requests another language. "
        "Use Korean Hangul for explanatory text. Do not answer in Chinese or Japanese unless the user explicitly asks for those languages. "
        "Keep answers concise, grounded, and safe for file-based productivity workflows. "
        "If the user asks about a real-world person, channel, brand, product, company, or other external fact without giving a supporting source, "
        "do not guess. State that you cannot verify it from the current local context and ask for a local document or source text. "
        "Never claim personal experiences such as having watched, read, visited, used, or tried something yourself."
    )

    def respond(self, prompt: str, *, active_preferences: list[dict[str, str]] | None = None) -> str:
        compact = self._is_compact_model
        pref_block = self._format_preference_block(active_preferences, korean=compact)
        system = (self._COMPACT_SYSTEM_RESPOND if compact else self._FULL_SYSTEM_RESPOND) + pref_block
        return self._generate(
            prompt=prompt,
            system=system,
            enforce_korean=True,
            korean_rewrite_instruction=(
                "한국어 한 문단으로 간결하게 다시 쓰세요." if compact else
                "Return one short Korean paragraph using Hangul for explanatory text. "
                "Do not use Chinese or Japanese. If the claim is not verified, say that you cannot confirm it."
            ),
        )

    def stream_respond(self, prompt: str, *, active_preferences: list[dict[str, str]] | None = None):
        compact = self._is_compact_model
        pref_block = self._format_preference_block(active_preferences, korean=compact)
        system = (self._COMPACT_SYSTEM_RESPOND if compact else self._FULL_SYSTEM_RESPOND) + pref_block
        yield from self._stream_generate(
            prompt=prompt,
            system=system,
            enforce_korean=True,
            korean_rewrite_instruction=(
                "한국어 한 문단으로 간결하게 다시 쓰세요." if compact else
                "Return one short Korean paragraph using Hangul for explanatory text. "
                "Do not use Chinese or Japanese. If the claim is not verified, say that you cannot confirm it."
            ),
        )

    _COMPACT_SYSTEM_SUMMARIZE = (
        "주어진 문서를 한국어로 요약하세요.\n"
        "규칙:\n"
        "- 문서에 실제로 적힌 내용만 요약하세요.\n"
        "- 이야기글이면 인물, 사건, 결말 순서로 쓰세요.\n"
        "- 정보글이면 주제, 핵심 내용, 결론 순서로 쓰세요.\n"
        "- 제목이나 머리말 없이 본문만 쓰세요.\n"
        "- 고유명사와 파일명은 그대로 유지하세요."
    )

    _FULL_SYSTEM_SUMMARIZE = (
        "Summarize the provided document for a solo user in Korean. "
        "Use Korean Hangul for explanatory text. Do not answer in Chinese or Japanese. "
        "Prioritize what the document actually says or what happens over memorable wording. "
        "If the text is narrative or fiction, summarize major characters or actors, key events, conflict changes, and the ending state in order. "
        "If the text is informational or argumentative, summarize the topic, main points, decisions or actions, and conclusion. "
        "If the prompt explicitly says 'Summary source type: search_results', treat it as a synthesis of selected search results and prioritize shared facts, meaningful differences, key actions or decisions, and the grounded conclusion. "
        "If the prompt explicitly says 'Summary source type: local_document', preserve the document flow guidance above without inventing a separate mode. "
        "Return only a concise Korean summary in plain text with no preamble, heading, or bullet label. "
        "Keep file names and proper nouns as they are when needed."
    )

    def summarize(self, text: str) -> str:
        compact = self._is_compact_model
        return self._generate(
            prompt=text,
            system=self._COMPACT_SYSTEM_SUMMARIZE if compact else self._FULL_SYSTEM_SUMMARIZE,
            enforce_korean=True,
            korean_rewrite_instruction=(
                "자연스러운 한국어로 간결하게 다시 쓰세요. 마크다운 제목 제거." if compact else
                "Rewrite the text into concise natural Korean using Hangul for explanatory text only. "
                "Preserve the actual flow of events or arguments instead of isolated memorable sentences. "
                "Do not use Chinese or Japanese. Remove markdown headings and return plain text only."
            ),
        )

    def stream_summarize(self, text: str):
        compact = self._is_compact_model
        yield from self._stream_generate(
            prompt=text,
            system=self._COMPACT_SYSTEM_SUMMARIZE if compact else self._FULL_SYSTEM_SUMMARIZE,
            enforce_korean=True,
            korean_rewrite_instruction=(
                "자연스러운 한국어로 간결하게 다시 쓰세요. 마크다운 제목 제거." if compact else
                "Rewrite the text into concise natural Korean using Hangul for explanatory text only. "
                "Preserve the actual flow of events or arguments instead of isolated memorable sentences. "
                "Do not use Chinese or Japanese. Remove markdown headings and return plain text only."
            ),
        )

    def create_summary_note(self, *, source_path: str, text: str) -> SummaryNoteDraft:
        summary = self.summarize(text)
        source_name = Path(source_path).name
        title = f"{source_name} 요약"
        note_body = "\n".join(
            [
                f"# {title}",
                "",
                f"원본 파일: {source_path}",
                "",
                "## 요약",
                summary,
            ]
        )
        return SummaryNoteDraft(title=title, summary=summary, note_body=note_body)

    def answer_with_context(
        self,
        *,
        intent: str,
        user_request: str,
        context_label: str,
        source_paths: list[str],
        context_excerpt: str,
        summary_hint: str | None = None,
        evidence_items: list[dict[str, str]] | None = None,
        active_preferences: list[dict[str, str]] | None = None,
    ) -> str:
        compact = self._is_compact_model
        if compact:
            prompt, context_cues = self._build_compact_context_prompt(
                intent=intent,
                user_request=user_request,
                context_label=context_label,
                source_paths=source_paths,
                context_excerpt=context_excerpt,
                summary_hint=summary_hint,
                evidence_items=evidence_items,
            )
            pref_block = self._format_preference_block(active_preferences, korean=True)
            system = self._compact_intent_system_prompt(intent) + pref_block
            rewrite = self._compact_intent_output_contract(intent)
        else:
            prompt, context_cues = self._build_context_prompt(
                intent=intent,
                user_request=user_request,
                context_label=context_label,
                source_paths=source_paths,
                context_excerpt=context_excerpt,
                summary_hint=summary_hint,
                evidence_items=evidence_items,
            )
            pref_block = self._format_preference_block(active_preferences)
            system = self._intent_system_prompt(intent) + pref_block
            rewrite = self._intent_output_contract(intent)
        raw_answer = self._generate(
            prompt=prompt,
            system=system,
            enforce_korean=True,
            korean_rewrite_instruction=rewrite,
        )
        return self._postprocess_answer(
            intent=intent,
            raw_answer=raw_answer,
            context_label=context_label,
            context_cues=context_cues,
        )

    def stream_answer_with_context(
        self,
        *,
        intent: str,
        user_request: str,
        context_label: str,
        source_paths: list[str],
        context_excerpt: str,
        summary_hint: str | None = None,
        evidence_items: list[dict[str, str]] | None = None,
        active_preferences: list[dict[str, str]] | None = None,
    ):
        compact = self._is_compact_model
        if compact:
            prompt, context_cues = self._build_compact_context_prompt(
                intent=intent,
                user_request=user_request,
                context_label=context_label,
                source_paths=source_paths,
                context_excerpt=context_excerpt,
                summary_hint=summary_hint,
                evidence_items=evidence_items,
            )
            pref_block = self._format_preference_block(active_preferences, korean=True)
            system = self._compact_intent_system_prompt(intent) + pref_block
            rewrite = self._compact_intent_output_contract(intent)
        else:
            prompt, context_cues = self._build_context_prompt(
                intent=intent,
                user_request=user_request,
                context_label=context_label,
                source_paths=source_paths,
                context_excerpt=context_excerpt,
                summary_hint=summary_hint,
                evidence_items=evidence_items,
            )
            pref_block = self._format_preference_block(active_preferences)
            system = self._intent_system_prompt(intent) + pref_block
            rewrite = self._intent_output_contract(intent)
        raw_answer = ""
        for event in self._stream_generate(
            prompt=prompt,
            system=system,
            enforce_korean=True,
            korean_rewrite_instruction=rewrite,
        ):
            raw_answer = self._apply_stream_event(raw_answer, event)
            yield event
        final_answer = self._postprocess_answer(
            intent=intent,
            raw_answer=raw_answer,
            context_label=context_label,
            context_cues=context_cues,
        )
        if final_answer != raw_answer:
            yield ModelStreamEvent(kind="text_replace", text=final_answer)

    def _intent_system_prompt(self, intent: str) -> str:
        common = (
            "You are a local-first AI assistant continuing a conversation about already selected local files. "
            "Answer only from the supplied bounded evidence and supporting excerpts, stay concise, and mention the relevant source name when it helps. "
            "The bounded evidence lines are the highest-priority facts. Do not use background knowledge or guess beyond them. "
            "If the answer is not directly supported by the provided evidence, explicitly say '제공된 근거만으로는 확인되지 않습니다.' in Korean. "
            "Do not invent facts, tasks, conclusions, timelines, entities, or causes that are not grounded in the provided document. "
            "Use Korean Hangul for explanatory text. Do not answer in Chinese or Japanese unless explicitly requested."
        )
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return (
                common
                + " Return exactly three bullet points in Korean. Each bullet must capture a distinct key point. "
                + "Prioritize purpose, principles, decisions, and conclusions. "
                + "Use the preferred evidence lines first when they are available. "
                + "Do not add preamble, conclusion, or source path-only bullets."
            )
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return (
                common
                + " Return only actionable next steps in Korean as a numbered list. "
                + "If the context does not clearly support an action, say that explicitly. "
                + "Do not invent work that is not grounded in the supplied text. "
                + "Use candidate action lines first, then decision-needed statements. "
                + "Never treat title, version, date, file path, or other metadata as an action item."
            )
        if intent == FOLLOW_UP_INTENT_MEMO:
            return (
                common
                + " Rewrite the answer in Korean memo format using this structure exactly: "
                + "'제목:', '핵심:', '다음 행동:'. Use the preferred evidence lines first. "
                + "Keep each section concise and grounded in the supplied text."
            )
        return common + " Answer in Korean with a short helpful paragraph."

    def _intent_prompt_suffix(self, intent: str) -> str:
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return (
                "Task: Extract exactly three key lines from the current document context. "
                "Prioritize major goals, principles, decisions, and final recommendations over metadata."
            )
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return (
                "Task: Extract concrete action items only. "
                "Prefer imperative or decision-needed items from the document. "
                "If the document mainly contains description, recommendations, or deferred work, convert only those grounded items into concise next steps. "
                "Never promote title/version/date metadata into action items."
            )
        if intent == FOLLOW_UP_INTENT_MEMO:
            return (
                "Task: Rewrite the context as a concise memo. "
                "Preserve the most important facts and proposed next steps."
            )
        return "Task: Answer the follow-up question based on the current document context."

    def _intent_output_contract(self, intent: str) -> str:
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return "Exactly 3 bullet points. No heading. No numbering. No metadata-only bullets."
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return (
                "Only a numbered list. 1 to 5 items maximum. "
                "Each item must be a concrete next action or decision. "
                "If no grounded action exists, return exactly: 1. 문서에 바로 실행할 일은 명확히 나오지 않습니다."
            )
        if intent == FOLLOW_UP_INTENT_MEMO:
            return "Use exactly these sections in Korean: 제목:, 핵심:, 다음 행동:."
        return "One short Korean paragraph answering the follow-up request."

    def _intent_reasoning_guardrails(self, intent: str) -> str:
        common = "Ignore file metadata such as title, version, author, date, and path unless the user explicitly asks about metadata."
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return (
                common
                + " Prefer recommendation sections, TODO-like bullets, next-step sections, "
                + "and decision-needed statements. Reject document metadata even if it appears near action sections."
            )
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return common + " Prefer the document's purpose, constraints, principles, and conclusions."
        if intent == FOLLOW_UP_INTENT_MEMO:
            return common + " Preserve the most decision-relevant facts and action-relevant lines."
        return common

    # ── Compact (≤7B) Korean-first context methods ────────────────

    def _compact_intent_system_prompt(self, intent: str) -> str:
        base = (
            "당신은 로컬 문서 어시스턴트입니다.\n"
            "규칙:\n"
            "- 아래 제공된 근거와 문서 발췌만 사용하세요.\n"
            "- 근거에 없는 내용은 '제공된 근거만으로는 확인되지 않습니다'라고 하세요.\n"
            "- 사실, 일정, 원인을 지어내지 마세요.\n"
            "- 한국어로 답하세요."
        )
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return base + "\n- 핵심 포인트 3개를 글머리 기호로 쓰세요.\n- 목적, 원칙, 결정, 결론 위주로 쓰세요."
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return base + "\n- 실행 가능한 항목만 번호 목록으로 쓰세요 (최대 5개).\n- 실행할 일이 없으면 '문서에 바로 실행할 일은 없습니다'라고 쓰세요."
        if intent == FOLLOW_UP_INTENT_MEMO:
            return base + "\n- 메모 형식으로 쓰세요: 제목:, 핵심:, 다음 행동:"
        return base + "\n- 짧은 한 문단으로 답하세요."

    def _compact_intent_output_contract(self, intent: str) -> str:
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return "핵심 3개를 글머리 기호로. 제목 없이."
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return "번호 목록. 최대 5개. 실행 가능한 것만."
        if intent == FOLLOW_UP_INTENT_MEMO:
            return "제목:, 핵심:, 다음 행동: 형식."
        return "한국어 한 문단."

    def _build_compact_context_prompt(
        self,
        *,
        intent: str,
        user_request: str,
        context_label: str,
        source_paths: list[str],
        context_excerpt: str,
        summary_hint: str | None = None,
        evidence_items: list[dict[str, str]] | None = None,
    ) -> tuple[str, dict[str, list[str]]]:
        """Simplified prompt for small models: evidence first, minimal meta."""
        context_cues = self._extract_context_cues(context_excerpt)
        sections: list[str] = []

        # 1. Document excerpt FIRST (most important for grounding)
        sections.append("=== 문서 내용 ===")
        sections.append(context_excerpt[:4000])

        # 2. Bounded evidence (merged, not split into categories)
        evidence_lines = self._format_evidence_items(evidence_items)
        if evidence_lines:
            sections.append("")
            sections.append("=== 핵심 근거 ===")
            for line in evidence_lines:
                sections.append(line)

        # 3. Summary hint if present
        if summary_hint:
            sections.append("")
            sections.append(f"=== 요약 ===\n{summary_hint}")

        # 4. Source info (compact)
        if source_paths:
            sources = ", ".join(Path(p).name for p in source_paths[:3])
            sections.append(f"\n출처: {sources}")

        # 5. User question LAST (closest to where model generates)
        sections.append("")
        sections.append(f"=== 질문 ===\n{user_request}")

        return "\n".join(sections), context_cues

    # ── Full (>7B) context methods (unchanged) ────────────────────

    def _build_context_prompt(
        self,
        *,
        intent: str,
        user_request: str,
        context_label: str,
        source_paths: list[str],
        context_excerpt: str,
        summary_hint: str | None = None,
        evidence_items: list[dict[str, str]] | None = None,
    ) -> tuple[str, dict[str, list[str]]]:
        sources = "\n".join(f"- {path}" for path in source_paths) or "- (출처 없음)"
        context_cues = self._extract_context_cues(context_excerpt)
        focus_lines = self._intent_focus_lines(intent, context_cues)
        prompt_sections = [
            f"Intent: {intent}",
            f"Context label: {context_label}",
            "Source paths:",
            sources,
            "",
            "Output contract:",
            self._intent_output_contract(intent),
            "",
            "Reasoning guardrails:",
            self._intent_reasoning_guardrails(intent),
            "",
            "Evidence policy:",
            "- Use only the bounded evidence lines and directly supporting excerpts below.",
            "- If a detail is not supported, say '제공된 근거만으로는 확인되지 않습니다.' in Korean.",
            "- Do not fill gaps with background knowledge, genre assumptions, or likely facts.",
            "",
            "Intent focus:",
            self._intent_focus_instruction(intent),
        ]
        prompt_sections.extend(
            [
                "",
                *self._prompt_list_block(
                    "Bounded evidence lines (highest priority):",
                    self._format_evidence_items(evidence_items),
                    "No bounded evidence lines were selected.",
                ),
            ]
        )
        prompt_sections.extend(
            ["", *self._prompt_list_block("Preferred evidence lines:", focus_lines, "No preferred evidence lines extracted.")]
        )
        prompt_sections.extend(
            [
                "",
                *self._prompt_list_block(
                    "High-signal lines:",
                    context_cues["high_signal_lines"],
                    "No structured high-signal lines extracted.",
                ),
            ]
        )
        prompt_sections.extend(
            [
                "",
                *self._prompt_list_block(
                    "Candidate action lines:",
                    context_cues["action_lines"],
                    "No action-oriented lines extracted.",
                ),
            ]
        )
        prompt_sections.extend(
            [
                "",
                *self._prompt_list_block(
                    "Decision or policy lines:",
                    context_cues["decision_lines"],
                    "No explicit decision or policy lines extracted.",
                ),
            ]
        )
        prompt_sections.extend(
            [
                "",
                *self._prompt_list_block(
                    "Metadata-only lines to ignore unless explicitly asked:",
                    context_cues["metadata_lines"],
                    "No metadata-only lines extracted.",
                ),
            ]
        )
        if summary_hint:
            prompt_sections.extend(["", "Context summary:", summary_hint])
        prompt_sections.extend(
            [
                "",
                "Document excerpts:",
                context_excerpt[:5000],
                "",
                f"User request: {user_request}",
                "",
                self._intent_prompt_suffix(intent),
            ]
        )
        return "\n".join(prompt_sections), context_cues

    def _postprocess_answer(
        self,
        *,
        intent: str,
        raw_answer: str,
        context_label: str,
        context_cues: dict[str, list[str]],
    ) -> str:
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return self._postprocess_key_points(raw_answer=raw_answer, context_cues=context_cues)
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return self._postprocess_action_items(raw_answer=raw_answer, context_cues=context_cues)
        if intent == FOLLOW_UP_INTENT_MEMO:
            return self._postprocess_memo(
                raw_answer=raw_answer,
                context_label=context_label,
                context_cues=context_cues,
            )
        return raw_answer.strip()

    def _postprocess_key_points(self, *, raw_answer: str, context_cues: dict[str, list[str]]) -> str:
        candidate_lines = self._extract_list_like_lines(raw_answer)
        key_lines = [
            line
            for line in candidate_lines
            if not self._looks_like_metadata(line)
        ]
        if len(key_lines) < 3:
            fallback_lines = self._dedupe_lines(
                key_lines
                + context_cues["purpose_lines"]
                + context_cues["decision_lines"]
                + context_cues["high_signal_lines"]
            )
            key_lines = [line for line in fallback_lines if not self._looks_like_metadata(line)]

        if not key_lines:
            key_lines = ["문서의 핵심 포인트를 분리하기 어렵습니다."]
        return self._render_bullets(key_lines[:3])

    def _postprocess_action_items(self, *, raw_answer: str, context_cues: dict[str, list[str]]) -> str:
        candidate_lines = self._extract_list_like_lines(raw_answer)
        grounded_lines = [
            line
            for line in candidate_lines
            if not self._looks_like_metadata(line)
            and (self._looks_like_action(line) or self._looks_like_actionable_decision(line))
        ]
        if len(grounded_lines) < 1:
            grounded_lines = self._dedupe_lines(
                context_cues["action_lines"]
                + [line for line in context_cues["decision_lines"] if self._looks_like_actionable_decision(line)]
            )

        grounded_lines = [
            self._normalize_action_line(line)
            for line in grounded_lines
            if not self._looks_like_metadata(line)
        ]
        grounded_lines = [line for line in grounded_lines if line]

        if not grounded_lines:
            return "1. 문서에 바로 실행할 일은 명확히 나오지 않습니다."
        return self._render_numbered(grounded_lines[:5])

    def _postprocess_memo(
        self,
        *,
        raw_answer: str,
        context_label: str,
        context_cues: dict[str, list[str]],
    ) -> str:
        sections = {"title": "", "summary": [], "actions": []}
        current_section: str | None = None
        for raw_line in raw_answer.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("제목:"):
                sections["title"] = line.removeprefix("제목:").strip()
                current_section = "title"
                continue
            if line.startswith("핵심:"):
                current_section = "summary"
                remainder = line.removeprefix("핵심:").strip()
                if remainder:
                    sections["summary"].append(remainder)
                continue
            if line.startswith("다음 행동:"):
                current_section = "actions"
                remainder = line.removeprefix("다음 행동:").strip()
                if remainder:
                    sections["actions"].append(remainder)
                continue
            if current_section == "summary":
                sections["summary"].append(line)
            elif current_section == "actions":
                sections["actions"].append(line)

        title = sections["title"] or f"{Path(context_label).name} 메모"
        summary_lines = self._dedupe_lines(
            [
                line
                for line in self._extract_list_like_lines("\n".join(sections["summary"]))
                if not self._looks_like_metadata(line)
            ]
            + context_cues["purpose_lines"]
            + context_cues["decision_lines"]
            + context_cues["high_signal_lines"]
        )[:3]
        action_lines = self._dedupe_lines(
            [
                self._normalize_action_line(line)
                for line in self._extract_list_like_lines("\n".join(sections["actions"]))
                if not self._looks_like_metadata(line)
            ]
            + [self._normalize_action_line(line) for line in context_cues["action_lines"]]
        )[:3]

        if not summary_lines:
            summary_lines = ["문서의 핵심 내용을 다시 확인해 주세요."]
        if not action_lines:
            action_lines = ["문서에 바로 실행할 일은 명확히 나오지 않습니다."]

        summary_block = "\n".join(f"- {line}" for line in summary_lines)
        action_block = "\n".join(f"- {line}" for line in action_lines)
        return "\n".join(
            [
                f"제목: {title}",
                "",
                "핵심:",
                summary_block,
                "",
                "다음 행동:",
                action_block,
            ]
        )

    def _extract_context_cues(self, context_excerpt: str) -> dict[str, list[str]]:
        heading_lines: list[str] = []
        bullet_lines: list[str] = []
        action_lines: list[str] = []
        metadata_lines: list[str] = []
        decision_lines: list[str] = []
        purpose_lines: list[str] = []
        sentence_lines: list[str] = []
        inside_action_section = False
        inside_purpose_section = False

        for raw_line in context_excerpt.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            cleaned = self._clean_line(line)
            if not cleaned:
                continue

            if self._looks_like_metadata(cleaned):
                metadata_lines.append(cleaned)
                continue

            if line.startswith("#"):
                heading_lines.append(cleaned)
                if self._looks_like_decision_line(cleaned):
                    decision_lines.append(cleaned)
                if self._looks_like_purpose_heading(cleaned):
                    purpose_lines.append(cleaned)
                inside_action_section = self._looks_like_action_heading(cleaned)
                inside_purpose_section = self._looks_like_purpose_heading(cleaned)
                continue

            if line.startswith(("-", "*")) or re.match(r"^\d+\.", line):
                bullet_lines.append(cleaned)
                if inside_action_section or self._looks_like_action(cleaned):
                    action_lines.append(cleaned)
                if inside_purpose_section or self._looks_like_key_point_line(cleaned):
                    purpose_lines.append(cleaned)
                if self._looks_like_decision_line(cleaned):
                    decision_lines.append(cleaned)
                continue

            if inside_action_section or self._looks_like_action(cleaned):
                action_lines.append(cleaned)
            if inside_purpose_section or self._looks_like_key_point_line(cleaned):
                purpose_lines.append(cleaned)
            if self._looks_like_decision_line(cleaned):
                decision_lines.append(cleaned)
            if len(cleaned) >= 24:
                sentence_lines.append(cleaned)

        high_signal_lines = self._dedupe_lines(heading_lines + purpose_lines + decision_lines + bullet_lines)
        if not high_signal_lines:
            sentence_candidates = sentence_lines or self._split_sentences(context_excerpt)
            high_signal_lines = self._dedupe_lines(sentence_candidates)

        return {
            "high_signal_lines": high_signal_lines[:8],
            "action_lines": self._dedupe_lines(action_lines)[:6],
            "decision_lines": self._dedupe_lines(decision_lines)[:6],
            "purpose_lines": self._dedupe_lines(purpose_lines)[:6],
            "metadata_lines": self._dedupe_lines(metadata_lines)[:6],
        }

    def _intent_focus_lines(self, intent: str, context_cues: dict[str, list[str]]) -> list[str]:
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return self._dedupe_lines(
                context_cues["purpose_lines"] + context_cues["decision_lines"] + context_cues["high_signal_lines"]
            )[:6]
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return self._dedupe_lines(
                context_cues["action_lines"] + context_cues["decision_lines"] + context_cues["high_signal_lines"]
            )[:6]
        if intent == FOLLOW_UP_INTENT_MEMO:
            return self._dedupe_lines(
                context_cues["purpose_lines"]
                + context_cues["decision_lines"]
                + context_cues["action_lines"]
                + context_cues["high_signal_lines"]
            )[:6]
        return self._dedupe_lines(context_cues["high_signal_lines"] + context_cues["action_lines"])[:6]

    def _intent_focus_instruction(self, intent: str) -> str:
        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            return "Prefer the document's purpose, principles, constraints, decisions, and conclusions over metadata or boilerplate."
        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            return "Prefer grounded next steps, recommendation bullets, decision-needed statements, and explicit TODO-like lines."
        if intent == FOLLOW_UP_INTENT_MEMO:
            return "Prefer the most decision-relevant facts first, then include only grounded next actions."
        return "Prefer the strongest grounded lines from the selected document context."

    def _prompt_list_block(self, title: str, lines: list[str], empty_message: str) -> list[str]:
        block = [title]
        if lines:
            block.extend(f"- {line}" for line in lines)
        else:
            block.append(f"- {empty_message}")
        return block

    def _format_evidence_items(self, evidence_items: list[dict[str, str]] | None) -> list[str]:
        if not evidence_items:
            return []
        formatted: list[str] = []
        for index, item in enumerate(evidence_items[:5], start=1):
            source_name = str(item.get("source_name") or item.get("source_path") or "(출처 없음)").strip()
            label = str(item.get("label") or "근거").strip()
            snippet = self._clean_line(str(item.get("snippet") or ""))
            if not snippet:
                continue
            formatted.append(f"[{index}] {source_name} | {label} | {snippet}")
        return formatted

    def _looks_like_metadata(self, line: str) -> bool:
        lowered = line.lower()
        metadata_keywords = [
            "영문 제목",
            "버전",
            "작성일",
            "source path",
            "source:",
            "match:",
            "snippet:",
            "원본 파일",
            "원본 경로",
            "file:",
            "path:",
            "version:",
            "date:",
        ]
        if any(keyword in lowered for keyword in metadata_keywords):
            return True
        if re.fullmatch(r"v?\d+(?:\.\d+)+", line):
            return True
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", line):
            return True
        return False

    def _looks_like_action(self, line: str) -> bool:
        action_keywords = [
            "해야",
            "필요",
            "권고",
            "다음",
            "검토",
            "확정",
            "결정",
            "도입",
            "추가",
            "정리",
            "구현",
            "확인",
            "연결",
            "update",
            "add",
            "fix",
            "review",
            "define",
        ]
        return any(keyword in line for keyword in action_keywords)

    def _looks_like_action_heading(self, line: str) -> bool:
        heading_keywords = ["실행", "권고", "다음", "후속", "할 일", "액션", "todo", "즉시"]
        lowered = line.lower()
        return any(keyword in lowered for keyword in heading_keywords)

    def _looks_like_purpose_heading(self, line: str) -> bool:
        heading_keywords = [
            "목적",
            "범위",
            "핵심",
            "원칙",
            "기준",
            "요약",
            "결론",
            "로드맵",
            "목표",
            "전략",
        ]
        return any(keyword in line for keyword in heading_keywords)

    def _looks_like_key_point_line(self, line: str) -> bool:
        key_point_keywords = [
            "목표",
            "원칙",
            "기준",
            "가정",
            "결론",
            "핵심",
            "우선",
            "전제",
            "범위",
            "보완",
            "리스크",
            "방향",
        ]
        return any(keyword in line for keyword in key_point_keywords)

    def _looks_like_decision_line(self, line: str) -> bool:
        decision_keywords = [
            "결정",
            "확정",
            "우선",
            "전제",
            "기준",
            "원칙",
            "금지",
            "허용",
            "제한",
            "필수",
            "must",
            "should",
        ]
        lowered = line.lower()
        return any(keyword in lowered for keyword in decision_keywords)

    def _looks_like_actionable_decision(self, line: str) -> bool:
        actionable_decision_keywords = [
            "결정",
            "확정",
            "검토",
            "도입",
            "추가",
            "유지",
            "정리",
            "구현",
            "연결",
            "필요",
            "권고",
            "다음",
            "우선",
            "금지",
            "허용",
            "필수",
        ]
        lowered = line.lower()
        return any(keyword in lowered for keyword in actionable_decision_keywords)

    def _split_sentences(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
        return [cleaned for cleaned in (self._clean_line(part) for part in parts) if cleaned]

    def _extract_list_like_lines(self, text: str) -> list[str]:
        lines: list[str] = []
        for raw_line in text.splitlines():
            cleaned = self._clean_line(raw_line)
            if cleaned:
                lines.append(cleaned)
        if lines:
            return lines
        return self._split_sentences(text)

    def _render_bullets(self, lines: list[str]) -> str:
        return "\n".join(f"- {line}" for line in lines)

    def _render_numbered(self, lines: list[str]) -> str:
        return "\n".join(f"{index}. {line}" for index, line in enumerate(lines, start=1))

    def _normalize_action_line(self, line: str) -> str:
        cleaned = self._clean_line(line)
        if cleaned.endswith("."):
            cleaned = cleaned[:-1].strip()
        return cleaned

    def _clean_line(self, line: str) -> str:
        cleaned = re.sub(r"^[#>\-\*\d\.\)\s]+", "", line.strip())
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip(" |")[:180].strip()

    def _dedupe_lines(self, lines: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for line in lines:
            normalized = line.strip()
            if len(normalized) < 6:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(normalized)
        return deduped

    def list_models(self) -> list[str]:
        payload = self._request_json("GET", "/api/tags")
        models = payload.get("models", [])
        if not isinstance(models, list):
            raise ModelAdapterError("Unexpected Ollama response: 'models' is not a list.")
        names: list[str] = []
        for item in models:
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                names.append(item["name"])
        return names

    def health_check(self) -> ModelRuntimeStatus:
        version_payload = self._request_json("GET", "/api/version")
        version = version_payload.get("version")
        if not isinstance(version, str) or not version.strip():
            raise ModelAdapterError("Ollama version endpoint returned an unexpected response.")

        available_models = self.list_models()
        model_available = self.model in available_models
        if model_available:
            detail = f"Ollama is reachable and model '{self.model}' is installed."
        elif available_models:
            joined = ", ".join(available_models)
            detail = (
                f"Ollama is reachable, but model '{self.model}' is not installed. "
                f"Available local models: {joined}. Run `ollama pull {self.model}` and retry."
            )
        else:
            detail = (
                f"Ollama is reachable, but no local models are installed. "
                f"Run `ollama pull {self.model}` and retry."
            )

        return ModelRuntimeStatus(
            provider="ollama",
            configured_model=self.model,
            reachable=True,
            configured_model_available=model_available,
            detail=detail,
            base_url=self.base_url,
            version=version,
            available_models=available_models,
        )

    def _generate(
        self,
        *,
        prompt: str,
        system: str,
        enforce_korean: bool = False,
        korean_rewrite_instruction: str | None = None,
    ) -> str:
        return self._consume_stream_events(
            self._stream_generate(
                prompt=prompt,
                system=system,
                enforce_korean=enforce_korean,
                korean_rewrite_instruction=korean_rewrite_instruction,
            )
        )

    def _consume_stream_events(self, events) -> str:
        text = ""
        for event in events:
            text = self._apply_stream_event(text, event)
        return text.strip()

    def _apply_stream_event(self, current: str, event: ModelStreamEvent) -> str:
        if event.kind == "text_replace":
            return event.text
        return current + event.text

    def _stream_generate(
        self,
        *,
        prompt: str,
        system: str,
        enforce_korean: bool = False,
        korean_rewrite_instruction: str | None = None,
    ):
        combined = ""
        buffered_chunks: list[str] = []
        emitted_raw = False
        for chunk in self._iter_generate_raw(prompt=prompt, system=system):
            combined += chunk
            if not enforce_korean:
                yield ModelStreamEvent(kind="text_delta", text=chunk)
                continue

            if emitted_raw:
                yield ModelStreamEvent(kind="text_delta", text=chunk)
                continue

            buffered_chunks.append(chunk)
            buffered_text = "".join(buffered_chunks)
            if self._needs_korean_rewrite(buffered_text):
                continue
            if self._should_release_korean_stream(buffered_text):
                for buffered in buffered_chunks:
                    yield ModelStreamEvent(kind="text_delta", text=buffered)
                buffered_chunks = []
                emitted_raw = True

        combined = combined.strip()
        if not combined:
            raise ModelAdapterError("Ollama returned an empty response.")

        if enforce_korean and self._needs_korean_rewrite(combined):
            rewritten = self._rewrite_in_korean(
                text=combined,
                instruction=korean_rewrite_instruction or "Return concise Korean text only.",
            )
            if rewritten.strip() != combined:
                if emitted_raw:
                    yield ModelStreamEvent(kind="text_replace", text=rewritten.strip())
                else:
                    yield ModelStreamEvent(kind="text_delta", text=rewritten.strip())
                return
        elif enforce_korean and buffered_chunks:
            for buffered in buffered_chunks:
                yield ModelStreamEvent(kind="text_delta", text=buffered)

    def _generate_raw(self, *, prompt: str, system: str) -> str:
        return self._consume_stream_events(
            self._stream_generate(prompt=prompt, system=system)
        )

    def _iter_generate_raw(self, *, prompt: str, system: str):
        payload = {
            "model": self._effective_model,
            "prompt": prompt,
            "system": system,
            "stream": True,
        }
        emitted = False
        for chunk in self._iter_request_json_lines("POST", "/api/generate", payload):
            response_text = chunk.get("response")
            if isinstance(response_text, str) and response_text:
                emitted = True
                yield response_text
        if not emitted:
            raise ModelAdapterError("Ollama returned an empty response.")

    def _needs_korean_rewrite(self, text: str) -> bool:
        hangul_count = len(re.findall(r"[가-힣]", text))
        han_count = len(re.findall(r"[\u4E00-\u9FFF]", text))
        kana_count = len(re.findall(r"[\u3040-\u30FF]", text))
        # Detect broken/garbled Unicode: combining marks, replacement chars,
        # or stray diacritics that appear mixed with Korean text.
        garbled_count = len(re.findall(r"[\u0300-\u036F\uFFFD\u0318\u0358]", text))
        if kana_count >= 1 and hangul_count >= 1:
            return True
        if han_count >= 1 and hangul_count >= 4:
            return True
        if kana_count >= 2 and hangul_count < max(2, kana_count // 2):
            return True
        if han_count >= 8 and hangul_count < max(3, han_count // 4):
            return True
        # Garbled characters mixed with Korean text
        if garbled_count >= 1 and hangul_count >= 4:
            return True
        return False

    def _should_release_korean_stream(self, text: str) -> bool:
        normalized = text.strip()
        if not normalized:
            return False
        return len(normalized) >= 40 or "\n" in normalized or normalized.endswith((".", "!", "?", "다"))

    def _rewrite_in_korean(self, *, text: str, instruction: str) -> str:
        rewrite_prompt = "\n".join(
            [
                "Format contract:",
                instruction,
                "",
                "Text to rewrite:",
                text,
            ]
        )
        rewritten = self._generate_raw(
            prompt=rewrite_prompt,
            system=(
                "Rewrite the supplied text into natural Korean. "
                "Use Hangul for explanatory text. Do not use Chinese or Japanese. "
                "Keep file names, product names, model names, and paths as-is when needed. "
                "Follow the format contract exactly."
            ),
        )
        return rewritten.strip()

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data: bytes | None = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ModelAdapterError(
                f"Ollama API request failed with HTTP {exc.code}: {detail}"
            ) from exc
        except error.URLError as exc:
            raise ModelAdapterError(self._unreachable_runtime_message()) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise ModelAdapterError(self._request_timeout_message()) from exc

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ModelAdapterError("Ollama returned invalid JSON.") from exc

        if isinstance(decoded, dict) and isinstance(decoded.get("error"), str):
            raise ModelAdapterError(decoded["error"])
        if not isinstance(decoded, dict):
            raise ModelAdapterError("Ollama returned an unexpected response shape.")
        return decoded

    def _iter_request_json_lines(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ):
        url = f"{self.base_url}{path}"
        data: bytes | None = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                while True:
                    raw_line = response.readline()
                    if not raw_line:
                        break
                    decoded_line = raw_line.decode("utf-8").strip()
                    if decoded_line:
                        try:
                            decoded = json.loads(decoded_line)
                        except json.JSONDecodeError as exc:
                            raise ModelAdapterError("Ollama returned invalid JSON.") from exc
                        if isinstance(decoded, dict) and isinstance(decoded.get("error"), str):
                            raise ModelAdapterError(decoded["error"])
                        if not isinstance(decoded, dict):
                            raise ModelAdapterError("Ollama returned an unexpected response shape.")
                        yield decoded
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ModelAdapterError(
                f"Ollama API request failed with HTTP {exc.code}: {detail}"
            ) from exc
        except error.URLError as exc:
            raise ModelAdapterError(self._unreachable_runtime_message()) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise ModelAdapterError(self._request_timeout_message()) from exc

    def _unreachable_runtime_message(self) -> str:
        message = f"Unable to reach Ollama at {self.base_url}. Is the local runtime running?"
        if self._is_localhost_base_url():
            message += (
                " If this app is running inside WSL, localhost may point to the Linux environment instead of Windows. "
                "Start Ollama in the same environment or use the Windows host IP as Base URL."
            )
        return message

    def _request_timeout_message(self) -> str:
        seconds = int(self.timeout_seconds) if self.timeout_seconds.is_integer() else self.timeout_seconds
        return (
            f"Ollama request timed out after {seconds} seconds while waiting for model '{self.model}'. "
            "The local model may still be loading or generating. Retry once, or increase LOCAL_AI_OLLAMA_TIMEOUT_SECONDS."
        )

    def _is_localhost_base_url(self) -> bool:
        hostname = (urlparse(self.base_url).hostname or "").lower()
        return hostname in {"localhost", "127.0.0.1", "::1"}


class _ModelOverrideContext:
    """Temporarily override the active model on an OllamaModelAdapter."""

    def __init__(self, adapter: OllamaModelAdapter, model: str) -> None:
        self._adapter = adapter
        self._model = model
        self._previous: str | None = None

    def __enter__(self) -> OllamaModelAdapter:
        self._previous = self._adapter._active_model
        self._adapter._active_model = self._model
        return self._adapter

    def __exit__(self, *_: object) -> None:
        self._adapter._active_model = self._previous
