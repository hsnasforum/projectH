from __future__ import annotations

import re
from typing import Any


def localize_text(text: str, *, locale: str = "ko") -> str:
    if locale != "ko":
        return text

    localized = text
    replacements = [
        ("[mock-response]", "[모의 응답]"),
        ("[mock-summary]", "[모의 요약]"),
        ("Search results:", "검색 결과:"),
        ("Selected sources:", "선택된 출처:"),
        ("Search query:", "검색어:"),
        ("Source References", "출처 참고"),
        ("Match type:", "일치 유형:"),
        ("Match:", "일치 방식:"),
        ("Snippet:", "발췌:"),
        ("(no snippet)", "(발췌 없음)"),
        ("## Summary", "## 요약"),
        ("Next steps:", "다음 단계:"),
        ("Note: ", "참고: "),
        ("could not be summarized.", "요약할 수 없습니다."),
        ("Using the built-in mock adapter.", "내장 모의 어댑터를 사용 중입니다."),
        ("Unable to complete request:", "요청을 완료하지 못했습니다:"),
    ]
    for source, target in replacements:
        localized = localized.replace(source, target)

    localized = re.sub(r"^# Summary of (.+)$", r"# \1 요약", localized, flags=re.MULTILINE)
    localized = re.sub(r"^# Search Summary for '(.+)'$", r"# '\1' 검색 요약", localized, flags=re.MULTILINE)
    localized = re.sub(r"(^|\n)Source: ", r"\1원본 파일: ", localized)
    localized = re.sub(r"^Source path: ", "원본 경로: ", localized, flags=re.MULTILINE)
    localized = re.sub(
        r"^1\. Save or export a searchable PDF with a text layer, then try again\.$",
        "1. 텍스트 레이어가 있는 검색 가능한 PDF로 다시 저장하거나 내보낸 뒤 다시 시도하세요.",
        localized,
        flags=re.MULTILINE,
    )
    localized = re.sub(
        r"^2\. Run OCR in another local tool, then retry with the OCRed PDF or a text file\.$",
        "2. 다른 로컬 도구에서 OCR을 수행한 뒤, OCR 처리된 PDF나 텍스트 파일로 다시 시도하세요.",
        localized,
        flags=re.MULTILINE,
    )
    localized = re.sub(
        r"^3\. Use the original text-based source document if one is available\.$",
        "3. 원래의 텍스트 기반 원본 문서가 있다면 그 파일로 다시 시도하세요.",
        localized,
        flags=re.MULTILINE,
    )
    localized = re.sub(
        r"^Search (.+) for (.+) and summarize the results$",
        r"\1에서 '\2'를 검색하고 결과를 요약해 주세요.",
        localized,
        flags=re.MULTILINE,
    )
    localized = re.sub(r"^Summarize (.+)$", r"\1 파일을 요약해 주세요.", localized, flags=re.MULTILINE)
    localized = re.sub(r"^Hello$", "안녕하세요", localized, flags=re.MULTILINE)
    localized = re.sub(
        r"No matching files found for '(.+?)' under (.+?)\.",
        r"\2 아래에서 '\1' 검색 결과를 찾지 못했습니다.",
        localized,
    )
    localized = re.sub(
        r"Approval required to save the search summary note to (.+)\.$",
        r"검색 요약 노트를 \1에 저장하려면 승인이 필요합니다.",
        localized,
    )
    localized = re.sub(
        r"Approval required to save the summary note to (.+)\.$",
        r"요약 노트를 \1에 저장하려면 승인이 필요합니다.",
        localized,
    )
    localized = re.sub(
        r"Saved search summary note to (.+)\.$",
        r"검색 요약 노트를 \1에 저장했습니다.",
        localized,
    )
    localized = re.sub(
        r"Saved summary note to (.+)\.$",
        r"요약 노트를 \1에 저장했습니다.",
        localized,
    )
    localized = re.sub(
        r"Skipped (\d+) scanned or image-only PDF file\(s\) during search because OCR is not supported in this MVP\. Examples:",
        r"검색 중 OCR 미지원으로 스캔본 또는 이미지형 PDF \1개를 건너뛰었습니다. 예시:",
        localized,
    )
    localized = re.sub(
        r"PDF does not contain extractable text\. It may be a scanned or image-only PDF and would require OCR, which is not enabled in this MVP\.",
        "PDF 안에 추출 가능한 텍스트가 없습니다. 스캔본 또는 이미지형 PDF일 수 있으며, 이 MVP에서는 OCR을 지원하지 않습니다.",
        localized,
    )
    localized = re.sub(
        r"Ollama is reachable and model '(.+?)' is installed\.",
        r"Ollama에 연결되었고 '\1' 모델이 설치되어 있습니다.",
        localized,
    )
    localized = re.sub(
        r"Ollama is reachable, but model '(.+?)' is not installed\. Available local models: (.+?)\. Run `ollama pull (.+?)` and retry\.",
        r"Ollama에는 연결되었지만 '\1' 모델이 설치되어 있지 않습니다. 사용 가능한 로컬 모델: \2. `ollama pull \3`를 실행한 뒤 다시 시도해 주세요.",
        localized,
    )
    localized = re.sub(
        r"Ollama is reachable, but no local models are installed\. Run `ollama pull (.+?)` and retry\.",
        r"Ollama에는 연결되었지만 설치된 로컬 모델이 없습니다. `ollama pull \1`를 실행한 뒤 다시 시도해 주세요.",
        localized,
    )
    localized = re.sub(
        r"Unable to reach Ollama at (.+?)\. Is the local runtime running\? If this app is running inside WSL, localhost may point to the Linux environment instead of Windows\. Start Ollama in the same environment or use the Windows host IP as Base URL\.",
        r"Ollama에 연결할 수 없습니다: \1. 로컬 런타임이 실행 중인지 확인해 주세요. WSL에서 앱을 실행 중이라면 localhost가 Windows가 아니라 Linux 환경을 가리킬 수 있습니다. Ollama를 같은 환경에서 실행하거나 Windows 호스트 IP를 Base URL로 입력해 주세요.",
        localized,
    )
    localized = re.sub(
        r"Unable to reach Ollama at (.+?)\. Is the local runtime running\?",
        r"Ollama에 연결할 수 없습니다: \1. 로컬 런타임이 실행 중인지 확인해 주세요.",
        localized,
    )
    localized = re.sub(
        r"Ollama API request failed with HTTP (\d+): (.+)",
        r"Ollama API 요청이 HTTP \1로 실패했습니다: \2",
        localized,
    )
    localized = re.sub(
        r"Ollama request timed out after (.+?) seconds while waiting for model '(.+?)'\. The local model may still be loading or generating\. Retry once, or increase LOCAL_AI_OLLAMA_TIMEOUT_SECONDS\.",
        r"Ollama 요청이 \1초 안에 끝나지 않았습니다. 모델 '\2'가 아직 로딩 중이거나 생성에 시간이 오래 걸리고 있을 수 있습니다. 한 번 더 시도하거나 LOCAL_AI_OLLAMA_TIMEOUT_SECONDS 값을 늘려 주세요.",
        localized,
    )
    localized = re.sub(r"Ollama returned an empty response\.", "Ollama가 빈 응답을 반환했습니다.", localized)
    return localized


def localize_session(session: dict[str, Any], *, locale: str = "ko") -> dict[str, Any]:
    if locale != "ko":
        return session

    localized = dict(session)
    localized_messages: list[dict[str, Any]] = []
    for message in session.get("messages", []):
        if not isinstance(message, dict):
            continue
        localized_message = dict(message)
        if isinstance(localized_message.get("text"), str):
            localized_message["text"] = localize_text(localized_message["text"], locale=locale)
        if isinstance(localized_message.get("note_preview"), str):
            localized_message["note_preview"] = localize_text(localized_message["note_preview"], locale=locale)
        suggestions = localized_message.get("follow_up_suggestions")
        if isinstance(suggestions, list):
            localized_message["follow_up_suggestions"] = [
                localize_text(str(item), locale=locale)
                for item in suggestions
            ]
        approval = localized_message.get("approval")
        if isinstance(approval, dict):
            localized_approval = dict(approval)
            preview_markdown = localized_approval.get("preview_markdown")
            if isinstance(preview_markdown, str):
                localized_approval["preview_markdown"] = localize_text(preview_markdown, locale=locale)
            localized_message["approval"] = localized_approval
        active_context = localized_message.get("active_context")
        if isinstance(active_context, dict):
            localized_context = dict(active_context)
            summary_hint = localized_context.get("summary_hint")
            if isinstance(summary_hint, str):
                localized_context["summary_hint"] = localize_text(summary_hint, locale=locale)
            suggestions = localized_context.get("suggested_prompts")
            if isinstance(suggestions, list):
                localized_context["suggested_prompts"] = [
                    localize_text(str(item), locale=locale)
                    for item in suggestions
                ]
            localized_message["active_context"] = localized_context
        localized_messages.append(localized_message)
    localized["messages"] = localized_messages
    active_context = localized.get("active_context")
    if isinstance(active_context, dict):
        localized_context = dict(active_context)
        summary_hint = localized_context.get("summary_hint")
        if isinstance(summary_hint, str):
            localized_context["summary_hint"] = localize_text(summary_hint, locale=locale)
        suggestions = localized_context.get("suggested_prompts")
        if isinstance(suggestions, list):
            localized_context["suggested_prompts"] = [
                localize_text(str(item), locale=locale)
                for item in suggestions
            ]
        localized["active_context"] = localized_context
    return localized


def localize_runtime_status_payload(
    payload: dict[str, Any] | None,
    *,
    locale: str = "ko",
) -> dict[str, Any] | None:
    if payload is None or locale != "ko":
        return payload

    localized = dict(payload)
    detail = localized.get("detail")
    if isinstance(detail, str):
        localized["detail"] = localize_text(detail, locale=locale)
    return localized
