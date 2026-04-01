from __future__ import annotations

import os
import re
import time
from pathlib import Path

from model_adapter.base import (
    FOLLOW_UP_INTENT_ACTION_ITEMS,
    FOLLOW_UP_INTENT_GENERAL,
    FOLLOW_UP_INTENT_KEY_POINTS,
    FOLLOW_UP_INTENT_MEMO,
    ModelAdapter,
    ModelStreamEvent,
    ModelRuntimeStatus,
    SummaryNoteDraft,
)


class MockModelAdapter(ModelAdapter):
    def respond(self, prompt: str, *, active_preferences: list[dict[str, str]] | None = None) -> str:
        prefix = "[모의 응답]"
        if active_preferences:
            prefix = f"[모의 응답, 선호 {len(active_preferences)}건 반영]"
        return f"{prefix} {prompt}"

    def summarize(self, text: str) -> str:
        if "Summary mode: merged_chunk_outline" in text:
            if "Summary source type: search_results" in text:
                return "[모의 요약] " + self._summarize_search_chunk_outline(text)
            return "[모의 요약] " + self._summarize_chunk_outline(text)
        if "Summary mode: short_summary" in text:
            if "Summary source type: search_results" in text:
                return "[모의 요약] " + self._summarize_search_short_summary_prompt(text)
            return "[모의 요약] " + self._summarize_short_summary_prompt(text)
        if "Summary mode: chunk_note" in text:
            return "[모의 요약] " + self._summarize_chunk_note_prompt(text)
        trimmed = text.strip().replace("\n", " ")
        return "[모의 요약] " + trimmed[:240]

    def create_summary_note(self, *, source_path: str, text: str) -> SummaryNoteDraft:
        summary = self.summarize(text)
        file_name = Path(source_path).name
        title = f"{file_name} 요약"
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
        source_names = ", ".join(Path(path).name for path in source_paths[:3]) or "(출처 없음)"
        compact_excerpt = " ".join(context_excerpt.split())
        compact_summary = (summary_hint or compact_excerpt or "문맥 요약을 만들 수 없습니다.").strip()
        title = self._extract_title(context_excerpt, context_label)
        grounded_lines = self._extract_grounded_lines(evidence_items)
        key_points = self._extract_key_points(context_excerpt, compact_summary, context_label, grounded_lines)
        action_items = self._extract_action_items(context_excerpt, key_points, context_label, grounded_lines)

        if intent == FOLLOW_UP_INTENT_KEY_POINTS:
            bullets = key_points[:3]
            while len(bullets) < 3:
                bullets.append(f"{context_label} 문맥에서 추가 핵심을 더 확인해 주세요.")
            return "\n".join(
                [
                    "[모의 핵심 3줄]",
                    f"문서: {title}",
                    *(f"- {item}" for item in bullets[:3]),
                    f"참고 출처: {source_names}",
                ]
            )

        if intent == FOLLOW_UP_INTENT_ACTION_ITEMS:
            actions = action_items[:3]
            if not actions:
                actions = ["문서에서 명확한 실행 항목을 찾지 못했습니다. 필요하면 직접 후속 작업을 지정해 주세요."]
            return "\n".join(
                [
                    "[모의 실행 항목]",
                    f"문서: {title}",
                    *(f"{index}. {item}" for index, item in enumerate(actions, start=1)),
                ]
            )

        if intent == FOLLOW_UP_INTENT_MEMO:
            memo_points = key_points[:2]
            while len(memo_points) < 2:
                memo_points.append(f"{context_label} 관련 내용을 더 보강해 주세요.")
            memo_actions = action_items[:2] or ["저장 전 미리보기를 확인합니다."]
            return "\n".join(
                [
                    "[모의 메모 재작성]",
                    f"제목: {title} 메모",
                    "",
                    "핵심:",
                    *(f"- {item}" for item in memo_points),
                    "",
                    "다음 행동:",
                    *(f"- {item}" for item in memo_actions),
                    f"- 참고 출처: {source_names}",
                ]
            )

        return "\n".join(
            [
                "[모의 문서 응답]",
                f"현재 문맥: {title}",
                f"질문: {user_request}",
                f"참고 출처: {source_names}",
                f"핵심 요약: {key_points[0] if key_points else compact_summary[:240]}",
                (
                    f"추천 다음 행동: {action_items[0]}"
                    if action_items
                    else "추천 다음 행동: 문서에서 후속 작업 후보를 더 확인해 보세요."
                ),
            ]
        )

    def stream_respond(self, prompt: str, *, active_preferences: list[dict[str, str]] | None = None):
        yield from self._stream_text(self.respond(prompt, active_preferences=active_preferences))

    def stream_summarize(self, text: str):
        yield from self._stream_text(self.summarize(text))

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
        yield from self._stream_text(
            self.answer_with_context(
                intent=intent,
                user_request=user_request,
                context_label=context_label,
                source_paths=source_paths,
                context_excerpt=context_excerpt,
                summary_hint=summary_hint,
                evidence_items=evidence_items,
                active_preferences=active_preferences,
            )
        )

    def _stream_text(self, text: str, chunk_size: int = 28):
        delay_ms = self._stream_delay_ms()
        for index in range(0, len(text), chunk_size):
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            yield ModelStreamEvent(kind="text_delta", text=text[index : index + chunk_size])

    def _stream_delay_ms(self) -> int:
        raw_value = os.getenv("LOCAL_AI_MOCK_STREAM_DELAY_MS", "").strip()
        if not raw_value:
            return 0
        try:
            return max(0, int(raw_value))
        except ValueError:
            return 0

    def _summarize_chunk_outline(self, text: str) -> str:
        notes: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line.startswith("Chunk note "):
                continue
            _, _, content = line.partition(":")
            cleaned = self._clean_line(content)
            if cleaned.startswith("[모의 요약] "):
                cleaned = cleaned[len("[모의 요약] ") :].strip()
            if cleaned:
                notes.append(cleaned)

        if not notes:
            trimmed = text.strip().replace("\n", " ")
            return trimmed[:240]

        def _priority(note: str) -> tuple[int, int]:
            keywords = {
                "핵심": 6,
                "결정": 6,
                "결론": 5,
                "갈등": 5,
                "마지막": 4,
                "관계": 4,
                "위험": 3,
                "변화": 3,
                "승인": 3,
            }
            score = sum(weight for keyword, weight in keywords.items() if keyword in note)
            return (score, len(note))

        ordered = sorted(
            enumerate(notes),
            key=lambda item: (-_priority(item[1])[0], -_priority(item[1])[1], item[0]),
        )
        selected: list[str] = []
        seen: set[str] = set()
        for _, note in ordered:
            normalized = note.strip().lower()
            if not normalized or normalized in seen:
                continue
            selected.append(note)
            seen.add(normalized)
            if len(selected) >= 4:
                break

        if not selected:
            selected = notes[:4]
        return " ".join(selected)[:240]

    def _summarize_search_chunk_outline(self, text: str) -> str:
        notes: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line.startswith("Chunk note "):
                continue
            _, _, content = line.partition(":")
            cleaned = self._clean_line(content)
            if cleaned.startswith("[모의 요약] "):
                cleaned = cleaned[len("[모의 요약] ") :].strip()
            if cleaned:
                notes.append(cleaned)

        if not notes:
            trimmed = text.strip().replace("\n", " ")
            return trimmed[:240]

        selected: list[str] = []
        seen: set[str] = set()
        for note in notes:
            normalized = note.strip().lower()
            if not normalized or normalized in seen:
                continue
            selected.append(note.rstrip("."))
            seen.add(normalized)
            if len(selected) >= 3:
                break

        if not selected:
            return notes[0][:240]
        if len(selected) == 1:
            return selected[0][:240]
        return ("여러 검색 결과를 종합하면 " + ", ".join(selected[:-1]) + "이고, " + selected[-1] + "입니다.")[:240]

    def _summarize_short_summary_prompt(self, text: str) -> str:
        body = self._extract_summary_prompt_body(text)
        candidates: list[str] = []
        for raw_line in body.splitlines():
            line = self._clean_line(raw_line)
            if not line:
                continue
            candidates.append(line)
            if len(" ".join(candidates)) >= 240:
                break
        if candidates:
            return " ".join(candidates)[:240]
        trimmed = body.strip().replace("\n", " ")
        return trimmed[:240]

    def _summarize_search_short_summary_prompt(self, text: str) -> str:
        body = self._extract_summary_prompt_body(text)
        findings: list[str] = []
        seen: set[str] = set()
        for raw_line in body.splitlines():
            line = self._clean_line(raw_line)
            if not line or line.startswith(("Search query:", "Selected sources:", "Source path:", "Match type:", "Snippet:", "## Source:")):
                continue
            normalized = line.lower()
            if normalized in seen:
                continue
            findings.append(line.rstrip("."))
            seen.add(normalized)
            if len(findings) >= 3:
                break
        if not findings:
            trimmed = body.strip().replace("\n", " ")
            return trimmed[:240]
        if len(findings) == 1:
            return findings[0][:240]
        return ("여러 검색 결과를 종합하면 " + ", ".join(findings[:-1]) + "이고, " + findings[-1] + "입니다.")[:240]

    def _summarize_chunk_note_prompt(self, text: str) -> str:
        body = self._extract_summary_prompt_body(text)
        candidates: list[str] = []
        for raw_line in body.splitlines():
            line = self._clean_line(raw_line)
            if not line:
                continue
            if line.startswith(("## Source:", "Match type:", "Snippet:")):
                continue
            candidates.append(line)
            if len(" ".join(candidates)) >= 240:
                break
        if candidates:
            return " ".join(candidates)[:240]
        trimmed = body.strip().replace("\n", " ")
        return trimmed[:240]

    def _extract_summary_prompt_body(self, text: str) -> str:
        for marker in (
            "Document excerpt:",
            "Selected search-result excerpt:",
            "Document text:",
            "Selected search-result text:",
        ):
            _, separator, tail = text.partition(marker)
            if separator:
                return tail.strip()
        return text.strip()

    def _extract_title(self, text: str, fallback: str) -> str:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(("[", "선택된 근거 묶음", "짧은 보조 문맥", "- 보조 문맥")):
                continue
            if line.startswith("#"):
                return line.lstrip("#").strip()
            if len(line) < 80 and not line.startswith(("Source:", "Match:", "Snippet:", "출처:", "라벨:", "근거:")):
                return line
        return fallback

    def _extract_grounded_lines(self, evidence_items: list[dict[str, str]] | None) -> list[str]:
        if not evidence_items:
            return []
        return self._dedupe_lines(
            [
                self._clean_line(str(item.get("snippet") or ""))
                for item in evidence_items
                if isinstance(item, dict)
            ]
        )

    def _extract_key_points(
        self,
        text: str,
        summary_hint: str,
        context_label: str,
        grounded_lines: list[str] | None = None,
    ) -> list[str]:
        candidates: list[str] = []
        if grounded_lines:
            candidates.extend(grounded_lines)
        section_bullets = self._collect_section_bullets(text, target_keywords=["핵심", "목표", "원칙", "개정", "보완", "목적"])
        candidates.extend(section_bullets)

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("|") or line.startswith(("Source:", "Match:", "Snippet:")):
                continue
            cleaned = self._clean_line(line)
            if not cleaned:
                continue
            if line.startswith(("#", "-", "*")) or re.match(r"^\d+\.", line):
                candidates.append(cleaned)
            elif len(cleaned) >= 30:
                candidates.append(cleaned)
            if len(candidates) >= 10:
                break

        candidates.extend(self._split_sentences(summary_hint))
        deduped = self._dedupe_lines(candidates)
        if not deduped:
            return [f"{context_label} 문맥에서 핵심 내용을 더 확인해 주세요."]
        return deduped[:3]

    def _extract_action_items(
        self,
        text: str,
        key_points: list[str],
        context_label: str,
        grounded_lines: list[str] | None = None,
    ) -> list[str]:
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
            "실행",
            "지원",
        ]
        candidates: list[str] = []
        if grounded_lines:
            candidates.extend(grounded_lines)
        candidates.extend(self._collect_section_bullets(text, target_keywords=["실행", "권고", "다음", "결정", "필요"]))

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("|"):
                continue
            cleaned = self._clean_line(line)
            if not cleaned:
                continue
            if any(keyword in cleaned for keyword in action_keywords):
                candidates.append(cleaned)

        for point in key_points:
            if any(keyword in point for keyword in action_keywords):
                candidates.append(point)

        return self._dedupe_lines(candidates)[:5]

    def _collect_section_bullets(self, text: str, *, target_keywords: list[str]) -> list[str]:
        collected: list[str] = []
        current_heading = ""
        section_active = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                current_heading = self._clean_line(line)
                section_active = any(keyword in current_heading for keyword in target_keywords)
                continue
            if section_active and (line.startswith(("-", "*")) or re.match(r"^\d+\.", line)):
                cleaned = self._clean_line(line)
                if cleaned:
                    collected.append(cleaned)
        return collected

    def _split_sentences(self, text: str) -> list[str]:
        pieces: list[str] = []
        for part in re.split(r"(?<=[.!?])\s+|\n+", text):
            cleaned = self._clean_line(part)
            if cleaned:
                pieces.append(cleaned)
        return pieces

    def _clean_line(self, line: str) -> str:
        cleaned = line.strip()
        cleaned = re.sub(r"^[#>\-\*\d\.\)\s]+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = cleaned.strip(" |")
        return cleaned[:140].strip()

    def _dedupe_lines(self, lines: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for line in lines:
            normalized = line.strip()
            if len(normalized) < 8:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(normalized)
        return deduped

    def health_check(self) -> ModelRuntimeStatus:
        return ModelRuntimeStatus(
            provider="mock",
            configured_model="mock-summary",
            reachable=True,
            configured_model_available=True,
            detail="Using the built-in mock adapter.",
        )
